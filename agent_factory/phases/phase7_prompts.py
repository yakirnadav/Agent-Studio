"""Phase 7 — Prompt Engineering."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "prompts"
PHASE_TITLE = "Phase 7 — Prompt Engineering"

INSTRUCTION = """\
Produce the actual, copy-pasteable system prompts (or detailed prompt specs) for
each agent, plus key tool/instruction prompts.

For each agent prompt include:
- **Role** statement.
- **Behavioral rules**.
- **Output format contract**.
- **Few-shot guidance** where useful.
- **Refusal / guardrail language**.

Put each prompt in a fenced code block so it can be copied directly.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
