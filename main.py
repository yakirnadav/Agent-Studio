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
    from rich.rule import Rule
    from rich import box
    _rich = True
    _console = Console(highlight=False)
except Exception:
    _rich = False
    _console = None  # type: ignore


# ---- helpers -------------------------------------------------------------

def _rule(msg: str, style: str = "cyan") -> None:
    if _rich:
        _console.print(Rule(f"[bold {style}]{msg}[/bold {style}]", style=style))
    else:
        print(f"\n{'=' * 70}  {msg}  {'=' * 70}", flush=True)


def _print(msg: str) -> None:
    if _rich:
        _console.print(msg)
    else:
        print(msg, flush=True)


def _phase_banner(num: int, title: str, model: str) -> None:
    _rule(f"[{num:02d}/11] {title}", style="yellow")
    _print(f"[dim]  ↳ Sending request to {model}…[/dim]" if _rich
           else f"  → Sending request to {model}…")


def _phase_first_token() -> None:
    _print("[dim]  ↳ First token received — streaming response:[/dim]\n"
           if _rich else "  → First token received — streaming response:\n")


def _phase_done(num: int, title: str, elapsed: float, n_chars: int) -> None:
    _print(
        f"\n[green]  ✓ Phase {num:02d} complete[/green]  "
        f"[dim]{elapsed:.1f}s · {n_chars:,} chars[/dim]"
        if _rich else
        f"\n  ✓ Phase {num:02d} complete  ({elapsed:.1f}s · {n_chars:,} chars)"
    )


def _summary(pack) -> None:
    _rule("PIPELINE COMPLETE", style="green")
    if _rich:
        from rich.table import Table
        t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        t.add_column("Phase", style="cyan")
        t.add_column("Chars", justify="right")
        for key, content in pack.phases.items():
            t.add_row(PHASE_TITLES.get(key, key), f"{len(content):,}")
        _console.print(t)
        _console.print(
            f"[bold green]Profiles extracted:[/bold green] {len(pack.profiles)}   "
            f"[bold green]Eval cases:[/bold green] {len(pack.evaluation_cases)}"
        )
    else:
        print("\n--- Phase summary ---")
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


def _run_streaming(orchestrator: AgentFactoryOrchestrator, requirement: str) -> None:
    """Run all 11 phases with token-level streaming output printed as received."""
    from agent_factory.phases import PHASE_MODULES

    pack = orchestrator._new_pack(requirement)
    model = orchestrator.client.model

    for num in range(1, len(PHASE_MODULES) + 1):
        key = PHASE_NUM_TO_KEY[num]
        title = PHASE_TITLES[key]

        _phase_banner(num, title, model)

        t0 = time.time()
        first = True
        chunks: list[str] = []

        for chunk in orchestrator.stream_phase(num, requirement, pack):
            if first:
                _phase_first_token()
                first = False
            # Print each token immediately so the user sees content as it arrives.
            print(chunk, end="", flush=True)
            chunks.append(chunk)

        elapsed = time.time() - t0
        n_chars = sum(len(c) for c in chunks)
        _phase_done(num, title, elapsed, n_chars)

    orchestrator._extract_structured_artifacts(pack)
    return pack


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    _rule("AGENT FACTORY ORCHESTRATOR")

    if not os.environ.get("ANTHROPIC_API_KEY") and not args.mock:
        _print("[yellow]⚠  No ANTHROPIC_API_KEY — running in MOCK mode.[/yellow]"
               if _rich else "⚠  No ANTHROPIC_API_KEY — running in MOCK mode.")

    client_kwargs: dict = {}
    if args.model:
        client_kwargs["model"] = args.model
    if args.mock:
        client_kwargs["mock"] = True
    client = ClaudeClient(**client_kwargs)
    orchestrator = AgentFactoryOrchestrator(client=client)

    _print(f"[dim]Model:[/dim]       [bold]{client.model}[/bold]" if _rich
           else f"Model: {client.model}")
    _print((f"[dim]Requirement:[/dim] {args.requirement[:120]}"
            + ("…" if len(args.requirement) > 120 else ""))
           if _rich else f"Requirement: {args.requirement[:120]}")

    # ---- single-phase mode -----------------------------------------------
    if args.phase is not None:
        if not (1 <= args.phase <= 11):
            print("--phase must be between 1 and 11", file=sys.stderr)
            return 2
        key = PHASE_NUM_TO_KEY[args.phase]
        title = PHASE_TITLES[key]
        pack = orchestrator._new_pack(args.requirement)

        _phase_banner(args.phase, title, client.model)
        t0 = time.time()
        first = True
        chunks: list[str] = []

        for chunk in orchestrator.stream_phase(args.phase, args.requirement, pack):
            if first:
                _phase_first_token()
                first = False
            print(chunk, end="", flush=True)
            chunks.append(chunk)

        _phase_done(args.phase, title, time.time() - t0, sum(len(c) for c in chunks))

        output = "".join(chunks)
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(output)
            _print(f"[green]Written to {args.output_file}[/green]" if _rich
                   else f"Written to {args.output_file}")
        return 0

    # ---- full pipeline (always streaming) --------------------------------
    _rule("Running all 11 phases — streaming each response live")

    pack = _run_streaming(orchestrator, args.requirement)

    _summary(pack)

    if args.output_file:
        pack.save_report(args.output_file, fmt=args.output_format)
        _print(f"[green]Report written to {args.output_file}[/green]" if _rich
               else f"Report written to {args.output_file}")
    else:
        content = pack.to_json() if args.output_format == "json" else pack.to_markdown()
        print("\n" + content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
