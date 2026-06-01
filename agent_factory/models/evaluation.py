"""Evaluation case data model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationCase:
    """A single test/eval case for an agent."""

    test_id: str = ""
    category: str = ""  # e.g. "happy_path", "edge_case", "adversarial", "safety"
    scenario: str = ""
    input: str = ""
    expected_behavior: str = ""
    scoring_criteria: list[str] = field(default_factory=list)
    severity: str = "medium"  # low | medium | high | critical

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "category": self.category,
            "scenario": self.scenario,
            "input": self.input,
            "expected_behavior": self.expected_behavior,
            "scoring_criteria": self.scoring_criteria,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationCase":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
