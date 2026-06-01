"""Phase 3 — Agent Characterization."""
from __future__ import annotations

from typing import Any

from ._common import run_generic_phase

PHASE_KEY = "characterization"
PHASE_TITLE = "Phase 3 — Agent Characterization"

INSTRUCTION = """\
For each agent in the chosen architecture, define a precise profile.

For every agent, provide:
- **Name** and **purpose**.
- **Agent type**: single / specialist / orchestrator / tool.
- **Target users** and the **scenarios it owns**.
- **Tools / integrations** required.
- **Capabilities** and **constraints**.
- **Personality / tone** and **autonomy level** (supervised / semi-autonomous /
  autonomous).
- A high-level **input/output contract**.

Present one clearly delimited subsection per agent.
"""


def run_phase(requirement_brief: str, context: dict[str, Any], client) -> str:
    return run_generic_phase(
        PHASE_TITLE, INSTRUCTION, requirement_brief, context, client
    )
