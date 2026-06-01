"""The main AgentFactoryOrchestrator.

Runs the 11-phase factory pipeline against a cached system prompt, threading the
output of each phase into the next, and produces a complete AgentDevelopmentPack.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Iterator, Optional

from .models import (
    PHASE_KEYS,
    PHASE_NUM_TO_KEY,
    PHASE_TITLES,
    AgentDevelopmentPack,
    AgentProfile,
    EvaluationCase,
)
from .phases import PHASE_MODULES
from .prompts import SYSTEM_PROMPT
from .phases._common import build_user_message
from .utils import ClaudeClient

ProgressCallback = Callable[[int, str, str], None]


class AgentFactoryOrchestrator:
    """Drive a requirement through all 11 factory phases.

    Parameters
    ----------
    client:
        A configured :class:`ClaudeClient`. If omitted, one is created (which
        auto-detects mock mode when no ``ANTHROPIC_API_KEY`` is present).
    """

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        self.client = client or ClaudeClient()
        self.system_prompt = SYSTEM_PROMPT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_full(
        self,
        requirement: str,
        progress: Optional[ProgressCallback] = None,
    ) -> AgentDevelopmentPack:
        """Run all 11 phases sequentially and return the completed pack."""
        pack = self._new_pack(requirement)

        for num in range(1, len(PHASE_MODULES) + 1):
            key = PHASE_NUM_TO_KEY[num]
            output = self._run_phase_num(num, requirement, pack)
            pack.set_phase(key, output)
            if progress is not None:
                progress(num, PHASE_TITLES[key], output)

        self._extract_structured_artifacts(pack)
        return pack

    def run_phase(
        self,
        phase_num: int,
        requirement: str,
        pack: Optional[AgentDevelopmentPack] = None,
    ) -> tuple[str, AgentDevelopmentPack]:
        """Run a single phase by number (1-11).

        Returns the phase output text and the pack it was written into. Any prior
        phases already present on ``pack`` are passed as context.
        """
        self._validate_phase_num(phase_num)
        if pack is None:
            pack = self._new_pack(requirement)

        output = self._run_phase_num(phase_num, requirement, pack)
        pack.set_phase(PHASE_NUM_TO_KEY[phase_num], output)
        self._extract_structured_artifacts(pack)
        return output, pack

    def stream_phase(
        self,
        phase_num: int,
        requirement: str,
        pack: Optional[AgentDevelopmentPack] = None,
    ) -> Iterator[str]:
        """Stream a single phase's output text chunk-by-chunk.

        The accumulated text is written back onto ``pack`` when the stream ends.
        Pass a pack to thread prior-phase context in.
        """
        self._validate_phase_num(phase_num)
        if pack is None:
            pack = self._new_pack(requirement)

        module = PHASE_MODULES[phase_num - 1]
        key = PHASE_NUM_TO_KEY[phase_num]
        user_message = build_user_message(
            PHASE_TITLES[key],
            getattr(module, "INSTRUCTION", ""),
            requirement,
            {"phases": dict(pack.phases)},
        )

        chunks: list[str] = []
        for chunk in self.client.stream(self.system_prompt, user_message, use_cache=True):
            chunks.append(chunk)
            yield chunk
        pack.set_phase(key, "".join(chunks).strip())

    def run_full_streaming(
        self,
        requirement: str,
        on_chunk: Optional[Callable[[int, str], None]] = None,
    ) -> AgentDevelopmentPack:
        """Run all phases, streaming each. ``on_chunk(phase_num, text)`` fires per chunk."""
        pack = self._new_pack(requirement)
        for num in range(1, len(PHASE_MODULES) + 1):
            for chunk in self.stream_phase(num, requirement, pack):
                if on_chunk is not None:
                    on_chunk(num, chunk)
        self._extract_structured_artifacts(pack)
        return pack

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _new_pack(self, requirement: str) -> AgentDevelopmentPack:
        return AgentDevelopmentPack(
            requirement=requirement,
            model=self.client.model,
            mock_mode=self.client.mock,
        )

    def _run_phase_num(
        self, phase_num: int, requirement: str, pack: AgentDevelopmentPack
    ) -> str:
        module = PHASE_MODULES[phase_num - 1]
        context: dict[str, Any] = {"phases": dict(pack.phases)}
        return module.run_phase(requirement, context, self.client)

    @staticmethod
    def _validate_phase_num(phase_num: int) -> None:
        if not (1 <= phase_num <= len(PHASE_MODULES)):
            raise ValueError(
                f"phase_num must be between 1 and {len(PHASE_MODULES)}, got {phase_num}"
            )

    # ---- lightweight structured extraction ----------------------------

    def _extract_structured_artifacts(self, pack: AgentDevelopmentPack) -> None:
        """Best-effort parse of profiles and eval cases from phase text.

        This is intentionally tolerant: it never raises, and only populates
        artifacts it can confidently recover from the markdown.
        """
        pack.profiles = _extract_profiles(pack.phases.get("characterization", ""))
        pack.evaluation_cases = _extract_eval_cases(pack.phases.get("evaluation", ""))


# ---- parsing helpers --------------------------------------------------

_AGENT_HEADING = re.compile(r"^#{2,4}\s+(?:Agent[:\-\s]*)?(.+?)\s*$", re.MULTILINE)


def _extract_profiles(text: str) -> list[AgentProfile]:
    if not text.strip():
        return []
    profiles: list[AgentProfile] = []
    headings = list(_AGENT_HEADING.finditer(text))
    for i, m in enumerate(headings):
        name = m.group(1).strip()
        # Skip obvious non-agent section headers.
        if name.lower() in {"agent characterization", "overview", "summary"}:
            continue
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end]
        purpose = _field(body, "purpose") or _first_sentence(body)
        agent_type = (_field(body, "agent type") or _field(body, "type") or "single").lower()
        agent_type = next(
            (t for t in ("orchestrator", "specialist", "tool", "single") if t in agent_type),
            "single",
        )
        profiles.append(
            AgentProfile(
                name=name[:80],
                purpose=purpose[:300],
                agent_type=agent_type,
                tools=_field_list(body, "tools"),
                autonomy_level=_autonomy(body),
            )
        )
    return profiles


def _extract_eval_cases(text: str) -> list[EvaluationCase]:
    """Parse a markdown table whose first column looks like an ID."""
    if not text.strip():
        return []
    cases: list[EvaluationCase] = []
    rows = [ln for ln in text.splitlines() if ln.count("|") >= 4]
    for ln in rows:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        first = cells[0]
        # Skip header/separator rows.
        if not first or set(first) <= set("-: ") or first.lower() in {"id", "test id"}:
            continue
        # Heuristic: an ID cell is short and not a full sentence.
        if len(first) > 24 or " " in first.strip():
            continue
        category = cells[1].lower() if len(cells) > 1 else "functional"
        category = next(
            (c for c in ("functional", "safety", "robustness", "performance", "edge_case", "edge")
             if c in category),
            "functional",
        )
        category = "edge_case" if category == "edge" else category
        scenario = cells[2] if len(cells) > 2 else ""
        inp = cells[3] if len(cells) > 3 else ""
        expected = cells[4] if len(cells) > 4 else ""
        scoring = cells[5] if len(cells) > 5 else ""
        severity_raw = (cells[-1] if cells else "").lower()
        severity = next(
            (s for s in ("critical", "high", "medium", "low") if s in severity_raw),
            "medium",
        )
        cases.append(
            EvaluationCase(
                test_id=first,
                category=category,
                scenario=scenario,
                input=inp,
                expected_behavior=expected,
                scoring_criteria=[s.strip() for s in re.split(r"[;,]", scoring) if s.strip()],
                severity=severity,
            )
        )
    return cases


def _field(body: str, label: str) -> str:
    m = re.search(
        rf"[*\-\s]*\**\s*{re.escape(label)}\s*\**\s*[:\-]\s*\**\s*(.+)",
        body,
        re.IGNORECASE,
    )
    if not m:
        return ""
    # Strip any trailing bold markers left over from the label/value.
    return m.group(1).strip().strip("*").strip()


def _field_list(body: str, label: str) -> list[str]:
    raw = _field(body, label)
    if not raw:
        return []
    return [t.strip(" `") for t in re.split(r"[,;]", raw) if t.strip(" `")]


def _autonomy(body: str) -> str:
    val = _field(body, "autonomy level") or _field(body, "autonomy")
    val = val.lower()
    for level in ("semi-autonomous", "autonomous", "supervised"):
        if level in val:
            return level
    return "supervised"


def _first_sentence(body: str) -> str:
    cleaned = re.sub(r"[#*`>\-]", " ", body).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.split(". ")[0][:300] if cleaned else ""
