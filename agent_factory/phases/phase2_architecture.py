"""Phase 2 — Architecture Decision."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "architecture"
PHASE_TITLE = "Phase 2 — Architecture Decision"

INSTRUCTION = """\
Decide the architecture: single agent, multiple specialized agents, or a
coordinated multi-agent system.

Produce:
- **Decision** with a clear one-line verdict.
- **Justification** mapped back to the Requirement Brief.
- **High-level architecture**: major components, data flows, external systems/tools.
- **Component table**: component -> responsibility.
- **Trade-offs** and **rejected alternatives** with reasons.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
