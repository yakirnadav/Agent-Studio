#!/usr/bin/env python3
"""CLI tool for the Invoice Reliability Assessment Agent (IRAA)."""
import argparse
import json
import sys
from pathlib import Path
from .agents import Orchestrator
from .sample_invoices import SAMPLE_INVOICES, list_samples
from .models import EvidenceBundle

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


def format_assessment(bundle: EvidenceBundle) -> str:
    """Format the assessment for display."""
    if not bundle.assessment:
        return "❌ Assessment failed — no score generated."

    assessment = bundle.assessment

    if _rich:
        output = []

        # Header
        output.append(f"[bold cyan]Invoice Reliability Assessment[/bold cyan]")
        output.append("")

        # Reliability score
        color = {
            "High": "green",
            "Medium": "yellow",
            "Low": "red",
            "Critical": "red",
        }.get(assessment.band.value, "white")

        output.append(
            f"[bold {color}]Reliability: {assessment.band.value}[/bold {color}] "
            f"[dim](Score: {assessment.score}/100)[/dim]"
        )
        output.append("")

        # Top reasons
        if assessment.top_reasons:
            output.append("[bold]Top Factors:[/bold]")
            for reason in assessment.top_reasons:
                output.append(f"  • {reason.contribution}")
            output.append("")

        # Explanation
        output.append("[bold]Explanation:[/bold]")
        output.append(assessment.explanation)
        output.append("")

        # Flags
        if assessment.flags:
            output.append("[bold yellow]⚠️  Flags:[/bold yellow]")
            for flag in assessment.flags:
                output.append(
                    f"  • [{flag.severity.value}] {flag.code}: {flag.evidence_ref}"
                )
            output.append("")

        # Fields summary
        if assessment.fields_summary:
            output.append("[bold]Fields Summary:[/bold]")
            for key, value in assessment.fields_summary.items():
                output.append(f"  {key.replace('_', ' ').title()}: {value}")

        output.append("")
        output.append("[bold green]✓ Assessment complete — human review required.[/bold green]")

        return "\n".join(output)

    else:
        # Plain text output
        lines = [
            "=" * 70,
            "INVOICE RELIABILITY ASSESSMENT",
            "=" * 70,
            "",
            f"Reliability: {assessment.band.value} (Score: {assessment.score}/100)",
            "",
        ]

        if assessment.top_reasons:
            lines.append("Top Factors:")
            for reason in assessment.top_reasons:
                lines.append(f"  • {reason.contribution}")
            lines.append("")

        lines.append("Explanation:")
        lines.append(assessment.explanation)
        lines.append("")

        if assessment.flags:
            lines.append("Flags:")
            for flag in assessment.flags:
                lines.append(f"  • [{flag.severity.value}] {flag.code}")
            lines.append("")

        if assessment.fields_summary:
            lines.append("Fields Summary:")
            for key, value in assessment.fields_summary.items():
                lines.append(f"  {key}: {value}")

        lines.append("")
        lines.append("Assessment complete — human review required.")
        lines.append("=" * 70)

        return "\n".join(lines)


def load_invoice(path: str) -> dict:
    """Load invoice from JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def save_result(bundle: EvidenceBundle, path: str):
    """Save assessment result as JSON."""
    with open(path, "w") as f:
        json.dump(bundle.to_dict(), f, indent=2)


def main(argv=None):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="invoice-check",
        description="Invoice Reliability Assessment Agent (IRAA) — Check invoice reliability for expense approval.",
    )

    parser.add_argument(
        "invoice",
        nargs="?",
        help="Path to invoice JSON file, or sample name (clean, duplicate, unknown_vendor, over_threshold, bad_arithmetic, foreign_currency)",
    )
    parser.add_argument(
        "--list-samples",
        action="store_true",
        help="List available sample invoices and exit.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Save assessment result to this JSON file.",
    )
    parser.add_argument(
        "--sample",
        "-s",
        help="Generate and assess a sample invoice (shorthand for invoice=<sample>).",
    )

    args = parser.parse_args(argv)

    if args.list_samples:
        if _rich:
            console.print("[bold cyan]Available sample invoices:[/bold cyan]")
            for name in list_samples():
                console.print(f"  • {name}")
        else:
            print("Available sample invoices:")
            for name in list_samples():
                print(f"  • {name}")
        return 0

    # Determine which invoice to process
    invoice_data = None
    invoice_name = None

    if args.sample:
        invoice_name = args.sample
        invoice_data = SAMPLE_INVOICES[args.sample]()
    elif args.invoice:
        # Check if it's a sample name or a file
        if args.invoice in SAMPLE_INVOICES:
            invoice_name = args.invoice
            invoice_data = SAMPLE_INVOICES[args.invoice]()
        else:
            # Try to load as file
            try:
                invoice_data = load_invoice(args.invoice)
                invoice_name = Path(args.invoice).stem
            except FileNotFoundError:
                if _rich:
                    console.print(f"[red]Error: Invoice file not found: {args.invoice}[/red]")
                else:
                    print(f"Error: Invoice file not found: {args.invoice}", file=sys.stderr)
                return 1
    else:
        parser.print_help()
        return 0

    if not invoice_data:
        if _rich:
            console.print("[red]Error: No invoice data provided[/red]")
        else:
            print("Error: No invoice data provided", file=sys.stderr)
        return 1

    # Display invoice being assessed
    if _rich:
        console.print(f"[dim]Processing invoice: {invoice_name}[/dim]")
    else:
        print(f"Processing invoice: {invoice_name}")

    # Run assessment
    orchestrator = Orchestrator()
    bundle = orchestrator.assess_invoice(invoice_data)

    # Display result
    if _rich:
        console.print("")
        console.print(format_assessment(bundle))
    else:
        print("")
        print(format_assessment(bundle))

    # Save if requested
    if args.output:
        save_result(bundle, args.output)
        if _rich:
            console.print(f"[green]Result saved to {args.output}[/green]")
        else:
            print(f"Result saved to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
