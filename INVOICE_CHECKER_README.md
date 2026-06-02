# Invoice Reliability Assessment Agent (IRAA)

A multi-agent system that evaluates invoice reliability for expense approval. Built from the Agent Factory Orchestrator design patterns, this CLI tool accepts invoices and returns a detailed reliability assessment with explanations.

## Features

- **Multi-modal assessment**: Extraction, validation, compliance checking, and scoring
- **Fraud detection**: Duplicate detection, vendor registry matching, arithmetic validation
- **Policy compliance**: Automatic policy rule evaluation with violation reporting
- **Explainability**: Human-readable assessment with cited evidence and rationale
- **No auto-approval**: Advisory-only output — humans always make the final decision
- **Structured output**: JSON export of full assessment evidence for audit trails

## Quick Start

### List sample invoices
```bash
python check_invoice.py --list-samples
```

### Check a sample invoice
```bash
# Clean, compliant invoice (happy path)
python check_invoice.py clean

# Duplicate fraud detection
python check_invoice.py duplicate

# Unknown vendor risk
python check_invoice.py unknown_vendor

# Policy threshold violation
python check_invoice.py over_threshold

# Arithmetic inconsistency
python check_invoice.py bad_arithmetic

# Multi-currency handling
python check_invoice.py foreign_currency
```

### Check a custom invoice
```bash
python check_invoice.py path/to/invoice.json
```

### Save assessment to JSON
```bash
python check_invoice.py clean --output assessment.json
```

## Sample Invoice Formats

All invoices accept JSON with this structure:

```json
{
  "vendor_name": "ACME Corp",
  "vendor_tax_id": "12-3456789",
  "invoice_number": "INV-12345",
  "invoice_date": "2026-05-20",
  "due_date": "2026-06-20",
  "po_number": "PO-2026-001",
  "currency": "USD",
  "line_items": [
    {
      "description": "Professional Services",
      "quantity": 10,
      "unit_price": 100.00,
      "amount": 1000.00
    }
  ],
  "tax_amount": 100.00,
  "total_amount": 1100.00
}
```

## Assessment Output

Each assessment includes:

### Reliability Band & Score
- **High** (85-100): Strong signals, minimal risk
- **Medium** (60-84): Some flags, review recommended
- **Low** (35-59): Multiple issues, careful review needed
- **Critical** (0-34): Serious fraud/compliance risks

### Top Factors
The 3 most impactful signals affecting the score:
- Extraction confidence issues
- Authenticity signals (vendor match, duplicates, arithmetic)
- Compliance violations (policy thresholds)

### Detailed Explanation
Human-readable rationale citing specific signals and evidence.

### Flags
Severity-ranked alerts:
- **critical**: Immediate investigation required
- **high**: Significant risk factor
- **medium**: Worth noting
- **low**: Minor concern

### Fields Summary
Extracted invoice data with high-confidence fields highlighted.

## Architecture

The system implements the 11-phase Agent Factory design:

### Agents
1. **Extraction Agent** (A2): Converts raw invoice data → canonical field schema
2. **Validation Agent** (A3): Authenticity checks (arithmetic, vendor match, duplicates)
3. **Compliance Agent** (A4): Policy rule evaluation
4. **Scoring Agent** (A5): Aggregates signals → reliability band + explanation
5. **Orchestrator** (A1): Supervisor coordinating all stages

### Tool Services
- **Vendor Database**: Vendor registry lookup and fuzzy matching
- **Duplicate Index**: Exact and near-duplicate detection
- **Policy Engine**: Rule-based compliance evaluation
- **Arithmetic Validator**: Line items → tax → total verification

### Design Principles
- **No auto-approval**: Hard-coded constraint; all output is advisory
- **Determinism for high-stakes ops**: Math, lookups, and rule evaluation use deterministic services
- **Evidence trail**: Every signal cited with source references for audit
- **Graceful degradation**: Tool failures convert to flags rather than crashes

## Data Models

### Core Models (models.py)
- `ExtractedInvoice`: Structured invoice fields with per-field confidence
- `ValidationResult`: Authenticity signals + vendor/duplicate status
- `ComplianceResult`: Policy violations + approval tier hints
- `ReliabilityAssessment`: Final score + explanation + flags
- `EvidenceBundle`: Shared state across the pipeline

### Enums
- `Band`: High, Medium, Low, Critical
- `Severity`: info, low, medium, high, critical

## Integration Points

### Mock Databases (db.py)
- **MockVendorDB**: Pre-populated with ACME, TechSolutions, Global Services
- **MockPolicyEngine**: Amount thresholds, currency restrictions, vendor blocks
- **MockDuplicateIndex**: Exact + fuzzy matching with configurable thresholds

For production, replace with:
- Real vendor database (read-only via API)
- External policy rule engine
- Invoice history store with indexing

## Example Assessments

### Clean Invoice (High)
```
Reliability: High (Score: 90/100)

✓ All fields extracted with high confidence
✓ Vendor "ACME Corp" matched in registry
✓ No duplicates found
✓ Compliant with policy
→ Recommendation: Human approval recommended (standard review)
```

### Duplicate (Critical)
```
Reliability: Critical (Score: 10/100)

🚩 Exact duplicate found: INV-2031 from ACME Corp on 2026-05-15
→ Recommendation: REJECT — likely fraud (resubmission attempt)
```

### Unknown Vendor (Low)
```
Reliability: Low (Score: 40/100)

⚠️ Vendor "Mystery Vendor LLC" not in registry
→ Recommendation: Verify vendor identity before approval; request business justification
```

### Over Threshold (Low)
```
Reliability: Low (Score: 45/100)

📋 Policy violations:
  • Amount ($13,200) exceeds high-tier threshold ($10,000)
→ Recommendation: Route to Director-level approval
```

## Deployment Notes

### Requirements
- Python 3.8+
- Optional: `rich` library (for colored CLI output)

### Performance
- Single invoice: <100ms (mock services)
- Batch mode: Scales linearly with volume
- Cost: Minimal (deterministic services only; no LLM calls in mock)

### Audit & Compliance
- Every assessment includes immutable Evidence Bundle
- Full signal chain with source references
- JSON export for audit logs and compliance reviews
- Idempotent re-assessment (same invoice → same result)

## Future Enhancements

From Phase 11 of the Agent Factory report:

1. **Shadow-mode evaluation**: Run on live invoices, collect human-decision ground truth
2. **Canary rollout**: Gradual exposure to limited vendor/team subset
3. **Calibration tuning**: Improve AUC ≥0.85 on human decision correlation
4. **3-way matching** (Q2): Add PO ↔ Receipt matching capability
5. **Real LLM integration**: Replace mock agents with Claude API for complex reasoning
6. **Document AI**: Support PDFs and images with real OCR + vision models
7. **Multi-language**: Support invoices in additional languages
8. **Real integrations**: Connect to actual vendor DB, policy engine, and approval workflow

## References

- Full Agent Development Pack: `invoice_agent_report.md`
- Agent Factory Orchestrator: `agent_factory/` module
- Architecture documentation: Phase 4 (Multi-Agent Orchestration)
- Evaluation framework: Phase 8 (Evaluation Design)
- Safety & testing: Phases 9–11
