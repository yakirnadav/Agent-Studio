"""Agent contract data model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContract:
    """The input/output contract an agent must honor."""

    agent_name: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    error_handling: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "error_handling": self.error_handling,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentContract":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
