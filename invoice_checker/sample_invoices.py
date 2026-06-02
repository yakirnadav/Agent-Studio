"""Sample invoice generators for testing."""
import json
from datetime import datetime, timedelta


def generate_clean_invoice():
    """Generate a clean, compliant invoice from a known vendor."""
    return {
        "vendor_name": "ACME Corp",
        "vendor_tax_id": "12-3456789",
        "invoice_number": "INV-12345",
        "invoice_date": "2026-05-20",
        "due_date": "2026-06-20",
        "po_number": "PO-2026-001",
        "currency": "USD",
        "line_items": [
            {"description": "Professional Services", "quantity": 10, "unit_price": 100.00, "amount": 1000.00},
            {"description": "Software License", "quantity": 1, "unit_price": 200.00, "amount": 200.00},
            {"description": "Support & Maintenance", "quantity": 1, "unit_price": 50.00, "amount": 50.00},
        ],
        "tax_amount": 125.00,
        "total_amount": 1375.00,
    }


def generate_duplicate_invoice():
    """Generate an invoice that matches a known duplicate."""
    return {
        "vendor_name": "ACME Corp",
        "vendor_tax_id": "12-3456789",
        "invoice_number": "INV-2031",
        "invoice_date": "2026-05-15",
        "due_date": "2026-06-15",
        "po_number": "PO-2026-002",
        "currency": "USD",
        "line_items": [
            {"description": "Services", "quantity": 1, "unit_price": 1250.00, "amount": 1250.00},
        ],
        "tax_amount": 0.00,
        "total_amount": 1250.00,
    }


def generate_unknown_vendor_invoice():
    """Generate an invoice from an unknown vendor."""
    return {
        "vendor_name": "Mystery Vendor LLC",
        "vendor_tax_id": "99-9999999",
        "invoice_number": "INV-99999",
        "invoice_date": "2026-05-21",
        "due_date": "2026-06-21",
        "po_number": None,
        "currency": "USD",
        "line_items": [
            {"description": "Consulting", "quantity": 5, "unit_price": 300.00, "amount": 1500.00},
        ],
        "tax_amount": 150.00,
        "total_amount": 1650.00,
    }


def generate_over_threshold_invoice():
    """Generate an invoice exceeding policy thresholds."""
    return {
        "vendor_name": "TechSolutions Inc",
        "vendor_tax_id": "98-7654321",
        "invoice_number": "INV-55555",
        "invoice_date": "2026-05-22",
        "due_date": "2026-06-22",
        "po_number": "PO-2026-003",
        "currency": "USD",
        "line_items": [
            {
                "description": "System Implementation",
                "quantity": 1,
                "unit_price": 12000.00,
                "amount": 12000.00,
            },
        ],
        "tax_amount": 1200.00,
        "total_amount": 13200.00,
    }


def generate_bad_arithmetic_invoice():
    """Generate an invoice with arithmetic inconsistencies."""
    return {
        "vendor_name": "Global Services Ltd",
        "vendor_tax_id": "55-1234567",
        "invoice_number": "INV-77777",
        "invoice_date": "2026-05-23",
        "due_date": "2026-06-23",
        "po_number": "PO-2026-004",
        "currency": "USD",
        "line_items": [
            {"description": "Service A", "quantity": 2, "unit_price": 500.00, "amount": 1000.00},
            {"description": "Service B", "quantity": 3, "unit_price": 250.00, "amount": 750.00},
        ],
        "tax_amount": 100.00,
        "total_amount": 3000.00,  # Should be 1750 + 175 tax = 1925 (MISMATCH)
    }


def generate_foreign_currency_invoice():
    """Generate an invoice in a foreign currency."""
    return {
        "vendor_name": "Global Services Ltd",
        "vendor_tax_id": "55-1234567",
        "invoice_number": "INV-33333",
        "invoice_date": "2026-05-24",
        "due_date": "2026-06-24",
        "po_number": "PO-2026-005",
        "currency": "EUR",
        "line_items": [
            {"description": "International Consulting", "quantity": 1, "unit_price": 9000.00, "amount": 9000.00},
        ],
        "tax_amount": 900.00,
        "total_amount": 9900.00,  # ~10,890 USD at 1.1 rate (over threshold)
    }


SAMPLE_INVOICES = {
    "clean": generate_clean_invoice,
    "duplicate": generate_duplicate_invoice,
    "unknown_vendor": generate_unknown_vendor_invoice,
    "over_threshold": generate_over_threshold_invoice,
    "bad_arithmetic": generate_bad_arithmetic_invoice,
    "foreign_currency": generate_foreign_currency_invoice,
}


def list_samples():
    """List available sample invoice types."""
    return list(SAMPLE_INVOICES.keys())


def get_sample(sample_type: str):
    """Get a sample invoice by type."""
    if sample_type not in SAMPLE_INVOICES:
        raise ValueError(f"Unknown sample type: {sample_type}. Available: {list_samples()}")
    return SAMPLE_INVOICES[sample_type]()
