"""Phase 4 — Multi-Agent Orchestration Design."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "orchestration"
PHASE_TITLE = "Phase 4 — Multi-Agent Orchestration Design"

INSTRUCTION = """\
Define how the agents coordinate. If the architecture is a single agent, say so
explicitly and describe the (trivial) control loop instead.

Produce:
- **Orchestration pattern**: single / supervisor / pipeline / blackboard /
  hierarchical / market — and why.
- **Message & handoff contracts** between agents.
- **Routing logic** (how work is dispatched).
- **Shared state & memory** model.
- **Conflict resolution** and **termination conditions**.
- A sequence/flow description for the primary scenario.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
