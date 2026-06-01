"""Phase 11 — Readiness Assessment."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "readiness"
PHASE_TITLE = "Phase 11 — Readiness Assessment"

INSTRUCTION = """\
Give a go/no-go readiness verdict.

Produce:
- **Verdict**: GO / NO-GO / GO-WITH-CONDITIONS, one line, up front.
- **Readiness scorecard** table scoring 0-5 across: functionality, evaluation
  coverage, safety, ops/observability, cost, documentation — with notes.
- **Blocking gaps** (must fix before launch).
- **Recommended pre-launch actions** (ranked).
- **Rollout plan**: shadow -> canary -> GA, with gating criteria per stage.
- **Post-launch monitoring & KPIs** to watch.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
