#!/usr/bin/env python3
"""CLI entry point for the Agent Factory Orchestrator."""
from __future__ import annotations

import argparse
import os
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from agent_factory import AgentFactoryOrchestrator, ClaudeClient
from agent_factory.models import PHASE_NUM_TO_KEY, PHASE_TITLES

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.text import Text
    from rich.spinner import Spinner
    from rich.live import Live
    from rich import box
    _rich = True
    _console = Console()
except Exception:
    _rich = False
    _console = None  # type: ignore


# ---- pretty-print helpers ------------------------------------------------

def _header(msg: str) -> None:
    if _rich:
        _console.print(Rule(f"[bold cyan]{msg}[/bold cyan]", style="cyan"))
    else:
        print(f"\n{'=' * 70}\n  {msg}\n{'=' * 70}")


def _phase_start(num: int, title: str) -> None:
    if _rich:
        _console.print(
            f"\n[bold yellow]▶ [{num:02d}/11][/bold yellow] [bold]{title}[/bold]  "
            f"[dim]calling claude-opus-4-8…[/dim]"
        )
    else:
        print(f"\n▶ [{num:02d}/11] {title}  (calling model…)", flush=True)


def _phase_done(num: int, title: str, elapsed: float, n_chars: int) -> None:
    if _rich:
        _console.print(
            f"  [green]✓[/green] [bold]{title}[/bold]  "
            f"[dim]{elapsed:.1f}s · {n_chars:,} chars[/dim]"
        )
    else:
        print(f"  ✓ {title}  ({elapsed:.1f}s · {n_chars:,} chars)", flush=True)


def _phase_output(num: int, title: str, text: str) -> None:
    if _rich:
        _console.print(
            Panel(
                text.strip()[:3000] + ("\n…[truncated]" if len(text) > 3000 else ""),
                title=f"[cyan]{title}[/cyan]",
                border_style="dim",
                expand=False,
            )
        )
    else:
        sep = "-" * 60
        print(f"\n{sep}\n{title}\n{sep}")
        print(text.strip()[:3000])
        if len(text) > 3000:
            print("…[truncated]")


def _summary(pack) -> None:
    if _rich:
        from rich.table import Table
        t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        t.add_column("Phase", style="cyan")
        t.add_column("Chars", justify="right")
        for key, content in pack.phases.items():
            title = PHASE_TITLES.get(key, key)
            t.add_row(title, f"{len(content):,}")
        _console.print("\n")
        _console.print(t)
        _console.print(
            f"[bold green]✓ Done.[/bold green]  "
            f"Profiles extracted: [bold]{len(pack.profiles)}[/bold]  "
            f"Eval cases: [bold]{len(pack.evaluation_cases)}[/bold]"
        )
    else:
        print("\n--- Summary ---")
        for key, content in pack.phases.items():
            print(f"  {PHASE_TITLES.get(key, key)}: {len(content):,} chars")
        print(f"Profiles: {len(pack.profiles)}  Eval cases: {len(pack.evaluation_cases)}")


# ---- CLI -----------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agent-factory",
        description="Turn a requirement into a complete Agent Development Pack.",
    )
    p.add_argument("requirement", help="The raw requirement for the new AI capability.")
    p.add_argument(
        "--output-format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    p.add_argument("--output-file", help="Write the report to this path instead of stdout.")
    p.add_argument(
        "--phase",
        type=int,
        metavar="N",
        help="Run only phase N (1-11) instead of the full pipeline.",
    )
    p.add_argument("--model", help="Override the model id (default: claude-opus-4-8).")
    p.add_argument(
        "--mock",
        action="store_true",
        help="Force mock mode (no API calls). Auto-enabled when no API key is set.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    _header("AGENT FACTORY ORCHESTRATOR")

    if not os.environ.get("ANTHROPIC_API_KEY") and not args.mock:
        msg = "No ANTHROPIC_API_KEY — running in MOCK mode (placeholder output)."
        if _rich:
            _console.print(f"[yellow]⚠ {msg}[/yellow]")
        else:
            print(f"⚠ {msg}", file=sys.stderr)

    client_kwargs: dict = {}
    if args.model:
        client_kwargs["model"] = args.model
    if args.mock:
        client_kwargs["mock"] = True
    client = ClaudeClient(**client_kwargs)
    orchestrator = AgentFactoryOrchestrator(client=client)

    if _rich:
        _console.print(f"[dim]Model:[/dim] [bold]{client.model}[/bold]")
        _console.print(
            f"[dim]Requirement:[/dim] {args.requirement[:120]}"
            + ("…" if len(args.requirement) > 120 else "")
        )
    else:
        print(f"Model: {client.model}")
        print(f"Requirement: {args.requirement[:120]}")

    # ---- single-phase mode -----------------------------------------------
    if args.phase is not None:
        if not (1 <= args.phase <= 11):
            print("--phase must be between 1 and 11", file=sys.stderr)
            return 2
        title = PHASE_TITLES[PHASE_NUM_TO_KEY[args.phase]]
        _phase_start(args.phase, title)
        t0 = time.time()
        output, _ = orchestrator.run_phase(args.phase, args.requirement)
        _phase_done(args.phase, title, time.time() - t0, len(output))
        _phase_output(args.phase, title, output)
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Written to {args.output_file}")
        return 0

    # ---- full pipeline with verbose per-phase logging --------------------
    _header(f"Running all 11 phases")
    timings: dict[int, float] = {}

    def progress(num: int, title: str, output: str) -> None:
        elapsed = time.time() - timings.get(num, time.time())
        _phase_done(num, title, elapsed, len(output))
        _phase_output(num, title, output)

    # Monkey-patch _run_phase_num to capture start times and print header.
    original_run = orchestrator._run_phase_num

    def _timed_run(phase_num: int, requirement: str, pack) -> str:
        title = PHASE_TITLES[PHASE_NUM_TO_KEY[phase_num]]
        _phase_start(phase_num, title)
        timings[phase_num] = time.time()
        result = original_run(phase_num, requirement, pack)
        return result

    orchestrator._run_phase_num = _timed_run  # type: ignore[method-assign]

    pack = orchestrator.run_full(args.requirement, progress=progress)

    _summary(pack)

    if args.output_file:
        pack.save_report(args.output_file, fmt=args.output_format)
        msg = f"Report written to {args.output_file}"
        if _rich:
            _console.print(f"[green]{msg}[/green]")
        else:
            print(msg)
    else:
        content = pack.to_json() if args.output_format == "json" else pack.to_markdown()
        print(content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
