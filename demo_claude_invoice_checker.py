#!/usr/bin/env python3
"""Interactive demo of the Claude-integrated Invoice Reliability Assessment Agent."""
import os
import json
from invoice_checker.claude_agents import ClaudeOrchestrator
from invoice_checker.agents import Orchestrator

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    _rich = True
    console = Console()
except ImportError:
    _rich = False
    console = None


def print_section(title: str):
    """Print a section header."""
    if _rich:
        console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]")
        console.print(f"[bold cyan]{title:^70}[/bold cyan]")
        console.print(f"[bold cyan]{'=' * 70}[/bold cyan]\n")
    else:
        print(f"\n{'=' * 70}")
        print(f"{title:^70}")
        print(f"{'=' * 70}\n")


def print_result(bundle, agent_type: str):
    """Display assessment result."""
    if not bundle.assessment:
        if _rich:
            console.print("[red]❌ Assessment failed[/red]")
        else:
            print("❌ Assessment failed")
        return

    assessment = bundle.assessment
    color = {
        "High": "green",
        "Medium": "yellow",
        "Low": "red",
        "Critical": "red",
    }.get(assessment.band.value, "white")

    if _rich:
        console.print(
            f"[bold {color}]Reliability: {assessment.band.value}[/bold {color}] "
            f"[dim](Score: {assessment.score}/100)[/dim]"
        )
        console.print(f"[dim]Agent type: {agent_type}[/dim]\n")
        console.print(assessment.explanation)

        if bundle.validation_result and bundle.validation_result.authenticity_signals:
            console.print("\n[bold yellow]Authenticity Signals:[/bold yellow]")
            for sig in bundle.validation_result.authenticity_signals:
                severity_color = "red" if sig.severity.value in ["critical", "high"] else "yellow"
                console.print(f"  [{severity_color}]{sig.severity.value.upper()}[/{severity_color}] {sig.code}: {sig.detail}")

        if bundle.compliance_result and bundle.compliance_result.violations:
            console.print("\n[bold yellow]Policy Violations:[/bold yellow]")
            for v in bundle.compliance_result.violations:
                console.print(f"  • {v.description} (Rule {v.rule_id})")
    else:
        print(f"Reliability: {assessment.band.value} (Score: {assessment.score}/100)")
        print(f"Agent type: {agent_type}\n")
        print(assessment.explanation)


def demo_clean_invoice(use_claude: bool):
    """Demo 1: Clean, compliant invoice."""
    print_section("DEMO 1: Clean Invoice from Known Vendor")

    invoice = {
        "vendor_name": "TechSolutions Inc",
        "vendor_tax_id": "98-7654321",
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-06-01",
        "due_date": "2026-07-01",
        "po_number": "PO-2026-100",
        "currency": "USD",
        "line_items": [
            {"description": "Cloud Infrastructure Setup", "quantity": 1, "unit_price": 1500.00, "amount": 1500.00},
            {"description": "24/7 Support (3 months)", "quantity": 3, "unit_price": 500.00, "amount": 1500.00},
        ],
        "tax_amount": 300.00,
        "total_amount": 3300.00,
    }

    if _rich:
        console.print("[dim]Assessing clean invoice from known vendor with proper tax and line items...[/dim]\n")

    orchestrator = ClaudeOrchestrator() if use_claude else Orchestrator()
    bundle = orchestrator.assess_invoice(invoice)
    print_result(bundle, "Claude" if use_claude else "Mock")


def demo_suspicious_invoice(use_claude: bool):
    """Demo 2: Suspicious invoice with red flags."""
    print_section("DEMO 2: Suspicious Invoice - High Amount + Unknown Vendor")

    invoice = {
        "vendor_name": "XYZ Consulting Group",
        "vendor_tax_id": "99-9999999",
        "invoice_number": "INV-2026-SUSP",
        "invoice_date": "2026-06-01",
        "due_date": "2026-06-15",
        "po_number": None,
        "currency": "USD",
        "line_items": [
            {"description": "Professional Consulting Services", "quantity": 1, "unit_price": 15000.00, "amount": 15000.00},
        ],
        "tax_amount": 1500.00,
        "total_amount": 16500.00,
    }

    if _rich:
        console.print("[dim]Assessing suspicious invoice: high amount, unknown vendor, no PO...[/dim]\n")

    orchestrator = ClaudeOrchestrator() if use_claude else Orchestrator()
    bundle = orchestrator.assess_invoice(invoice)
    print_result(bundle, "Claude" if use_claude else "Mock")


def demo_duplicate_invoice(use_claude: bool):
    """Demo 3: Duplicate invoice (fraud detection)."""
    print_section("DEMO 3: Duplicate Invoice - Fraud Detection")

    invoice = {
        "vendor_name": "ACME Corp",
        "vendor_tax_id": "12-3456789",
        "invoice_number": "INV-2031",
        "invoice_date": "2026-05-15",
        "due_date": "2026-06-15",
        "po_number": "PO-2026-050",
        "currency": "USD",
        "line_items": [
            {"description": "Services", "quantity": 1, "unit_price": 1250.00, "amount": 1250.00},
        ],
        "tax_amount": 0.00,
        "total_amount": 1250.00,
    }

    if _rich:
        console.print("[dim]Assessing exact duplicate of previously submitted invoice...[/dim]\n")

    orchestrator = ClaudeOrchestrator() if use_claude else Orchestrator()
    bundle = orchestrator.assess_invoice(invoice)
    print_result(bundle, "Claude" if use_claude else "Mock")


def demo_multicurrency_invoice(use_claude: bool):
    """Demo 4: Multi-currency invoice with policy check."""
    print_section("DEMO 4: Multi-Currency Invoice (EUR)")

    invoice = {
        "vendor_name": "Global Services Ltd",
        "vendor_tax_id": "55-1234567",
        "invoice_number": "INV-2026-EUR",
        "invoice_date": "2026-06-01",
        "due_date": "2026-07-01",
        "po_number": "PO-2026-200",
        "currency": "EUR",
        "line_items": [
            {"description": "International Consulting", "quantity": 8, "unit_price": 750.00, "amount": 6000.00},
        ],
        "tax_amount": 900.00,
        "total_amount": 6900.00,
    }

    if _rich:
        console.print("[dim]Assessing EUR invoice with valid vendor but near policy threshold...[/dim]\n")

    orchestrator = ClaudeOrchestrator() if use_claude else Orchestrator()
    bundle = orchestrator.assess_invoice(invoice)
    print_result(bundle, "Claude" if use_claude else "Mock")


def main():
    """Run the interactive demo."""
    if _rich:
        console.print("\n")
        console.print("[bold magenta]" + "=" * 70 + "[/bold magenta]")
        console.print("[bold magenta]  INVOICE RELIABILITY ASSESSMENT AGENT - CLAUDE API DEMO[/bold magenta]")
        console.print("[bold magenta]" + "=" * 70 + "[/bold magenta]\n")
    else:
        print("\n" + "=" * 70)
        print("  INVOICE RELIABILITY ASSESSMENT AGENT - CLAUDE API DEMO")
        print("=" * 70 + "\n")

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        if _rich:
            console.print("[yellow]⚠️  ANTHROPIC_API_KEY not set. Using mock agents for demo.[/yellow]\n")
        else:
            print("⚠️  ANTHROPIC_API_KEY not set. Using mock agents for demo.\n")
        use_claude = False
    else:
        if _rich:
            console.print("[green]✓ Claude API key found. Running with real Claude intelligence.[/green]\n")
        else:
            print("✓ Claude API key found. Running with real Claude intelligence.\n")
        use_claude = True

    # Run demos
    demo_clean_invoice(use_claude)
    demo_suspicious_invoice(use_claude)
    demo_duplicate_invoice(use_claude)
    demo_multicurrency_invoice(use_claude)

    # Summary
    print_section("DEMO COMPLETE")
    if _rich:
        console.print("[bold green]✓ All assessments complete[/bold green]")
        console.print("""
[dim]The Invoice Reliability Assessment Agent successfully:[/dim]
  • Extracted structured invoice fields
  • Validated authenticity signals (vendor, duplicates, arithmetic)
  • Checked policy compliance (thresholds, currencies, tiers)
  • Generated explainable reliability scores
  • Produced audit-ready JSON assessments

[dim]Claude's reasoning was used to:[/dim]
  • Analyze format plausibility
  • Generate contextual explanations
  • Score reliability with nuanced judgment
  • Provide human-friendly rationale

[bold]Next steps:[/bold]
  • Connect to real vendor database
  • Integrate document AI for PDFs/images
  • Add real expense approval workflow
  • Deploy to production with SLA monitoring
""")
    else:
        print("✓ All assessments complete")
        print("""
The Invoice Reliability Assessment Agent successfully:
  • Extracted structured invoice fields
  • Validated authenticity signals (vendor, duplicates, arithmetic)
  • Checked policy compliance (thresholds, currencies, tiers)
  • Generated explainable reliability scores
  • Produced audit-ready JSON assessments

Claude's reasoning was used to:
  • Analyze format plausibility
  • Generate contextual explanations
  • Score reliability with nuanced judgment
  • Provide human-friendly rationale

Next steps:
  • Connect to real vendor database
  • Integrate document AI for PDFs/images
  • Add real expense approval workflow
  • Deploy to production with SLA monitoring
""")


if __name__ == "__main__":
    main()
