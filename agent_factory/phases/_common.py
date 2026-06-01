"""Shared helpers for phase modules."""
from __future__ import annotations

from typing import Any

from ..prompts import SYSTEM_PROMPT


def build_user_message(
    phase_title: str,
    phase_instruction: str,
    requirement_brief: str,
    context: dict[str, Any],
) -> str:
    """Assemble the per-phase user message.

    The large orchestrator role lives in the cached system prompt; here we add
    only the specific phase instruction plus the requirement and the outputs of
    all prior phases so each phase builds on the previous ones.
    """
    parts: list[str] = []
    parts.append(f"# CURRENT PHASE: {phase_title}")
    parts.append("")
    parts.append(phase_instruction.strip())
    parts.append("")
    parts.append("## ORIGINAL REQUIREMENT")
    parts.append(requirement_brief.strip())
    parts.append("")

    prior = context.get("phases", {})
    if prior:
        parts.append("## CONTEXT FROM PRIOR PHASES")
        for key, content in prior.items():
            parts.append(f"### {key}")
            parts.append(str(content).strip())
            parts.append("")
    else:
        parts.append("## CONTEXT FROM PRIOR PHASES")
        parts.append("(none — this is the first phase)")
        parts.append("")

    parts.append(
        "Produce a thorough, structured, production-ready response for THIS phase "
        "only. Use clear markdown headings, tables, and lists where helpful."
    )
    return "\n".join(parts)


def run_generic_phase(
    phase_title: str,
    phase_instruction: str,
    requirement_brief: str,
    context: dict[str, Any],
    client,
) -> str:
    """Run one phase against the cached system prompt and return its text."""
    user_message = build_user_message(
        phase_title, phase_instruction, requirement_brief, context
    )
    return client.generate(SYSTEM_PROMPT, user_message, use_cache=True)
