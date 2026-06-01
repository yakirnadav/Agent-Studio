#!/usr/bin/env python3
"""CLI entry point for the Agent Factory Orchestrator.

Examples
--------
    python main.py "Build an AI customer support agent for an e-commerce platform"
    python main.py "..." --output-format json --output-file pack.json
    python main.py "..." --phase 2
    python main.py "..." --stream
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass

from agent_factory import AgentFactoryOrchestrator, ClaudeClient
from agent_factory.models import PHASE_NUM_TO_KEY, PHASE_TITLES

try:
    from rich.console import Console

    _console = Console()

    def _info(msg: str) -> None:
        _console.print(msg)
except Exception:  # pragma: no cover - rich is optional
    def _info(msg: str) -> None:
        print(msg, file=sys.stderr)


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
    p.add_argument(
        "--stream",
        action="store_true",
        help="Stream output as it is generated.",
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

    if not os.environ.get("ANTHROPIC_API_KEY") and not args.mock:
        _info(
            "[yellow]No ANTHROPIC_API_KEY found — running in MOCK mode "
            "(placeholder output).[/yellow]"
            if "rich" in sys.modules
            else "No ANTHROPIC_API_KEY found — running in MOCK mode (placeholder output)."
        )

    client_kwargs: dict = {}
    if args.model:
        client_kwargs["model"] = args.model
    if args.mock:
        client_kwargs["mock"] = True
    client = ClaudeClient(**client_kwargs)
    orchestrator = AgentFactoryOrchestrator(client=client)

    # Single-phase mode.
    if args.phase is not None:
        if not (1 <= args.phase <= 11):
            print("--phase must be between 1 and 11", file=sys.stderr)
            return 2
        title = PHASE_TITLES[PHASE_NUM_TO_KEY[args.phase]]
        _info(f"Running {title}...")
        if args.stream:
            for chunk in orchestrator.stream_phase(args.phase, args.requirement):
                print(chunk, end="", flush=True)
            print()
            return 0
        output, _ = orchestrator.run_phase(args.phase, args.requirement)
        _write(output, args.output_file)
        return 0

    # Full pipeline.
    if args.stream:
        current = {"n": 0}

        def on_chunk(num: int, text: str) -> None:
            if num != current["n"]:
                current["n"] = num
                title = PHASE_TITLES[PHASE_NUM_TO_KEY[num]]
                print(f"\n\n===== {title} =====\n", flush=True)
            print(text, end="", flush=True)

        pack = orchestrator.run_full_streaming(args.requirement, on_chunk=on_chunk)
        print()
    else:
        def progress(num: int, title: str, _output: str) -> None:
            _info(f"[green]✓[/green] {title}" if "rich" in sys.modules else f"[done] {title}")

        pack = orchestrator.run_full(args.requirement, progress=progress)

    content = pack.to_json() if args.output_format == "json" else pack.to_markdown()
    if args.output_file:
        pack.save_report(args.output_file, fmt=args.output_format)
        _info(f"Report written to {args.output_file}")
    elif not args.stream:
        print(content)
    return 0


def _write(content: str, output_file: str | None) -> None:
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        _info(f"Written to {output_file}")
    else:
        print(content)


if __name__ == "__main__":
    raise SystemExit(main())
