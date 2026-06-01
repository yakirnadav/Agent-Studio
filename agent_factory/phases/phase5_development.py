"""Phase 5 — Agent Development Plan."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "development"
PHASE_TITLE = "Phase 5 — Agent Development Plan"

INSTRUCTION = """\
Lay out how to actually build the system.

Produce:
- **Tech stack & frameworks**.
- **Model selection per agent** and the rationale.
- **Tool / function implementations** (signatures and responsibilities).
- **Memory & retrieval** approach.
- **State management** and **deployment surface**.
- **Reusable components** to leverage.
- A **phased build plan** with milestones and rough effort estimates.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
