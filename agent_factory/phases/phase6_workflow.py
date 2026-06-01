"""Phase 6 — Workflow & Execution Design."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "workflow"
PHASE_TITLE = "Phase 6 — Workflow & Execution Design"

INSTRUCTION = """\
Specify the runtime execution.

Produce:
- **Happy-path workflow** as numbered steps.
- **Control flow**: branching, looping, retry, timeout, and back-off policies.
- **Human-in-the-loop checkpoints** and approval gates.
- **Streaming vs batch** behavior.
- **End-to-end sequence** for the primary scenarios (step / actor / action /
  output).
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
