"""The 11 sequential factory phases.

Each module exposes ``run_phase(requirement_brief, context, client)`` and a
``PHASE_KEY`` matching the keys in ``models.agent_pack.PHASE_KEYS``.
"""
from . import (
    phase1_intake,
    phase2_architecture,
    phase3_characterization,
    phase4_orchestration,
    phase5_development,
    phase6_workflow,
    phase7_prompts,
    phase8_evaluation,
    phase9_testing,
    phase10_risks,
    phase11_readiness,
)

# Ordered list of phase modules, indexed by phase number - 1.
PHASE_MODULES = [
    phase1_intake,
    phase2_architecture,
    phase3_characterization,
    phase4_orchestration,
    phase5_development,
    phase6_workflow,
    phase7_prompts,
    phase8_evaluation,
    phase9_testing,
    phase10_risks,
    phase11_readiness,
]

__all__ = ["PHASE_MODULES"]
