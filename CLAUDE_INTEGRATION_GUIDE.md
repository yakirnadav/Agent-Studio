# Claude API Integration Guide

## Overview

The Invoice Reliability Assessment Agent now integrates with Claude API for intelligent reasoning and explanations. This guide shows how to use it with real Claude intelligence.

## Quick Start

### 1. Set Your API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or add it to your shell profile:
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Run the Claude-Integrated CLI

```bash
# Check a clean invoice with Claude
python check_invoice_claude.py clean --mode claude

# Check with mock agents (fallback)
python check_invoice_claude.py clean --mode mock

# Run the interactive demo
python demo_claude_invoice_checker.py

# Save assessment to JSON
python check_invoice_claude.py clean --mode claude --output assessment.json
```

## What Claude Does

### In the Pipeline

**Extraction Agent (Claude)**
- Uses Claude's reasoning to extract invoice fields from text
- Handles ambiguous layouts and formats
- Returns structured JSON with field confidence scores
- Supports multi-language invoices

**Validation Agent (Claude + Deterministic)**
- Deterministic: Vendor DB lookup, duplicate detection, arithmetic checking
- Claude: Analyzes invoice format for anomalies and red flags
- Combines both for holistic authenticity assessment

**Compliance Agent (Deterministic)**
- Policy rules are deterministic (non-negotiable)
- Ensures audit trail and reproducibility

**Scoring Agent (Claude)**
- Aggregates all evidence signals
- Generates nuanced reliability scores
- Produces human-readable explanations citing specific evidence
- Considers context and edge cases

### Key Benefits

✅ **Intelligent extraction** — Handles scans, poor formatting, multi-language  
✅ **Contextual reasoning** — Understands invoice anomalies humans would catch  
✅ **Clear explanations** — Why the score is what it is, in plain language  
✅ **Audit trail** — All Claude reasoning logged in JSON output  
✅ **Graceful fallback** — Auto-reverts to deterministic scoring if Claude fails  

## CLI Usage

### List Samples
```bash
python check_invoice_claude.py --list-samples
```

### Check a Sample Invoice
```bash
python check_invoice_claude.py clean --mode claude
python check_invoice_claude.py duplicate --mode claude
python check_invoice_claude.py unknown_vendor --mode claude
```

### Check a Custom Invoice
```bash
# JSON file
python check_invoice_claude.py my_invoice.json --mode claude

# Save result
python check_invoice_claude.py my_invoice.json --mode claude --output result.json
```

### Compare Modes
```bash
# Mock agent (fast, deterministic)
python check_invoice_claude.py clean --mode mock

# Claude agent (intelligent, contextual)
python check_invoice_claude.py clean --mode claude
```

## Running the Demo

The interactive demo shows all capabilities:

```bash
python demo_claude_invoice_checker.py
```

This runs 4 test cases:
1. **Clean invoice** — Happy path with known vendor
2. **Suspicious invoice** — High amount + unknown vendor
3. **Duplicate invoice** — Fraud detection
4. **Multi-currency invoice** — EUR with policy checks

Each is assessed with mock agents (or Claude if API key is set).

## JSON Output Format

When saving with `--output`, you get a complete audit trail:

```json
{
  "assessment_id": "uuid",
  "invoice_hash": "sha256",
  "extracted_invoice": {
    "vendor_name": "...",
    "total_amount": 1250.0,
    "currency": "USD",
    "per_field_confidence": {...},
    "line_items": [...]
  },
  "validation_result": {
    "vendor_status": "matched",
    "duplicate_status": "none",
    "authenticity_signals": [...]
  },
  "compliance_result": {
    "compliance_status": "compliant",
    "violations": [...]
  },
  "assessment": {
    "reliability": {
      "band": "High",
      "score": 90
    },
    "explanation": "Claude's reasoning explaining the score...",
    "top_reasons": [...]
  }
}
```

## Architecture

```
Invoice (JSON/text)
    ↓
Orchestrator (supervisor)
    ├→ Extraction Agent (Claude)
    │  └→ Structured fields + confidence
    ├→ Validation Agent (Deterministic + Claude)
    │  ├→ Vendor DB lookup (deterministic)
    │  ├→ Duplicate index check (deterministic)
    │  ├→ Arithmetic validation (deterministic)
    │  └→ Format analysis (Claude)
    ├→ Compliance Agent (Deterministic)
    │  └→ Policy rule evaluation
    └→ Scoring Agent (Claude)
       └→ Reliability band + explanation

↓
Advisory Assessment (never auto-approves)
```

## Models Used

- **Extraction**: `claude-opus-4-8` (vision + reasoning)
- **Validation**: `claude-opus-4-8` (format analysis)
- **Scoring**: `claude-opus-4-8` (explanation generation)
- **Fallback**: Deterministic if Claude fails

## Cost Considerations

Per invoice (with Claude):
- Extraction: ~1,200 tokens (extraction prompt + response)
- Validation: ~800 tokens (format analysis)
- Scoring: ~600 tokens (score + explanation)
- **Total**: ~2,600 tokens ≈ $0.05–$0.10 per invoice

Deterministic services add minimal cost (vendor lookups, policy evaluation).

## Extending for Production

### Real Vendor Database
Replace `MockVendorDB` in `db.py`:
```python
class RealVendorDB:
    def __init__(self, api_url, api_key):
        self.api = VendorAPI(api_url, api_key)
    
    def lookup(self, name, tax_id=None):
        return self.api.search(name, tax_id)
```

### Real Policy Engine
Replace `MockPolicyEngine`:
```python
class RealPolicyEngine:
    def __init__(self, api_url, api_key):
        self.api = PolicyAPI(api_url, api_key)
    
    def evaluate(self, amount, currency, vendor, policy_version):
        return self.api.eval_rules(amount, currency, vendor, policy_version)
```

### Document AI (PDFs/Images)
Update `ClaudeExtractionAgent.extract()` to use Claude's vision:
```python
def extract(self, invoice_bytes: bytes, file_type: str):
    # Send to Claude with vision
    message = self.client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/{file_type}",
                        "data": base64.b64encode(invoice_bytes).decode()
                    }
                },
                {"type": "text", "text": "Extract invoice fields..."}
            ]
        }]
    )
```

### Real Approval Workflow Integration
Add after scoring:
```python
bundle = orchestrator.assess_invoice(invoice_data)

# Send to approval workflow
if bundle.assessment:
    approval_task = {
        "invoice_hash": bundle.invoice_hash,
        "assessment": bundle.assessment.to_dict(),
        "status": "pending_approval",
        "created_at": datetime.now().isoformat(),
    }
    workflow_api.create_approval_task(approval_task)
```

### Monitoring & Observability
Add to `ClaudeOrchestrator`:
```python
import logging
logger = logging.getLogger(__name__)

# Log all Claude API calls
logger.info(f"Claude API call: {model}, tokens_in={usage.input_tokens}, tokens_out={usage.output_tokens}")

# Track assessment metrics
metrics.increment("invoices.assessed")
metrics.gauge("score.distribution", assessment.score)
metrics.timing("assessment.duration_ms", duration)
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
# Check if env var is set
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify it's set
python -c "import os; print(os.environ.get('ANTHROPIC_API_KEY'))"
```

### Claude API quota exceeded
- Check your Anthropic console usage
- Reduce batch sizes or implement rate limiting
- Add retry logic with exponential backoff

### JSON parsing errors from Claude
The CLI has fallback logic to handle malformed responses:
1. Tries to extract JSON from Claude's response
2. Falls back to deterministic scoring if extraction fails
3. Logs the raw response for debugging

## Examples

### Example 1: Assessment with Claude
```bash
python check_invoice_claude.py clean --mode claude
```

Output:
```
Processing invoice: clean (CLAUDE)

Invoice Reliability Assessment

Reliability: High (Score: 90/100)

Explanation:
All fields extracted with high confidence from a known vendor (ACME Corp).
Vendor matches registry exactly, no duplicates detected, and arithmetic is
consistent across line items and tax. Policy compliant. Human review
recommended for final approval as per procedure.

Fields Summary:
  Vendor: ACME Corp
  Amount: 1375.0 USD
  Date: 2026-05-20
  Invoice Number: INV-12345
  Line Items Count: 3

✓ Assessment complete — human review required.
```

### Example 2: Save to JSON
```bash
python check_invoice_claude.py over_threshold --mode claude --output policy_violation.json
cat policy_violation.json | jq '.assessment.explanation'
```

Output:
```
"The invoice exceeds the high-tier approval threshold of $10,000 with a
total of $13,200. While the vendor (TechSolutions Inc) is verified and
arithmetic is consistent, the amount triggers Director-level review per
policy POL-002. Recommend escalating to Director for approval."
```

### Example 3: Compare Mock vs Claude
```bash
echo "=== With Mock Agents ===" 
python check_invoice_claude.py unknown_vendor --mode mock

echo -e "\n=== With Claude API ===" 
python check_invoice_claude.py unknown_vendor --mode claude
```

## API Reference

### ClaudeOrchestrator

```python
orchestrator = ClaudeOrchestrator()
bundle = orchestrator.assess_invoice(invoice_data, invoice_text)

# Access results
print(bundle.assessment.band)      # Band.High / .Medium / .Low / .Critical
print(bundle.assessment.score)     # 0-100
print(bundle.assessment.explanation)  # Human-readable text
```

### CLI Arguments

```
python check_invoice_claude.py [invoice] [options]

positional:
  invoice              Path to invoice JSON, or sample name

options:
  --list-samples       Show available samples
  --output FILE        Save result to JSON
  --sample NAME        Use a sample invoice
  --mode {claude,mock} Use Claude or mock agents (default: claude)
```

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Verify your API key is set
3. Check Anthropic console for quota/usage
4. Review the JSON output for error details

---

**Ready to assess invoices with AI?**

```bash
export ANTHROPIC_API_KEY="your-key"
python check_invoice_claude.py clean --mode claude
```
