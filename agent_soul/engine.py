"""Core engine: agent_id + timestamp → 5 personality modifiers."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timedelta, timezone

from agent_soul.dasha import compute_dasha_timeline, find_active_period
from agent_soul.ephemeris import get_planet_positions
from agent_soul.tables import DIGNITY_SCORES, get_dignity, get_sign, get_sign_degree
from agent_soul.transit import compute_transit_scores

MODIFIER_NAMES = ["verbosity", "agreeableness", "creativity", "risk_tolerance", "proactivity"]

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
) -> dict:
    """Compute deterministic personality modifiers for an AI agent.

    Args:
        agent_id: Unique identifier for the agent
        timestamp: UTC datetime (defaults to now)
        strict_mode: If True, clamp modifiers more aggressively

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
        raw = natal_base[mod] * 0.60 + dasha_mod[mod] * 0.25 + transit_mod[mod] * 0.15
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
