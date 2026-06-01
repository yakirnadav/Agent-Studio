"""Phase 1 — Requirement Intake."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "intake"
PHASE_TITLE = "Phase 1 — Requirement Intake"

INSTRUCTION = """\
Clarify and normalize the raw requirement into a precise Requirement Brief.

Produce:
- **Core problem** and the business/user goal it serves.
- **Success metrics** (quantified where possible).
- **In scope** vs **Out of scope** (explicit lists).
- **Primary users & stakeholders**.
- **Key use-case scenarios** (3-6 concrete scenarios).
- **Hard constraints**: latency, cost, compliance, data residency, integrations.
- **Explicit assumptions** you are making to proceed.
- **Top open questions** (ranked).

End with a tight, self-contained "Requirement Brief" block that later phases can
anchor to.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
