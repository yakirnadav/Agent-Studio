"""The combined Agent Development Pack produced by the factory."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .agent_profile import AgentProfile
from .contracts import AgentContract
from .evaluation import EvaluationCase

# Ordered phase keys used throughout the pack.
PHASE_KEYS = [
    "intake",          # 1
    "architecture",    # 2
    "characterization",# 3
    "orchestration",   # 4
    "development",     # 5
    "workflow",        # 6
    "prompts",         # 7
    "evaluation",      # 8
    "testing",         # 9
    "risks",           # 10
    "readiness",       # 11
]

PHASE_TITLES = {
    "intake": "Phase 1 — Requirement Intake",
    "architecture": "Phase 2 — Architecture Decision",
    "characterization": "Phase 3 — Agent Characterization",
    "orchestration": "Phase 4 — Multi-Agent Orchestration",
    "development": "Phase 5 — Agent Development Plan",
    "workflow": "Phase 6 — Workflow & Execution Design",
    "prompts": "Phase 7 — Prompt Engineering",
    "evaluation": "Phase 8 — Evaluation Design",
    "testing": "Phase 9 — Testing Strategy",
    "risks": "Phase 10 — Risks & Guardrails",
    "readiness": "Phase 11 — Readiness Assessment",
}

PHASE_NUM_TO_KEY = {i + 1: k for i, k in enumerate(PHASE_KEYS)}


@dataclass
class AgentDevelopmentPack:
    """Complete output of an end-to-end factory run."""

    requirement: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model: str = ""
    mock_mode: bool = False

    # Per-phase free-form outputs (markdown/text from Claude).
    phases: dict[str, str] = field(default_factory=dict)

    # Structured artifacts extracted along the way.
    profiles: list[AgentProfile] = field(default_factory=list)
    contracts: list[AgentContract] = field(default_factory=list)
    evaluation_cases: list[EvaluationCase] = field(default_factory=list)

    def set_phase(self, key: str, content: str) -> None:
        if key not in PHASE_KEYS:
            raise ValueError(f"Unknown phase key: {key!r}")
        self.phases[key] = content

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement": self.requirement,
            "created_at": self.created_at,
            "model": self.model,
            "mock_mode": self.mock_mode,
            "phases": self.phases,
            "profiles": [p.to_dict() for p in self.profiles],
            "contracts": [c.to_dict() for c in self.contracts],
            "evaluation_cases": [e.to_dict() for e in self.evaluation_cases],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentDevelopmentPack":
        pack = cls(
            requirement=data.get("requirement", ""),
            created_at=data.get("created_at", ""),
            model=data.get("model", ""),
            mock_mode=data.get("mock_mode", False),
            phases=data.get("phases", {}),
        )
        pack.profiles = [AgentProfile.from_dict(d) for d in data.get("profiles", [])]
        pack.contracts = [AgentContract.from_dict(d) for d in data.get("contracts", [])]
        pack.evaluation_cases = [
            EvaluationCase.from_dict(d) for d in data.get("evaluation_cases", [])
        ]
        return pack

    # ---- formatting / persistence -------------------------------------

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        from ..utils.formatters import pack_to_markdown

        return pack_to_markdown(self)

    def save_report(self, path: str, fmt: str = "markdown") -> str:
        content = self.to_json() if fmt == "json" else self.to_markdown()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
