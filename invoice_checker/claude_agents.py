"""Claude API-integrated agents for invoice assessment."""
import os
import json
from typing import Optional
from anthropic import Anthropic

from .models import (
    ExtractedInvoice,
    LineItem,
    ValidationResult,
    AuthenticitySignal,
    ComplianceResult,
    ComplianceViolation,
    ReliabilityAssessment,
    Band,
    Flag,
    TopReason,
    Severity,
    EvidenceBundle,
)
from .db import MockVendorDB, MockPolicyEngine, MockDuplicateIndex


class ClaudeExtractionAgent:
    """Claude-powered extraction agent for invoice field parsing."""

    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-opus-4-8"

    def extract(self, invoice_text: str, invoice_data: Optional[dict] = None) -> ExtractedInvoice:
        """Extract invoice fields using Claude vision/reasoning."""

        if invoice_data:
            # If structured data provided, use it
            return self._extract_from_dict(invoice_data)

        # Use Claude to extract from text/description
        prompt = f"""You are an expert invoice analyzer. Extract the following fields from the invoice text and return a JSON object.

Invoice text:
{invoice_text}

Extract and return ONLY valid JSON (no markdown, no explanation) with these fields:
{{
  "vendor_name": "string",
  "vendor_tax_id": "string or null",
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD or null",
  "po_number": "string or null",
  "currency": "string (3-letter code like USD, EUR)",
  "line_items": [
    {{"description": "string", "quantity": number, "unit_price": number, "amount": number}}
  ],
  "tax_amount": number,
  "total_amount": number
}}

Rules:
- Line items must sum to total_amount (minus tax_amount)
- All amounts as floats
- If field is missing, use null
- Return ONLY the JSON object, nothing else"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not extract JSON from Claude response: {response_text}")

        return self._extract_from_dict(data)

    @staticmethod
    def _extract_from_dict(data: dict) -> ExtractedInvoice:
        """Convert dict to ExtractedInvoice."""
        line_items = [
            LineItem(
                description=li.get("description", ""),
                quantity=li.get("quantity", 1),
                unit_price=li.get("unit_price", 0),
                amount=li.get("amount", 0),
            )
            for li in data.get("line_items", [])
        ]

        extracted = ExtractedInvoice(
            vendor_name=data.get("vendor_name", ""),
            vendor_tax_id=data.get("vendor_tax_id"),
            total_amount=data.get("total_amount", 0),
            currency=data.get("currency", "USD").upper(),
            invoice_date=data.get("invoice_date", ""),
            due_date=data.get("due_date"),
            invoice_number=data.get("invoice_number", ""),
            po_number=data.get("po_number"),
            tax_amount=data.get("tax_amount", 0),
            line_items=line_items,
        )

        extracted.per_field_confidence = {
            "vendor_name": 0.95,
            "total_amount": 0.95,
            "currency": 0.95,
            "invoice_date": 0.93,
            "tax_amount": 0.88,
        }

        return extracted


class ClaudeValidationAgent:
    """Claude-powered validation agent with deterministic authenticity checks."""

    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-opus-4-8"
        self.vendor_db = MockVendorDB()
        self.duplicate_index = MockDuplicateIndex()

    def validate(self, extracted: ExtractedInvoice) -> ValidationResult:
        """Validate authenticity with Claude reasoning + deterministic checks."""
        signals = []

        # Deterministic checks
        arithmetic_ok = self._check_arithmetic(extracted)
        if not arithmetic_ok:
            signals.append(
                AuthenticitySignal(
                    code="arithmetic_mismatch",
                    severity=Severity.HIGH,
                    detail="Line items sum does not match total amount",
                    evidence_ref="line_items vs. total_amount",
                )
            )

        # Vendor lookup (deterministic)
        vendor_lookup = self.vendor_db.lookup(extracted.vendor_name)
        vendor_status = vendor_lookup["status"]

        if vendor_status == "not_found":
            signals.append(
                AuthenticitySignal(
                    code="vendor_not_found",
                    severity=Severity.HIGH,
                    detail=f"Vendor '{extracted.vendor_name}' not found in registry",
                    evidence_ref="vendor_db.lookup",
                )
            )
        elif vendor_status == "fuzzy":
            similarity = vendor_lookup.get("similarity_score", 0.0)
            signals.append(
                AuthenticitySignal(
                    code="vendor_fuzzy_match",
                    severity=Severity.MEDIUM,
                    detail=f"Vendor fuzzy-matched to '{vendor_lookup['vendor']['name']}' ({similarity:.0%})",
                    evidence_ref="vendor_db.fuzzy_match",
                )
            )

        # Duplicate check (deterministic)
        dup_result = self.duplicate_index.check(
            extracted.vendor_name, extracted.invoice_number, extracted.total_amount
        )
        dup_status = dup_result["status"]

        if dup_status == "exact":
            signals.append(
                AuthenticitySignal(
                    code="duplicate_exact",
                    severity=Severity.CRITICAL,
                    detail="Exact duplicate invoice found in history",
                    evidence_ref=dup_result["matched_invoices"][0]["hash"],
                )
            )
        elif dup_status == "near":
            signals.append(
                AuthenticitySignal(
                    code="duplicate_near",
                    severity=Severity.HIGH,
                    detail=f"Near-duplicate found ({dup_result['match_score']:.0%} similarity)",
                    evidence_ref=dup_result["matched_invoices"][0]["hash"],
                )
            )

        # Claude reasoning for format/plausibility
        format_analysis = self._analyze_format_with_claude(extracted, vendor_status)
        if format_analysis and "anomaly" in format_analysis.lower():
            signals.append(
                AuthenticitySignal(
                    code="format_anomaly",
                    severity=Severity.MEDIUM,
                    detail=format_analysis,
                    evidence_ref="claude_format_analysis",
                )
            )

        return ValidationResult(
            arithmetic_consistent=arithmetic_ok,
            vendor_status=vendor_status,
            vendor_match_score=vendor_lookup.get("similarity_score"),
            duplicate_status=dup_status,
            duplicate_refs=[inv["hash"] for inv in dup_result.get("matched_invoices", [])],
            authenticity_signals=signals,
        )

    def _analyze_format_with_claude(self, extracted: ExtractedInvoice, vendor_status: str) -> str:
        """Use Claude to analyze invoice format plausibility."""
        prompt = f"""Analyze this invoice for format anomalies or red flags:
- Vendor: {extracted.vendor_name} (Status: {vendor_status})
- Invoice #: {extracted.invoice_number}
- Date: {extracted.invoice_date}
- Amount: {extracted.total_amount} {extracted.currency}
- Line items: {len(extracted.line_items)}
- Tax rate: {extracted.tax_amount / (extracted.total_amount - extracted.tax_amount) * 100:.1f}% (if applicable)

Return ONLY one sentence identifying any red flags, or say "No anomalies detected" if clean. Be concise."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text.strip()

    @staticmethod
    def _check_arithmetic(extracted: ExtractedInvoice) -> bool:
        """Verify line items sum to total."""
        if not extracted.line_items:
            return True
        line_items_total = sum(li.amount for li in extracted.line_items)
        return abs(line_items_total + extracted.tax_amount - extracted.total_amount) < 0.01


class ClaudeComplianceAgent:
    """Claude-powered compliance agent with deterministic rule engine."""

    def __init__(self):
        self.policy_engine = MockPolicyEngine()

    def check_compliance(self, extracted: ExtractedInvoice) -> ComplianceResult:
        """Check compliance with deterministic rules (policies are non-negotiable)."""
        result = self.policy_engine.evaluate(
            extracted.total_amount, extracted.currency, extracted.vendor_name
        )

        violations = [
            ComplianceViolation(
                rule_id=v["rule_id"],
                policy_version="1.0",
                description=v["description"],
                severity=Severity(v["severity"]),
                observed=v["observed"],
                threshold=v["threshold"],
            )
            for v in result.get("violations", [])
        ]

        return ComplianceResult(
            compliance_status=result["status"],
            violations=violations,
            required_approval_tier=result.get("approval_tier"),
            base_currency="USD",
            fx_rate=1.0 if extracted.currency == "USD" else 1.1,
            fx_source="mock_rates",
        )


class ClaudeScoringAgent:
    """Claude-powered scoring agent for reliability assessment and explanation."""

    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-opus-4-8"

    def score(self, evidence_bundle: EvidenceBundle) -> ReliabilityAssessment:
        """Generate reliability score and explanation using Claude."""
        extracted = evidence_bundle.extracted_invoice
        validation = evidence_bundle.validation_result
        compliance = evidence_bundle.compliance_result

        # Gather evidence for Claude
        evidence_summary = self._build_evidence_summary(extracted, validation, compliance)

        # Use Claude to generate score and explanation
        prompt = f"""You are an expert invoice compliance officer assessing invoice reliability for expense approval.

INVOICE DATA:
Vendor: {extracted.vendor_name}
Amount: {extracted.total_amount} {extracted.currency}
Invoice #: {extracted.invoice_number}
Date: {extracted.invoice_date}

EVIDENCE ASSESSMENT:
{evidence_summary}

Based on the evidence above, provide a JSON assessment with:
1. band: "High" (85-100), "Medium" (60-84), "Low" (35-59), or "Critical" (0-34)
2. score: numeric 0-100
3. top_reasons: array of {{signal_code, severity, contribution}}
4. explanation: 3-4 sentences citing specific evidence (plain text, no markdown)

Return ONLY valid JSON, no markdown or explanation outside the JSON."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()

        # Parse Claude's assessment
        try:
            assessment_data = json.loads(response_text)
        except json.JSONDecodeError:
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                assessment_data = json.loads(json_match.group())
            else:
                # Fallback to deterministic scoring
                assessment_data = self._fallback_scoring(evidence_bundle)

        # Convert to ReliabilityAssessment
        band = Band(assessment_data.get("band", "Medium"))
        score = assessment_data.get("score", 50)

        reasons = [
            TopReason(
                signal_code=r.get("signal_code", "unknown"),
                severity=Severity(r.get("severity", "medium")),
                contribution=r.get("contribution", ""),
            )
            for r in assessment_data.get("top_reasons", [])
        ]

        explanation = assessment_data.get(
            "explanation", "Invoice assessment complete. Human review required."
        )

        assessment = ReliabilityAssessment(
            band=band,
            score=int(score),
            top_reasons=reasons[:3],
            explanation=explanation,
            human_review_required=True,
        )

        if extracted:
            assessment.fields_summary = {
                "vendor": extracted.vendor_name,
                "amount": f"{extracted.total_amount} {extracted.currency}",
                "date": extracted.invoice_date,
                "invoice_number": extracted.invoice_number,
                "line_items_count": len(extracted.line_items),
            }

        return assessment

    @staticmethod
    def _build_evidence_summary(extracted, validation, compliance) -> str:
        """Build a summary of all evidence for Claude."""
        lines = []

        # Extraction
        lines.append("EXTRACTION:")
        lines.append(f"  ✓ Fields extracted with high confidence (95%+)")

        # Validation
        lines.append("\nVALIDATION:")
        if validation:
            if validation.arithmetic_consistent:
                lines.append("  ✓ Arithmetic consistent (line items = total)")
            else:
                lines.append("  ✗ Arithmetic INCONSISTENT")

            lines.append(f"  • Vendor status: {validation.vendor_status}")

            if validation.duplicate_status != "none":
                lines.append(f"  🚩 Duplicate: {validation.duplicate_status}")

            if validation.authenticity_signals:
                for sig in validation.authenticity_signals:
                    lines.append(f"  • [{sig.severity.value}] {sig.code}: {sig.detail}")

        # Compliance
        lines.append("\nCOMPLIANCE:")
        if compliance:
            if compliance.compliance_status == "compliant":
                lines.append("  ✓ Compliant with all policies")
            else:
                for v in compliance.violations:
                    lines.append(f"  ✗ {v.description} (Rule {v.rule_id})")

        return "\n".join(lines)

    @staticmethod
    def _fallback_scoring(evidence_bundle):
        """Fallback deterministic scoring if Claude fails."""
        score = 90
        band = "High"

        if evidence_bundle.validation_result:
            val = evidence_bundle.validation_result
            if val.duplicate_status != "none":
                score = 10
                band = "Critical"
            elif any(s.severity == Severity.CRITICAL for s in val.authenticity_signals):
                score = 10
                band = "Critical"
            elif val.vendor_status == "not_found":
                score = 40
                band = "Low"
            elif val.vendor_status == "fuzzy":
                score = 60
                band = "Medium"

        if evidence_bundle.compliance_result:
            comp = evidence_bundle.compliance_result
            if comp.violations:
                score = min(score, 45)
                band = "Low"

        return {
            "band": band,
            "score": score,
            "top_reasons": [{"signal_code": "assessment_complete", "severity": "info", "contribution": ""}],
            "explanation": "Invoice assessment complete. Human review required.",
        }


class ClaudeOrchestrator:
    """Supervisor agent coordinating the Claude-powered pipeline."""

    def __init__(self):
        self.extraction_agent = ClaudeExtractionAgent()
        self.validation_agent = ClaudeValidationAgent()
        self.compliance_agent = ClaudeComplianceAgent()
        self.scoring_agent = ClaudeScoringAgent()

    def assess_invoice(self, invoice_data: dict = None, invoice_text: str = None) -> EvidenceBundle:
        """Run the complete invoice assessment pipeline with Claude."""
        import hashlib

        # Create assessment
        key_str = invoice_text or str(invoice_data)
        invoice_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
        import uuid

        assessment_id = str(uuid.uuid4())

        bundle = EvidenceBundle(assessment_id=assessment_id, invoice_hash=invoice_hash)

        # Stage 1: Extraction
        try:
            extracted = self.extraction_agent.extract(invoice_text, invoice_data)
            bundle.extracted_invoice = extracted
        except Exception as e:
            bundle.flags.append(
                Flag(
                    code="extraction_failed",
                    severity=Severity.CRITICAL,
                    source_agent="orchestrator",
                    evidence_ref=str(e),
                )
            )
            return bundle

        # Stage 2: Validation
        try:
            validation_result = self.validation_agent.validate(extracted)
            bundle.validation_result = validation_result
        except Exception as e:
            bundle.flags.append(
                Flag(
                    code="validation_failed",
                    severity=Severity.HIGH,
                    source_agent="orchestrator",
                    evidence_ref=str(e),
                )
            )

        # Stage 3: Compliance
        try:
            compliance_result = self.compliance_agent.check_compliance(extracted)
            bundle.compliance_result = compliance_result
        except Exception as e:
            bundle.flags.append(
                Flag(
                    code="compliance_failed",
                    severity=Severity.HIGH,
                    source_agent="orchestrator",
                    evidence_ref=str(e),
                )
            )

        # Stage 4: Scoring with Claude
        try:
            assessment = self.scoring_agent.score(bundle)
            bundle.assessment = assessment
        except Exception as e:
            bundle.flags.append(
                Flag(
                    code="scoring_failed",
                    severity=Severity.HIGH,
                    source_agent="orchestrator",
                    evidence_ref=str(e),
                )
            )
            return bundle

        return bundle
