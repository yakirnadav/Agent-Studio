"""Phase 8 — Evaluation Design."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "evaluation"
PHASE_TITLE = "Phase 8 — Evaluation Design"

INSTRUCTION = """\
Define how success is measured.

Produce:
- **Metrics**: quality, accuracy, safety, latency, cost, satisfaction (with
  targets).
- **Evaluation harness** approach: LLM-as-judge, rubric grading, golden sets.
- A concrete **evaluation case set** — present as a table with columns:
  ID | Category | Scenario | Input | Expected behavior | Scoring criteria | Severity.
  Categories: functional / safety / robustness / performance / edge_case.
  Provide at least 8 representative cases spanning multiple categories.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
