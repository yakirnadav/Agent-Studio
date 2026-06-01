"""Agent profile data model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentProfile:
    """Describes a single agent's identity and capabilities."""

    name: str = ""
    purpose: str = ""
    agent_type: str = ""  # e.g. "single", "specialist", "orchestrator"
    target_users: list[str] = field(default_factory=list)
    scenarios: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    knowledge_sources: list[str] = field(default_factory=list)
    autonomy_level: str = ""  # e.g. "assistive", "supervised", "autonomous"
    persona: str = ""
    constraints: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "agent_type": self.agent_type,
            "target_users": self.target_users,
            "scenarios": self.scenarios,
            "tools": self.tools,
            "knowledge_sources": self.knowledge_sources,
            "autonomy_level": self.autonomy_level,
            "persona": self.persona,
            "constraints": self.constraints,
            "success_metrics": self.success_metrics,
            "raw": self.raw,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentProfile":
        known = {f for f in cls.__dataclass_fields__ if f != "raw"}
        kwargs = {k: v for k, v in data.items() if k in known}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(raw=extra, **kwargs)
