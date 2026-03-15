"""Core engine: agent_id + timestamp → personality modifiers.

v1: 5 flat modifiers (verbosity, agreeableness, creativity, risk_tolerance, proactivity)
v2: 9 graha dimensions from Digital Soul (authority, empathy, execution, analysis,
    wisdom, aesthetics, restriction, innovation, compression)
"""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timedelta, timezone

from agent_soul.dasha import compute_dasha_timeline, find_active_period
from agent_soul.ephemeris import get_planet_positions
from agent_soul.tables import DIGNITY_SCORES, get_dignity, get_sign, get_sign_degree
from agent_soul.transit import compute_transit_scores

MODIFIER_NAMES = ["verbosity", "agreeableness", "creativity", "risk_tolerance", "proactivity"]

# v2: 9 graha dimension names
DIMENSION_NAMES = [
    "authority", "empathy", "execution", "analysis",
    "wisdom", "aesthetics", "restriction", "innovation", "compression",
]

# Planet → dimension mapping (each planet governs one dimension)
PLANET_TO_DIMENSION = {
    "Sun": "authority",
    "Moon": "empathy",
    "Mars": "execution",
    "Mercury": "analysis",
    "Jupiter": "wisdom",
    "Venus": "aesthetics",
    "Saturn": "restriction",
    "Rahu": "innovation",
    "Ketu": "compression",
}

# Dasha overlay v2: how each mahadasha lord shifts ALL 9 dimensions.
# Primary dimension gets the strongest boost; related dimensions get secondary effects.
DASHA_OVERLAY_V2: dict[str, dict[str, float]] = {
    "Sun": {
        "authority": 0.35, "empathy": -0.1, "execution": 0.1,
        "analysis": 0.0, "wisdom": 0.1, "aesthetics": 0.0,
        "restriction": -0.1, "innovation": 0.0, "compression": 0.0,
    },
    "Moon": {
        "authority": 0.0, "empathy": 0.35, "execution": -0.1,
        "analysis": 0.1, "wisdom": 0.15, "aesthetics": 0.15,
        "restriction": -0.1, "innovation": 0.0, "compression": 0.0,
    },
    "Mars": {
        "authority": 0.1, "empathy": -0.2, "execution": 0.35,
        "analysis": -0.1, "wisdom": 0.0, "aesthetics": 0.0,
        "restriction": -0.15, "innovation": 0.1, "compression": 0.0,
    },
    "Mercury": {
        "authority": 0.0, "empathy": 0.0, "execution": 0.1,
        "analysis": 0.35, "wisdom": 0.1, "aesthetics": 0.1,
        "restriction": 0.0, "innovation": 0.15, "compression": 0.0,
    },
    "Jupiter": {
        "authority": 0.1, "empathy": 0.15, "execution": 0.0,
        "analysis": 0.1, "wisdom": 0.35, "aesthetics": 0.1,
        "restriction": 0.0, "innovation": 0.0, "compression": -0.1,
    },
    "Venus": {
        "authority": 0.0, "empathy": 0.15, "execution": 0.0,
        "analysis": 0.0, "wisdom": 0.1, "aesthetics": 0.35,
        "restriction": -0.1, "innovation": 0.1, "compression": 0.0,
    },
    "Saturn": {
        "authority": -0.1, "empathy": -0.1, "execution": -0.1,
        "analysis": 0.1, "wisdom": 0.0, "aesthetics": -0.15,
        "restriction": 0.35, "innovation": -0.1, "compression": 0.15,
    },
    "Rahu": {
        "authority": 0.0, "empathy": -0.15, "execution": 0.1,
        "analysis": 0.1, "wisdom": -0.1, "aesthetics": 0.0,
        "restriction": -0.1, "innovation": 0.35, "compression": 0.0,
    },
    "Ketu": {
        "authority": -0.1, "empathy": 0.0, "execution": -0.1,
        "analysis": -0.1, "wisdom": 0.15, "aesthetics": 0.0,
        "restriction": 0.1, "innovation": 0.0, "compression": 0.35,
    },
}

# Planet → modifier weights (from MAPPING.md v2)
PLANET_MODIFIER_WEIGHTS: dict[str, dict[str, float]] = {
    "Sun": {"proactivity": 0.2},
    "Moon": {"agreeableness": 0.3, "creativity": 0.3},
    "Mars": {"risk_tolerance": 0.35, "agreeableness": -0.3},
    "Mercury": {"verbosity": 0.4, "proactivity": 0.35},
    "Jupiter": {"agreeableness": 0.4, "verbosity": 0.3, "risk_tolerance": 0.25},
    "Venus": {"creativity": 0.2, "proactivity": 0.25},
    "Saturn": {"verbosity": -0.3, "creativity": -0.1, "risk_tolerance": -0.2},
    "Rahu": {"creativity": 0.4, "risk_tolerance": 0.2},
    "Ketu": {"proactivity": -0.2},
}

# Dasha overlay: how each mahadasha lord shifts modifiers
DASHA_OVERLAY: dict[str, dict[str, float]] = {
    "Sun": {"verbosity": 0.1, "agreeableness": -0.1, "creativity": 0.0, "risk_tolerance": 0.1, "proactivity": 0.3},
    "Moon": {"verbosity": 0.1, "agreeableness": 0.4, "creativity": 0.2, "risk_tolerance": -0.1, "proactivity": 0.0},
    "Mars": {"verbosity": -0.1, "agreeableness": -0.3, "creativity": 0.0, "risk_tolerance": 0.4, "proactivity": 0.2},
    "Mercury": {"verbosity": 0.4, "agreeableness": 0.0, "creativity": 0.1, "risk_tolerance": 0.0, "proactivity": 0.3},
    "Jupiter": {"verbosity": 0.3, "agreeableness": 0.3, "creativity": 0.1, "risk_tolerance": 0.1, "proactivity": 0.1},
    "Venus": {"verbosity": 0.1, "agreeableness": 0.2, "creativity": 0.4, "risk_tolerance": 0.0, "proactivity": 0.2},
    "Saturn": {"verbosity": -0.3, "agreeableness": -0.1, "creativity": -0.2, "risk_tolerance": -0.3, "proactivity": -0.1},
    "Rahu": {"verbosity": 0.0, "agreeableness": -0.2, "creativity": 0.4, "risk_tolerance": 0.3, "proactivity": 0.1},
    "Ketu": {"verbosity": -0.2, "agreeableness": 0.0, "creativity": 0.1, "risk_tolerance": -0.1, "proactivity": -0.3},
}


def agent_id_to_birth(agent_id: str) -> datetime:
    """Deterministically map agent_id to a birth datetime (1970-2020).

    Uses SHA256 hash to ensure uniform distribution and determinism.
    """
    h = hashlib.sha256(agent_id.encode("utf-8")).hexdigest()

    # Use first 8 hex chars for date (32 bits → ~4B range)
    date_seed = int(h[:8], 16)
    # Map to range 1970-01-01 to 2019-12-31 (50 years = ~18262 days)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    days_range = 50 * 365  # ~18250 days
    day_offset = date_seed % days_range
    birth_date = epoch + timedelta(days=day_offset)

    # Use next 4 hex chars for time of day
    time_seed = int(h[8:12], 16)
    seconds_in_day = 24 * 60 * 60
    second_offset = time_seed % seconds_in_day
    birth_dt = birth_date + timedelta(seconds=second_offset)

    return birth_dt


def compute_natal_modifiers(positions: dict[str, dict]) -> dict[str, float]:
    """Compute base modifiers from natal planet positions.

    Each planet contributes its weight × dignity_score to each modifier.
    """
    modifiers = {m: 0.0 for m in MODIFIER_NAMES}

    for planet, pos in positions.items():
        dignity = get_dignity(planet, pos["sign"], pos["degree"])
        dignity_score = DIGNITY_SCORES.get(dignity, 0.0)

        weights = PLANET_MODIFIER_WEIGHTS.get(planet, {})
        for mod_name, weight in weights.items():
            modifiers[mod_name] += weight * dignity_score

    return modifiers


def compute_transit_modifiers(transit_scores: dict[str, float]) -> dict[str, float]:
    """Convert transit scores into modifier adjustments."""
    modifiers = {m: 0.0 for m in MODIFIER_NAMES}

    for planet, score in transit_scores.items():
        weights = PLANET_MODIFIER_WEIGHTS.get(planet, {})
        for mod_name, weight in weights.items():
            # Transit effect is score × weight (both can be negative)
            modifiers[mod_name] += score * abs(weight) * (1 if weight > 0 else -1)

    return modifiers


def compute_tarabala_volatility(
    transit_positions: dict[str, dict],
    natal_positions: dict[str, dict],
) -> float:
    """Compute volatility score based on Tarabala (star transit).

    Returns a value in [0, 1] representing how much modifiers might
    fluctuate within the current period.
    """
    natal_moon_lon = natal_positions["Moon"]["lon"]
    transit_moon_lon = transit_positions["Moon"]["lon"]

    # Tarabala = distance in nakshatras from natal to transit Moon
    nak_span = 360.0 / 27.0
    natal_nak = int(natal_moon_lon / nak_span) % 27
    transit_nak = int(transit_moon_lon / nak_span) % 27

    tara = ((transit_nak - natal_nak) % 9) + 1  # 1-9 cycle

    # Tarabala scores: 1=Janma(mid), 2=Sampat(good), 3=Vipat(bad),
    # 4=Kshema(good), 5=Pratyari(bad), 6=Sadhaka(good),
    # 7=Vadha(bad), 8=Mitra(good), 9=Param Mitra(good)
    volatility_map = {
        1: 0.5,  # Janma — moderate volatility
        2: 0.2,  # Sampat — low
        3: 0.8,  # Vipat — high
        4: 0.2,  # Kshema — low
        5: 0.7,  # Pratyari — high
        6: 0.3,  # Sadhaka — moderate-low
        7: 0.9,  # Vadha — very high
        8: 0.2,  # Mitra — low
        9: 0.1,  # Param Mitra — very low
    }

    return volatility_map.get(tara, 0.5)


def describe_phase(active_period: dict | None) -> str:
    """Create human-readable phase description."""
    if active_period is None:
        return "unknown"
    md = active_period["mahadasha"]
    ad = active_period["antardasha"]
    return f"{md}-{ad}"


def compute_modifiers(
    agent_id: str,
    timestamp: datetime | None = None,
    strict_mode: bool = False,
    weights: tuple[float, float, float] = (0.60, 0.25, 0.15),
) -> dict:
    """Compute deterministic personality modifiers for an AI agent.

    Args:
        agent_id: Unique identifier for the agent
        timestamp: UTC datetime (defaults to now)
        strict_mode: If True, clamp modifiers more aggressively
        weights: (natal, dasha, transit) weights, must sum to 1.0

    Returns:
        Dict with modifiers, phase info, volatility, and metadata
    """
    birth_dt = agent_id_to_birth(agent_id)
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    elif timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    # Natal base (60%)
    natal_positions = get_planet_positions(birth_dt)
    natal_base = compute_natal_modifiers(natal_positions)

    # Dasha phase (25%)
    moon_lon = natal_positions["Moon"]["lon"]
    timeline = compute_dasha_timeline(birth_dt, moon_lon)
    active = find_active_period(timeline, timestamp)

    if active is not None:
        dasha_mod = DASHA_OVERLAY[active["mahadasha"]]
    else:
        dasha_mod = {m: 0.0 for m in MODIFIER_NAMES}

    # Transit weather (15%)
    transit_positions = get_planet_positions(timestamp)
    natal_moon_sign = natal_positions["Moon"]["sign"]
    transit_scores = compute_transit_scores(transit_positions, natal_moon_sign)
    transit_mod = compute_transit_modifiers(transit_scores)

    # Combine with tanh
    modifiers = {}
    clamp = 0.6 if strict_mode else 1.0
    for mod in MODIFIER_NAMES:
        w_natal, w_dasha, w_transit = weights
        raw = natal_base[mod] * w_natal + dasha_mod[mod] * w_dasha + transit_mod[mod] * w_transit
        value = math.tanh(raw)
        modifiers[mod] = max(-clamp, min(clamp, value))

    # Tarabala volatility
    volatility = compute_tarabala_volatility(transit_positions, natal_positions)

    return {
        "agent_id": agent_id,
        "genesis_timestamp": birth_dt.isoformat(),
        "computed_at": timestamp.isoformat(),
        "modifiers": modifiers,
        "phase": describe_phase(active),
        "volatility": volatility,
        "strict_mode": strict_mode,
        "next_refresh": (timestamp + timedelta(hours=4)).isoformat(),
    }


# ──────────────────────────────────────────────
# v2: 9 Graha Dimensions (Digital Soul)
# ──────────────────────────────────────────────

def compute_transit_dimensions(
    transit_scores: dict[str, float],
) -> dict[str, float]:
    """Convert transit scores into 9-dimension adjustments.

    Each planet's transit score maps directly to its governing dimension.
    """
    dimensions = {d: 0.0 for d in DIMENSION_NAMES}
    for planet, score in transit_scores.items():
        dim = PLANET_TO_DIMENSION.get(planet)
        if dim:
            dimensions[dim] += score * 0.5  # Scale transit effect
    return dimensions


def compute_modifiers_v2(
    soul: "AgentSoul",
    timestamp: datetime | None = None,
    weights: tuple[float, float, float] = (0.60, 0.25, 0.15),
) -> dict:
    """Compute 9-dimensional personality modifiers from a Digital Soul.

    Hierarchy: Natal (ceiling) x Dasha (throttle) x Transit (trigger).
    Combined additively with tanh saturation and hard caps.

    Args:
        soul: AgentSoul instance (from soul.py)
        timestamp: UTC datetime (defaults to now)
        weights: (natal, dasha, transit) weights

    Returns:
        Dict with dimensions (9), yogas, phase info, volatility, metadata
    """
    from agent_soul.soul import AgentSoul

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    elif timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    w_natal, w_dasha, w_transit = weights

    # 1. Natal base (from soul — already computed at creation)
    natal_dims = soul.dimensions

    # 2. Dasha overlay
    moon_lon = soul.moon_lon
    timeline = compute_dasha_timeline(soul.birth_dt, moon_lon)
    active = find_active_period(timeline, timestamp)

    if active is not None:
        dasha_dims = DASHA_OVERLAY_V2.get(active["mahadasha"], {})
    else:
        dasha_dims = {}

    # 3. Transit weather
    transit_positions = get_planet_positions(timestamp)
    natal_moon_sign = soul.positions["Moon"]["sign"]
    transit_scores = compute_transit_scores(transit_positions, natal_moon_sign)
    transit_dims = compute_transit_dimensions(transit_scores)

    # 4. Combine: additive with tanh
    dimensions = {}
    for dim in DIMENSION_NAMES:
        raw = (
            natal_dims.get(dim, 0.0) * w_natal
            + dasha_dims.get(dim, 0.0) * w_dasha
            + transit_dims.get(dim, 0.0) * w_transit
        )
        dimensions[dim] = max(-1.0, min(1.0, math.tanh(raw)))

    # 5. Tarabala volatility
    natal_positions = get_planet_positions(soul.birth_dt)
    volatility = compute_tarabala_volatility(transit_positions, natal_positions)

    return {
        "agent_id": soul.seed,
        "genesis_timestamp": soul.birth_dt.isoformat(),
        "computed_at": timestamp.isoformat(),
        "lagna": soul.lagna_sign,
        "dimensions": dimensions,
        "yogas": soul.yogas,
        "retrograde": soul.retrograde_planets,
        "capabilities": soul.capabilities,
        "phase": describe_phase(active),
        "volatility": volatility,
        "next_refresh": (timestamp + timedelta(hours=4)).isoformat(),
    }
