"""Phase 10 — Risks & Guardrails."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "risks"
PHASE_TITLE = "Phase 10 — Risks & Guardrails"

INSTRUCTION = """\
Enumerate risks and concrete guardrails.

Produce:
- A **risk register** table: Risk | Category | Likelihood | Impact | Mitigation /
  Guardrail. Cover safety, security (prompt injection, data exfiltration, tool
  misuse), reliability, cost runaway, hallucination, bias, and compliance.
- **Input/output filtering**, allow/deny lists, and rate limits.
- **Escalation paths** and kill-switch criteria.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
