"""Output formatters for an AgentDevelopmentPack."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.agent_pack import AgentDevelopmentPack


def pack_to_markdown(pack: "AgentDevelopmentPack") -> str:
    from ..models.agent_pack import PHASE_KEYS, PHASE_TITLES

    lines: list[str] = []
    lines.append("# Agent Development Pack")
    lines.append("")
    lines.append(f"- **Generated:** {pack.created_at}")
    lines.append(f"- **Model:** {pack.model}")
    if pack.mock_mode:
        lines.append("- **Mode:** MOCK (no API key — placeholder content)")
    lines.append("")
    lines.append("## Original Requirement")
    lines.append("")
    lines.append("> " + pack.requirement.replace("\n", "\n> "))
    lines.append("")

    for key in PHASE_KEYS:
        if key not in pack.phases:
            continue
        lines.append(f"## {PHASE_TITLES[key]}")
        lines.append("")
        lines.append(pack.phases[key].strip())
        lines.append("")

    if pack.profiles:
        lines.append("## Extracted Agent Profiles")
        lines.append("")
        for p in pack.profiles:
            lines.append(f"### {p.name or '(unnamed agent)'}")
            lines.append(f"- **Type:** {p.agent_type}")
            lines.append(f"- **Purpose:** {p.purpose}")
            if p.tools:
                lines.append(f"- **Tools:** {', '.join(p.tools)}")
            lines.append("")

    if pack.evaluation_cases:
        lines.append("## Extracted Evaluation Cases")
        lines.append("")
        lines.append("| ID | Category | Severity | Scenario |")
        lines.append("| --- | --- | --- | --- |")
        for e in pack.evaluation_cases:
            scenario = (e.scenario or "").replace("|", "\\|")[:80]
            lines.append(f"| {e.test_id} | {e.category} | {e.severity} | {scenario} |")
        lines.append("")

    return "\n".join(lines)
