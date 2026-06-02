"""Invoice assessment agents."""
import uuid
from datetime import datetime
from typing import Optional
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


class ExtractionAgent:
    """Specialist agent for extracting invoice fields."""

    def extract(self, invoice_data: dict) -> ExtractedInvoice:
        """Extract fields from invoice data."""
        line_items = [
            LineItem(
                description=li.get("description", ""),
                quantity=li.get("quantity", 1),
                unit_price=li.get("unit_price", 0),
                amount=li.get("amount", 0),
            )
            for li in invoice_data.get("line_items", [])
        ]

        extracted = ExtractedInvoice(
            vendor_name=invoice_data.get("vendor_name", ""),
            vendor_tax_id=invoice_data.get("vendor_tax_id"),
            total_amount=invoice_data.get("total_amount", 0),
            currency=invoice_data.get("currency", "USD"),
            invoice_date=invoice_data.get("invoice_date", ""),
            due_date=invoice_data.get("due_date"),
            invoice_number=invoice_data.get("invoice_number", ""),
            po_number=invoice_data.get("po_number"),
            tax_amount=invoice_data.get("tax_amount", 0),
            line_items=line_items,
        )

        # Set confidence scores
        extracted.per_field_confidence = {
            "vendor_name": 0.98,
            "total_amount": 0.98,
            "currency": 0.98,
            "invoice_date": 0.95,
            "tax_amount": 0.90,
        }

        return extracted


class ValidationAgent:
    """Specialist agent for authenticity validation."""

    def __init__(self):
        self.vendor_db = MockVendorDB()
        self.duplicate_index = MockDuplicateIndex()

    def validate(self, extracted: ExtractedInvoice) -> ValidationResult:
        """Validate authenticity signals."""
        signals: list[AuthenticitySignal] = []

        # Check arithmetic consistency
        arithmetic_ok = self._check_arithmetic(extracted)
        arithmetic_discrepancies = []
        if not arithmetic_ok:
            arithmetic_discrepancies = ["Line items sum does not match total amount"]
            signals.append(
                AuthenticitySignal(
                    code="arithmetic_mismatch",
                    severity=Severity.HIGH,
                    detail="Arithmetic inconsistency detected between line items and total",
                    evidence_ref="extraction.line_items vs. total_amount",
                )
            )

        # Check vendor
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
                    detail=f"Vendor matched with {similarity:.0%} confidence to '{vendor_lookup['vendor']['name']}'",
                    evidence_ref="vendor_db.fuzzy_match",
                )
            )

        # Check duplicates
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
                    detail=f"Near-duplicate found with {dup_result['match_score']:.0%} similarity",
                    evidence_ref=dup_result["matched_invoices"][0]["hash"],
                )
            )

        return ValidationResult(
            arithmetic_consistent=arithmetic_ok,
            arithmetic_discrepancies=arithmetic_discrepancies,
            vendor_status=vendor_status,
            vendor_match_score=vendor_lookup.get("similarity_score"),
            duplicate_status=dup_status,
            duplicate_refs=[inv["hash"] for inv in dup_result.get("matched_invoices", [])],
            authenticity_signals=signals,
        )

    @staticmethod
    def _check_arithmetic(extracted: ExtractedInvoice) -> bool:
        """Verify line items sum to total."""
        if not extracted.line_items:
            return True
        line_items_total = sum(li.amount for li in extracted.line_items)
        # Allow small rounding differences
        return abs(line_items_total + extracted.tax_amount - extracted.total_amount) < 0.01


class ComplianceAgent:
    """Specialist agent for policy compliance."""

    def __init__(self):
        self.policy_engine = MockPolicyEngine()

    def check_compliance(self, extracted: ExtractedInvoice) -> ComplianceResult:
        """Check invoice against policy rules."""
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


class ScoringAgent:
    """Specialist agent for reliability scoring and explanation."""

    def score(self, evidence_bundle: EvidenceBundle) -> ReliabilityAssessment:
        """Generate reliability score and explanation."""
        extracted = evidence_bundle.extracted_invoice
        validation = evidence_bundle.validation_result
        compliance = evidence_bundle.compliance_result

        # Determine base band
        band = Band.HIGH
        score = 90
        reasons: list[TopReason] = []
        flags: list[Flag] = []

        # Adjust for validation signals
        if validation:
            for signal in validation.authenticity_signals:
                if signal.severity == Severity.CRITICAL:
                    band = Band.CRITICAL
                    score = 10
                    reasons.append(TopReason(signal.code, signal.severity, "Critical fraud signal"))
                elif signal.severity == Severity.HIGH:
                    if band in (Band.HIGH, Band.MEDIUM):
                        band = Band.LOW
                    score = min(score, 40)
                    reasons.append(TopReason(signal.code, signal.severity, "High-severity authenticity issue"))

            # Adjust for vendor match quality
            if validation.vendor_status == "fuzzy":
                score -= 15
                reasons.append(
                    TopReason("vendor_fuzzy_match", Severity.MEDIUM, "Vendor requires verification")
                )

        # Adjust for compliance violations
        if compliance:
            for violation in compliance.violations:
                if violation.severity == Severity.CRITICAL:
                    band = Band.CRITICAL
                    score = 10
                elif violation.severity == Severity.HIGH:
                    band = Band.LOW
                    score = min(score, 45)
                elif violation.severity == Severity.MEDIUM:
                    score = max(score - 20, 30)

                reasons.append(
                    TopReason(
                        violation.rule_id,
                        violation.severity,
                        f"Policy violation: {violation.description}",
                    )
                )

        # Extraction confidence
        if extracted:
            extraction_flags = extracted.extraction_flags
            if extraction_flags:
                band = Band.MEDIUM if band == Band.HIGH else band
                score = max(score - 10, 0)

        # Build explanation
        explanation = self._build_explanation(band, reasons, validation, compliance, extracted)

        # Build assessment
        assessment = ReliabilityAssessment(
            band=band,
            score=score,
            top_reasons=reasons[:3],  # Top 3 reasons
            explanation=explanation,
            human_review_required=True,
        )

        # Add fields summary
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
    def _build_explanation(band: Band, reasons: list[TopReason], validation, compliance, extracted) -> str:
        """Build human-readable explanation."""
        lines = [f"Invoice reliability assessment: **{band.value}** ({score_from_band(band)}/100)"]
        lines.append("")

        if reasons:
            lines.append("**Key factors:**")
            for reason in reasons[:3]:
                lines.append(f"  • {reason.contribution} ({reason.signal_code})")
            lines.append("")

        if validation and validation.vendor_status == "not_found":
            lines.append("⚠️  **Vendor not found in registry** — recommend verifying vendor before approval.")
        elif validation and validation.vendor_status == "fuzzy":
            lines.append(
                "⚠️  **Vendor name requires verification** — matches on record with fuzzy match."
            )

        if validation and validation.duplicate_status != "none":
            lines.append(f"🚩 **Duplicate detected** — possible resubmission (status: {validation.duplicate_status}).")

        if compliance and compliance.compliance_status == "violations_found":
            lines.append("📋 **Policy violations detected:**")
            for v in compliance.violations:
                lines.append(f"  • {v.description} (Rule {v.rule_id})")

        lines.append("")
        lines.append("**Recommendation:** Human approval required. This is an advisory assessment only.")

        return "\n".join(lines)


def score_from_band(band: Band) -> int:
    """Map band to numeric score."""
    return {"High": 85, "Medium": 60, "Low": 35, "Critical": 10}.get(band.value, 50)


class Orchestrator:
    """Supervisor agent coordinating the assessment pipeline."""

    def __init__(self):
        self.extraction_agent = ExtractionAgent()
        self.validation_agent = ValidationAgent()
        self.compliance_agent = ComplianceAgent()
        self.scoring_agent = ScoringAgent()

    def assess_invoice(self, invoice_data: dict) -> EvidenceBundle:
        """Run the complete invoice assessment pipeline."""
        import hashlib

        # Create assessment
        invoice_json = str(invoice_data)
        invoice_hash = hashlib.sha256(invoice_json.encode()).hexdigest()[:16]
        assessment_id = str(uuid.uuid4())

        bundle = EvidenceBundle(assessment_id=assessment_id, invoice_hash=invoice_hash)

        # Stage 1: Extraction
        try:
            extracted = self.extraction_agent.extract(invoice_data)
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

        # Stage 2: Validation (parallel in real system, sequential here)
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

        # Stage 3: Compliance (parallel in real system, sequential here)
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

        # Stage 4: Scoring
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
