#!/usr/bin/env python3
"""Worked example: run the full Agent Factory pipeline on a sample request.

Run from the repo root:

    python examples/run_example.py

Works without an API key (mock mode). Set ANTHROPIC_API_KEY for a real run.
"""
from __future__ import annotations

import os
import sys

# Make the package importable when run directly from the repo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from agent_factory import AgentFactoryOrchestrator, ClaudeClient
from examples.sample_requests import DEFAULT_REQUEST


def main() -> int:
    requirement = DEFAULT_REQUEST
    print("=" * 70)
    print("AGENT FACTORY ORCHESTRATOR — EXAMPLE RUN")
    print("=" * 70)
    print(f"\nRequirement:\n{requirement}\n")

    client = ClaudeClient()
    if client.mock:
        print("(No ANTHROPIC_API_KEY — running in MOCK mode with placeholder output.)\n")

    orchestrator = AgentFactoryOrchestrator(client=client)

    def progress(num: int, title: str, output: str) -> None:
        preview = output.strip().splitlines()[0][:90] if output.strip() else ""
        print(f"  [{num:>2}/11] {title}\n         {preview}")

    print("Running all 11 phases...\n")
    pack = orchestrator.run_full(requirement, progress=progress)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Phases completed : {len(pack.phases)}")
    print(f"Agent profiles   : {len(pack.profiles)}")
    print(f"Evaluation cases : {len(pack.evaluation_cases)}")

    out_path = os.path.join(os.path.dirname(__file__), "example_pack.md")
    pack.save_report(out_path, fmt="markdown")
    print(f"\nFull markdown report written to:\n  {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
