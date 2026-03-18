"""ClawClaw Soul -- deterministic identity engine for AI agents."""

from clawclaw_soul.engine import compute_modifiers
from clawclaw_soul.params import soul_to_params, timestamp_to_params
from clawclaw_soul.soul import AgentSoul, create_soul, generate

__version__ = "0.2.0"
__all__ = [
    "generate",
    "AgentSoul",
    "create_soul",
    "soul_to_params",
    "timestamp_to_params",
    "compute_modifiers",
]
