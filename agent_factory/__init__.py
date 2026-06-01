"""Agent Factory Orchestrator — a meta-AI system that turns a requirement for a
new AI capability into a complete Agent Development Pack via an 11-phase pipeline.
"""
from .orchestrator import AgentFactoryOrchestrator
from .prompts import SYSTEM_PROMPT
from .models import (
    PHASE_KEYS,
    PHASE_NUM_TO_KEY,
    PHASE_TITLES,
    AgentContract,
    AgentDevelopmentPack,
    AgentProfile,
    EvaluationCase,
)
from .utils import DEFAULT_MODEL, ClaudeClient

__version__ = "0.1.0"

__all__ = [
    "AgentFactoryOrchestrator",
    "ClaudeClient",
    "AgentDevelopmentPack",
    "AgentProfile",
    "AgentContract",
    "EvaluationCase",
    "SYSTEM_PROMPT",
    "DEFAULT_MODEL",
    "PHASE_KEYS",
    "PHASE_TITLES",
    "PHASE_NUM_TO_KEY",
]
