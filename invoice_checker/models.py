"""Data models for the invoice assessment pipeline."""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
import json


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Band(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    CRITICAL = "Critical"


@dataclass
class LineItem:
    description: str
    quantity: float
    unit_price: float
    amount: float

    def to_dict(self):
        return asdict(self)


@dataclass
class ExtractedInvoice:
    """Extracted invoice fields."""
    vendor_name: str
    vendor_tax_id: Optional[str]
    total_amount: float
    currency: str
    invoice_date: str
    due_date: Optional[str]
    invoice_number: str
    po_number: Optional[str]
    tax_amount: float
    line_items: List[LineItem]

    # Extraction metadata
    per_field_confidence: Dict[str, float] = field(default_factory=dict)
    extraction_flags: List[str] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["line_items"] = [li.to_dict() for li in self.line_items]
        return d


@dataclass
class AuthenticitySignal:
    code: str
    severity: Severity
    detail: str
    evidence_ref: str = ""


@dataclass
class ValidationResult:
    """Authenticity validation signals."""
    arithmetic_consistent: bool
    vendor_status: str  # matched|fuzzy|not_found
    duplicate_status: str  # none|exact|near
    arithmetic_discrepancies: List[str] = field(default_factory=list)
    vendor_match_score: Optional[float] = None
    duplicate_refs: List[str] = field(default_factory=list)
    format_consistent: bool = True
    format_anomalies: List[str] = field(default_factory=list)
    authenticity_signals: List[AuthenticitySignal] = field(default_factory=list)

    def to_dict(self):
        return {
            "arithmetic_consistent": self.arithmetic_consistent,
            "arithmetic_discrepancies": self.arithmetic_discrepancies,
            "vendor_status": self.vendor_status,
            "vendor_match_score": self.vendor_match_score,
            "duplicate_status": self.duplicate_status,
            "duplicate_refs": self.duplicate_refs,
            "format_consistent": self.format_consistent,
            "format_anomalies": self.format_anomalies,
            "authenticity_signals": [{"code": s.code, "severity": s.severity.value, "detail": s.detail}
                                    for s in self.authenticity_signals],
        }


@dataclass
class ComplianceViolation:
    rule_id: str
    policy_version: str
    description: str
    severity: Severity
    observed: str
    threshold: str


@dataclass
class ComplianceResult:
    """Policy compliance check results."""
    compliance_status: str  # compliant|violations_found|indeterminate
    violations: List[ComplianceViolation] = field(default_factory=list)
    required_approval_tier: Optional[str] = None
    base_currency: str = "USD"
    fx_rate: float = 1.0
    fx_source: str = "mock"

    def to_dict(self):
        return {
            "compliance_status": self.compliance_status,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "policy_version": v.policy_version,
                    "description": v.description,
                    "severity": v.severity.value,
                    "observed": v.observed,
                    "threshold": v.threshold,
                }
                for v in self.violations
            ],
            "required_approval_tier": self.required_approval_tier,
            "normalization": {
                "base_currency": self.base_currency,
                "fx_rate": self.fx_rate,
                "fx_source": self.fx_source,
            },
        }


@dataclass
class Flag:
    code: str
    severity: Severity
    source_agent: str
    evidence_ref: str
    human_action_hint: Optional[str] = None

    def to_dict(self):
        return {
            "code": self.code,
            "severity": self.severity.value,
            "source_agent": self.source_agent,
            "evidence_ref": self.evidence_ref,
            "human_action_hint": self.human_action_hint,
        }


@dataclass
class TopReason:
    signal_code: str
    severity: Severity
    contribution: str

    def to_dict(self):
        return {
            "signal_code": self.signal_code,
            "severity": self.severity.value,
            "contribution": self.contribution,
        }


@dataclass
class ReliabilityAssessment:
    """Final advisory assessment (the output of Scoring agent)."""
    band: Band
    score: int  # 0-100
    rubric_version: str = "1.0"
    top_reasons: List[TopReason] = field(default_factory=list)
    flags: List[Flag] = field(default_factory=list)
    explanation: str = ""
    fields_summary: Dict[str, Any] = field(default_factory=dict)
    recommendation_type: str = "advisory_only"
    human_review_required: bool = True

    def to_dict(self):
        return {
            "reliability": {
                "band": self.band.value,
                "score": self.score,
                "rubric_version": self.rubric_version,
            },
            "top_reasons": [r.to_dict() for r in self.top_reasons],
            "flags": [f.to_dict() for f in self.flags],
            "explanation": self.explanation,
            "fields_summary": self.fields_summary,
            "recommendation_type": self.recommendation_type,
            "human_review_required": self.human_review_required,
        }


@dataclass
class EvidenceBundle:
    """Shared state across the pipeline."""
    assessment_id: str
    invoice_hash: str
    extracted_invoice: Optional[ExtractedInvoice] = None
    validation_result: Optional[ValidationResult] = None
    compliance_result: Optional[ComplianceResult] = None
    assessment: Optional[ReliabilityAssessment] = None
    flags: List[Flag] = field(default_factory=list)

    def to_dict(self):
        return {
            "assessment_id": self.assessment_id,
            "invoice_hash": self.invoice_hash,
            "extracted_invoice": self.extracted_invoice.to_dict() if self.extracted_invoice else None,
            "validation_result": self.validation_result.to_dict() if self.validation_result else None,
            "compliance_result": self.compliance_result.to_dict() if self.compliance_result else None,
            "assessment": self.assessment.to_dict() if self.assessment else None,
            "flags": [f.to_dict() for f in self.flags],
        }
