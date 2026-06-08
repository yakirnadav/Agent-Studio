"""Invoice service: wraps the invoice_checker package."""
import sys
import os
import json
import base64
import hashlib
import uuid
from typing import Optional

sys.path.insert(0, '/home/user/Agent-Studio')

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def extract_from_image(image_bytes: bytes, media_type: str) -> dict:
    """Use Claude vision to extract structured invoice data from image/PDF."""
    from anthropic import Anthropic
    client = Anthropic()
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64.b64encode(image_bytes).decode()
                    }
                },
                {
                    "type": "text",
                    "text": """Extract invoice data from this image and return ONLY valid JSON with these fields:
{
  "vendor_name": "string",
  "vendor_tax_id": "string or null",
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD or null",
  "po_number": "string or null",
  "currency": "3-letter ISO code",
  "line_items": [{"description": "string", "quantity": number, "unit_price": number, "amount": number}],
  "tax_amount": number,
  "total_amount": number
}
Return ONLY the JSON, no explanation."""
                }
            ]
        }]
    )
    text = message.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(text)


def run_assessment(invoice_data: dict) -> dict:
    """Run the invoice through the pipeline and return a serialisable result dict."""
    if ANTHROPIC_API_KEY:
        from invoice_checker.claude_agents import ClaudeOrchestrator
        orchestrator = ClaudeOrchestrator()
    else:
        from invoice_checker.agents import Orchestrator
        orchestrator = Orchestrator()

    bundle = orchestrator.run(invoice_data)
    return bundle.to_dict()


def assess_invoice_data(invoice_data: dict) -> dict:
    """Accept structured invoice dict and return full assessment."""
    return run_assessment(invoice_data)


def assess_json_file(content: bytes) -> dict:
    """Parse a JSON file and assess it."""
    invoice_data = json.loads(content.decode("utf-8"))
    return run_assessment(invoice_data)


def assess_image_file(content: bytes, media_type: str) -> dict:
    """Extract from image then assess."""
    invoice_data = extract_from_image(content, media_type)
    return run_assessment(invoice_data)


def assess_pdf_file(content: bytes) -> dict:
    """Convert PDF first page to image, then assess."""
    try:
        from PIL import Image
        import io
        # Try to use pdf2image if available
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(content, first_page=1, last_page=1)
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            return assess_image_file(buf.getvalue(), "image/png")
        except ImportError:
            pass
    except Exception:
        pass

    # Fallback: send PDF bytes directly as base64 to Claude
    return assess_image_file(content, "application/pdf")
