"""ClawClaw Soul -- deterministic identity engine for AI agents."""

from clawclaw_soul.compatibility import compatibility
from clawclaw_soul.engine import compute_modifiers
from clawclaw_soul.params import soul_to_params, timestamp_to_params
from clawclaw_soul.soul import AgentSoul, create_soul, generate, generate_soul_md, verify_soul_md

__version__ = "0.3.0"
__all__ = [
    "generate",
    "AgentSoul",
    "create_soul",
    "soul_to_params",
    "timestamp_to_params",
    "generate_soul_md",
    "verify_soul_md",
    "compute_modifiers",
    "compatibility",
]
