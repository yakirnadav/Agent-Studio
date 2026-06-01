"""Phase 9 — Testing Strategy."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "testing"
PHASE_TITLE = "Phase 9 — Testing Strategy"

INSTRUCTION = """\
Define the testing pyramid for the system and the CI gating strategy.

Produce:
- **Unit tests** for tools/functions.
- **Integration tests** for agent + tool.
- **End-to-end scenario tests** tied to Phase 8 evaluation cases.
- **Adversarial / red-team tests**.
- **Regression suite** and how it grows.
- **Load / performance tests**.
- **CI gating**: what must pass before merge/deploy, and pass thresholds.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
