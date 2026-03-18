"""Skyfield wrapper for planet positions, retrograde detection, ayanamsha."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from skyfield.api import Loader, load as sf_load
from skyfield.timelib import Time

from clawclaw_soul.tables import get_nakshatra, get_sign, get_sign_degree

# Cache directory for ephemeris files
CACHE_DIR = Path(os.environ.get("AGENT_SOUL_CACHE", Path.home() / ".agent-soul"))

# Planet name → Skyfield target mapping
_SKYFIELD_TARGETS = {
    "Sun": "sun",
    "Moon": "moon",
    "Mars": "mars",
    "Mercury": "mercury",
    "Jupiter": "jupiter barycenter",
    "Venus": "venus",
    "Saturn": "saturn barycenter",
}

_loader: Loader | None = None
_ephemeris = None
_ts = None


def _ensure_loaded():
    """Load ephemeris file on first use."""
    global _loader, _ephemeris, _ts
    if _ephemeris is not None:
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _loader = Loader(str(CACHE_DIR))
    _ephemeris = _loader("de421.bsp")
    _ts = _loader.timescale()


def _dt_to_skyfield_time(dt: datetime) -> Time:
    """Convert datetime to Skyfield Time object."""
    _ensure_loaded()
    return _ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def get_ayanamsha(jd: float) -> float:
    """Compute Lahiri ayanamsha for a given Julian day.

    Uses the standard Lahiri polynomial approximation.
    """
    t_centuries = (jd - 2451545.0) / 36525.0
    # Lahiri ayanamsha: precession-based formula
    ayanamsha = 23.85 + 0.01396 * (jd - 2451545.0) / 365.25
    return ayanamsha


def _compute_rahu_longitude(jd: float) -> float:
    """Compute mean Rahu (North Node) longitude.

    Uses the standard mean node formula.
    """
    t = (jd - 2451545.0) / 36525.0
    # Mean longitude of ascending node (tropical)
    rahu_tropical = (125.04452 - 1934.136261 * t) % 360
    return rahu_tropical


def is_retrograde(planet: str, dt: datetime) -> bool:
    """Check if a planet is retrograde at given datetime.

    Rahu and Ketu are always considered retrograde (mean motion).
    """
    if planet in ("Rahu", "Ketu"):
        return True

    _ensure_loaded()
    t = _dt_to_skyfield_time(dt)
    target_name = _SKYFIELD_TARGETS.get(planet)
    if target_name is None:
        return False

    if planet == "Sun":
        return False  # Sun never retrogrades

    earth = _ephemeris["earth"]
    target = _ephemeris[target_name]

    # Compute position at t and t + small delta
    astrometric = earth.at(t).observe(target)
    lat, lon, _ = astrometric.apparent().ecliptic_latlon()

    from skyfield.api import load as sf_load2
    delta_days = 0.1  # ~2.4 hours
    t2 = _ts.tt_jd(t.tt + delta_days)
    astrometric2 = earth.at(t2).observe(target)
    lat2, lon2, _ = astrometric2.apparent().ecliptic_latlon()

    # If longitude decreased, planet is retrograde
    lon_diff = lon2.degrees - lon.degrees
    # Handle wrap-around at 360°
    if lon_diff > 180:
        lon_diff -= 360
    elif lon_diff < -180:
        lon_diff += 360

    return lon_diff < 0


def get_planet_positions(dt: datetime) -> dict[str, dict]:
    """Get sidereal positions of all 9 Vedic planets.

    Args:
        dt: UTC datetime

    Returns:
        Dict mapping planet name to position info:
        {planet: {lon, sign, nakshatra, pada, motion}}
    """
    _ensure_loaded()
    t = _dt_to_skyfield_time(dt)
    jd = t.tt

    ayanamsha = get_ayanamsha(jd)
    positions = {}

    earth = _ephemeris["earth"]

    # Compute Sun through Saturn via Skyfield
    for planet, target_name in _SKYFIELD_TARGETS.items():
        target = _ephemeris[target_name]
        astrometric = earth.at(t).observe(target)
        _, lon, _ = astrometric.apparent().ecliptic_latlon()

        tropical_lon = lon.degrees
        sidereal_lon = (tropical_lon - ayanamsha) % 360

        sign = get_sign(sidereal_lon)
        degree = get_sign_degree(sidereal_lon)
        nakshatra, pada = get_nakshatra(sidereal_lon)
        retro = is_retrograde(planet, dt)

        positions[planet] = {
            "lon": sidereal_lon,
            "sign": sign,
            "degree": degree,
            "nakshatra": nakshatra,
            "pada": pada,
            "motion": "retrograde" if retro else "direct",
        }

    # Compute Rahu and Ketu via mean node formula
    rahu_tropical = _compute_rahu_longitude(jd)
    rahu_sidereal = (rahu_tropical - ayanamsha) % 360
    ketu_sidereal = (rahu_sidereal + 180) % 360

    for node_name, node_lon in [("Rahu", rahu_sidereal), ("Ketu", ketu_sidereal)]:
        sign = get_sign(node_lon)
        degree = get_sign_degree(node_lon)
        nakshatra, pada = get_nakshatra(node_lon)

        positions[node_name] = {
            "lon": node_lon,
            "sign": sign,
            "degree": degree,
            "nakshatra": nakshatra,
            "pada": pada,
            "motion": "retrograde",
        }

    return positions
