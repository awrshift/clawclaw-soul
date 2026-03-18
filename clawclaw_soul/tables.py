"""BPHS reference tables — public domain Vedic astrology data.

All data from Brihat Parashara Hora Shastra (1500+ years old, public domain).
"""

from __future__ import annotations

# --- Signs ---

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_INDEX = {name: i for i, name in enumerate(SIGNS)}

# --- Nakshatras (27 lunar mansions) ---

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Nakshatra rulers cycle: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
NAKSHATRA_RULERS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

# --- Exaltation / Debilitation ---
# {planet: (exaltation_sign, exaltation_degree, debilitation_sign, debilitation_degree)}

EXALTATION = {
    "Sun": ("Aries", 10),
    "Moon": ("Taurus", 3),
    "Mars": ("Capricorn", 28),
    "Mercury": ("Virgo", 15),
    "Jupiter": ("Cancer", 5),
    "Venus": ("Pisces", 27),
    "Saturn": ("Libra", 20),
    "Rahu": ("Taurus", 20),
    "Ketu": ("Scorpio", 20),
}

DEBILITATION = {
    "Sun": ("Libra", 10),
    "Moon": ("Scorpio", 3),
    "Mars": ("Cancer", 28),
    "Mercury": ("Pisces", 15),
    "Jupiter": ("Capricorn", 5),
    "Venus": ("Virgo", 27),
    "Saturn": ("Aries", 20),
    "Rahu": ("Scorpio", 20),
    "Ketu": ("Taurus", 20),
}

# --- Ownership ---
# {planet: [signs owned]}

OWNERSHIP = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
    "Rahu": ["Aquarius"],  # co-ruler
    "Ketu": ["Scorpio"],   # co-ruler
}

# --- Moolatrikona ---
# {planet: (sign, start_degree, end_degree)}

MOOLATRIKONA = {
    "Sun": ("Leo", 0, 20),
    "Moon": ("Taurus", 3, 30),
    "Mars": ("Aries", 0, 12),
    "Mercury": ("Virgo", 15, 20),
    "Jupiter": ("Sagittarius", 0, 10),
    "Venus": ("Libra", 0, 15),
    "Saturn": ("Aquarius", 0, 20),
}

# --- Natural Friendships (BPHS) ---
# For each planet: friends, neutrals, enemies

NATURAL_FRIENDSHIPS: dict[str, dict[str, str]] = {}

_FRIENDS = {
    "Sun": ["Moon", "Mars", "Jupiter"],
    "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"],
    "Rahu": ["Mercury", "Venus", "Saturn"],
    "Ketu": ["Mars", "Jupiter"],
}

_ENEMIES = {
    "Sun": ["Venus", "Saturn"],
    "Moon": ["Rahu", "Ketu"],
    "Mars": ["Mercury"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus"],
    "Venus": ["Sun", "Moon"],
    "Saturn": ["Sun", "Moon", "Mars"],
    "Rahu": ["Sun", "Moon", "Mars"],
    "Ketu": ["Moon", "Venus"],
}

_ALL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

for planet in _ALL_PLANETS:
    friends = set(_FRIENDS.get(planet, []))
    enemies = set(_ENEMIES.get(planet, []))
    NATURAL_FRIENDSHIPS[planet] = {}
    for other in _ALL_PLANETS:
        if other == planet:
            continue
        if other in friends:
            NATURAL_FRIENDSHIPS[planet][other] = "friend"
        elif other in enemies:
            NATURAL_FRIENDSHIPS[planet][other] = "enemy"
        else:
            NATURAL_FRIENDSHIPS[planet][other] = "neutral"

# --- Mahadasha years (total = 120) ---

MAHADASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

# Dasha sequence order
DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# --- Gochar (transit) favorable houses from Moon ---
# {planet: list of favorable houses (1-based)}

GOCHAR_FAVORABLE = {
    "Sun": [3, 6, 10, 11],
    "Moon": [1, 3, 6, 7, 10, 11],
    "Mars": [3, 6, 11],
    "Mercury": [2, 4, 6, 8, 10, 11],
    "Jupiter": [2, 5, 7, 9, 11],
    "Venus": [1, 2, 3, 4, 5, 8, 9, 11, 12],
    "Saturn": [3, 6, 11],
    "Rahu": [3, 6, 10, 11],
    "Ketu": [3, 6, 10, 11],
}

# --- Vedha pairs ---
# {planet: {favorable_house: obstructing_house}}

VEDHA_PAIRS = {
    "Sun": {3: 9, 6: 12, 10: 4, 11: 5},
    "Moon": {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "Mars": {3: 12, 6: 9, 11: 5},
    "Mercury": {2: 5, 4: 3, 6: 9, 8: 1, 10: 7, 11: 12},
    "Jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    "Venus": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 6, 12: 3},
    "Saturn": {3: 12, 6: 9, 11: 5},
    "Rahu": {3: 12, 6: 9, 10: 4, 11: 5},
    "Ketu": {3: 12, 6: 9, 10: 4, 11: 5},
}

# --- Dignity scores ---

DIGNITY_SCORES = {
    "exalted": 1.0,
    "moolatrikona": 0.8,
    "own_sign": 0.7,
    "friend": 0.3,
    "neutral": 0.0,
    "enemy": -0.3,
    "debilitated": -1.0,
}


def get_sign(longitude: float) -> str:
    """Get zodiac sign from sidereal longitude (0-360)."""
    return SIGNS[int(longitude // 30) % 12]


def get_sign_degree(longitude: float) -> float:
    """Get degree within sign (0-30) from sidereal longitude."""
    return longitude % 30


def get_nakshatra(longitude: float) -> tuple[str, int]:
    """Get nakshatra name and pada (1-4) from sidereal longitude."""
    nak_span = 360.0 / 27.0  # 13.333...
    nak_index = int(longitude / nak_span) % 27
    pos_in_nak = longitude % nak_span
    pada = int(pos_in_nak / (nak_span / 4)) + 1
    pada = min(pada, 4)
    return NAKSHATRAS[nak_index], pada


def get_nakshatra_ruler(longitude: float) -> str:
    """Get the ruler planet of the nakshatra at given longitude."""
    nak_span = 360.0 / 27.0
    nak_index = int(longitude / nak_span) % 27
    return NAKSHATRA_RULERS[nak_index]


def get_dignity(planet: str, sign: str, degree: float) -> str:
    """Determine dignity of a planet in a given sign and degree."""
    # Check exaltation
    if planet in EXALTATION:
        ex_sign, _ = EXALTATION[planet]
        if sign == ex_sign:
            return "exalted"

    # Check debilitation
    if planet in DEBILITATION:
        deb_sign, _ = DEBILITATION[planet]
        if sign == deb_sign:
            return "debilitated"

    # Check moolatrikona
    if planet in MOOLATRIKONA:
        mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
        if sign == mt_sign and mt_start <= degree <= mt_end:
            return "moolatrikona"

    # Check own sign
    if planet in OWNERSHIP:
        if sign in OWNERSHIP[planet]:
            return "own_sign"

    # Check friendship
    sign_lord = get_sign_lord(sign)
    if sign_lord and planet in NATURAL_FRIENDSHIPS:
        relationship = NATURAL_FRIENDSHIPS[planet].get(sign_lord, "neutral")
        return relationship

    return "neutral"


def get_sign_lord(sign: str) -> str | None:
    """Get the lord (ruler) of a sign."""
    for planet, signs in OWNERSHIP.items():
        if planet in ("Rahu", "Ketu"):
            continue  # Use traditional rulers
        if sign in signs:
            return planet
    return None


def get_house_from_moon(planet_sign: str, moon_sign: str) -> int:
    """Calculate house number (1-12) of planet from Moon sign."""
    planet_idx = SIGN_INDEX.get(planet_sign, 0)
    moon_idx = SIGN_INDEX.get(moon_sign, 0)
    return ((planet_idx - moon_idx) % 12) + 1
