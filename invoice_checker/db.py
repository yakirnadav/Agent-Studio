"""Mock databases and services for vendor lookup, policy rules, duplicate detection."""
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import hashlib


class MockVendorDB:
    """Mock vendor database."""

    def __init__(self):
        self.vendors = {
            "acme": {"id": "V001", "name": "ACME Corp", "tax_id": "12-3456789", "status": "active"},
            "techsolutions": {
                "id": "V002",
                "name": "TechSolutions Inc",
                "tax_id": "98-7654321",
                "status": "active",
            },
            "globalservices": {
                "id": "V003",
                "name": "Global Services Ltd",
                "tax_id": "55-1234567",
                "status": "active",
            },
            "unknown_vendor": {"id": None, "status": "not_found"},
        }

    def lookup(self, name: str, tax_id: Optional[str] = None) -> Dict:
        """Look up vendor by name or tax ID."""
        name_lower = name.lower()

        # Exact match
        for key, vendor in self.vendors.items():
            if key == name_lower or vendor.get("name", "").lower() == name_lower:
                return {"status": "matched", "vendor": vendor}

            # Fuzzy match
            if self._similarity(name_lower, vendor.get("name", "").lower()) > 0.7:
                return {
                    "status": "fuzzy",
                    "vendor": vendor,
                    "similarity_score": self._similarity(name_lower, vendor.get("name", "").lower()),
                }

        return {"status": "not_found", "vendor": None}

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()


class MockPolicyEngine:
    """Mock expense policy rule engine."""

    def __init__(self):
        self.rules = [
            {"id": "POL-001", "name": "Standard amount threshold", "type": "amount_limit", "value": 5000},
            {"id": "POL-002", "name": "High tier threshold", "type": "amount_limit", "value": 10000},
            {"id": "POL-003", "name": "Prohibited vendors", "vendors": ["banned.com"], "type": "vendor_block"},
            {"id": "POL-004", "name": "Allowed currencies", "currencies": ["USD", "EUR", "GBP"], "type": "currency"},
        ]

    def evaluate(self, amount: float, currency: str, vendor: str, policy_version: str = "1.0") -> Dict:
        """Evaluate invoice against policy rules."""
        violations = []

        # Amount threshold check
        if amount > 10000:
            violations.append(
                {
                    "rule_id": "POL-002",
                    "description": "Amount exceeds high-tier threshold ($10,000)",
                    "observed": f"${amount}",
                    "threshold": "$10,000",
                    "severity": "high",
                    "approval_tier": "Director",
                }
            )
        elif amount > 5000:
            violations.append(
                {
                    "rule_id": "POL-001",
                    "description": "Amount exceeds standard threshold ($5,000)",
                    "observed": f"${amount}",
                    "threshold": "$5,000",
                    "severity": "medium",
                    "approval_tier": "Manager",
                }
            )

        # Currency check
        if currency not in ["USD", "EUR", "GBP"]:
            violations.append(
                {
                    "rule_id": "POL-004",
                    "description": f"Currency {currency} not in approved list",
                    "observed": currency,
                    "threshold": "USD, EUR, GBP",
                    "severity": "medium",
                }
            )

        # Vendor block check
        if "banned" in vendor.lower():
            violations.append(
                {
                    "rule_id": "POL-003",
                    "description": "Vendor is on prohibited list",
                    "observed": vendor,
                    "threshold": "Must be approved vendor",
                    "severity": "critical",
                }
            )

        status = "violations_found" if violations else "compliant"
        approval_tier = violations[0].get("approval_tier") if violations else None

        return {
            "status": status,
            "violations": violations,
            "approval_tier": approval_tier,
            "policy_version": policy_version,
        }


class MockDuplicateIndex:
    """Mock duplicate detection service."""

    def __init__(self):
        self.history: Dict[str, Dict] = {}

        # Pre-populate with a known duplicate for testing
        dup_key = self._make_key("ACME Corp", "INV-2031", 1250.00)
        self.history[dup_key] = {
            "vendor": "ACME Corp",
            "invoice_number": "INV-2031",
            "amount": 1250.00,
            "date": "2026-05-15",
            "hash": dup_key,
        }

    def check(self, vendor: str, invoice_number: str, amount: float) -> Dict:
        """Check for duplicates and near-duplicates."""
        key = self._make_key(vendor, invoice_number, amount)
        similarity_threshold = 0.85

        # Exact match
        if key in self.history:
            return {
                "status": "exact",
                "matched_invoices": [self.history[key]],
                "match_score": 1.0,
            }

        # Fuzzy match against all historical invoices
        fuzzy_matches = []
        for hist_key, hist_invoice in self.history.items():
            similarity = self._calculate_similarity(
                (vendor, invoice_number, amount), (hist_invoice["vendor"], hist_invoice["invoice_number"], hist_invoice["amount"])
            )
            if similarity >= similarity_threshold:
                fuzzy_matches.append({**hist_invoice, "match_score": similarity})

        if fuzzy_matches:
            return {
                "status": "near",
                "matched_invoices": fuzzy_matches,
                "match_score": max(m["match_score"] for m in fuzzy_matches),
            }

        return {"status": "none", "matched_invoices": [], "match_score": None}

    def record(self, vendor: str, invoice_number: str, amount: float, date: str):
        """Record invoice in history for future duplicate detection."""
        key = self._make_key(vendor, invoice_number, amount)
        self.history[key] = {
            "vendor": vendor,
            "invoice_number": invoice_number,
            "amount": amount,
            "date": date,
            "hash": key,
        }

    @staticmethod
    def _make_key(vendor: str, invoice_number: str, amount: float) -> str:
        """Create a hash key for the invoice."""
        key_str = f"{vendor.lower()}:{invoice_number.lower()}:{amount}"
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    @staticmethod
    def _calculate_similarity(a: Tuple, b: Tuple) -> float:
        """Calculate similarity between two invoice tuples."""
        # Vendor similarity
        vendor_sim = SequenceMatcher(None, a[0].lower(), b[0].lower()).ratio()
        # Invoice number similarity
        inv_num_sim = SequenceMatcher(None, a[1].lower(), b[1].lower()).ratio()
        # Amount similarity (within 5%)
        amount_sim = 1.0 if abs(a[2] - b[2]) / max(a[2], b[2]) < 0.05 else 0.0

        # Weighted average: vendor 40%, invoice 40%, amount 20%
        return vendor_sim * 0.4 + inv_num_sim * 0.4 + amount_sim * 0.2
