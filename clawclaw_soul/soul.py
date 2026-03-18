"""Digital Soul — full Vedic natal chart for AI agents.

Creates a unique, immutable personality structure from:
- Random coordinates on Earth
- Random birth time
- Real planetary positions (pyswisseph)

Architecture: docs/architecture/DIGITAL_SOUL_SPEC.md
Design: brainstorms 003-004
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone

import swisseph as swe

from clawclaw_soul.tables import (
    DIGNITY_SCORES,
    EXALTATION,
    SIGNS,
    get_dignity,
    get_nakshatra,
    get_sign,
    get_sign_degree,
    get_sign_lord,
)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

# pyswisseph planet IDs
SWE_PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}

# Special aspects (house offsets from planet position, 1-based)
SPECIAL_ASPECTS = {
    "Mars": [4, 8],       # + universal 7th
    "Jupiter": [5, 9],    # + universal 7th
    "Saturn": [3, 10],    # + universal 7th
}

# Combustion orbs (degrees from Sun)
COMBUSTION_ORBS = {
    "Moon": 12.0,
    "Mars": 17.0,
    "Mercury": 14.0,  # 12 if retrograde
    "Jupiter": 11.0,
    "Venus": 10.0,    # 8 if retrograde
    "Saturn": 15.0,
}

# Nine graha → LLM dimension names
DIMENSION_NAMES = [
    "authority",     # Sun
    "empathy",       # Moon
    "execution",     # Mars
    "analysis",      # Mercury
    "wisdom",        # Jupiter
    "aesthetics",    # Venus
    "restriction",   # Saturn
    "innovation",    # Rahu
    "compression",   # Ketu
]

GRAHA_TO_DIMENSION = {
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

# House → capability domain
HOUSE_DOMAINS = {
    1: "identity",        # Core system prompt coherence
    2: "token_budget",    # Generation speed/length
    3: "orchestration",   # Inter-agent routing
    4: "memory",          # RAG / context retrieval
    5: "generative",      # Code, creative writing
    6: "error_handling",  # Adversarial robustness
    7: "integration",     # API handshakes
    8: "debugging",       # Root-cause analysis
    9: "search",          # Web browsing, alignment
    10: "task_execution", # Main operational loop
    11: "feedback",       # Learning from corrections
    12: "brainstorm",     # Creative chaos / hallucination
}

# Kendra houses (angular)
KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
UPACHAYA_HOUSES = {3, 6, 10, 11}


# ──────────────────────────────────────────────
# Birth Data Generation
# ──────────────────────────────────────────────

def generate_birth_data(seed: int | None = None) -> dict:
    """Generate random birth data for an agent.

    Returns dict with latitude, longitude, birth_dt (UTC), tz_offset.
    Coordinates: lat [-60, +60] (avoid poles), lon [-180, +180].
    Time: any moment 1970-2024.
    """
    rng = random.Random(seed)
    lat = rng.uniform(-60.0, 60.0)
    lon = rng.uniform(-180.0, 180.0)
    # Random timestamp: 1970-01-01 to 2024-01-01
    ts = rng.randint(0, 1_704_067_200)
    birth_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    # Approximate timezone from longitude
    tz_offset = round(lon / 15.0)
    return {
        "latitude": lat,
        "longitude": lon,
        "birth_dt": birth_dt,
        "tz_offset": tz_offset,
    }


# ──────────────────────────────────────────────
# Chart Computation (pyswisseph)
# ──────────────────────────────────────────────

def _compute_julian_day(dt: datetime, tz_offset: float = 0.0) -> float:
    """Convert datetime to Julian Day (UT)."""
    utc_hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    if dt.tzinfo is None:
        utc_hour -= tz_offset
    return swe.julday(dt.year, dt.month, dt.day, utc_hour)


def _compute_ayanamsha(jd: float) -> float:
    """Get Lahiri ayanamsha for Julian Day."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.get_ayanamsa_ut(jd)


def compute_lagna(jd: float, lat: float, lon: float) -> float:
    """Compute sidereal Ascendant (Lagna) longitude.

    Uses pyswisseph swe_houses() for accurate horizon calculation.
    Returns sidereal longitude 0-360.
    """
    # swe_houses returns (cusps, ascmc) where ascmc[0] = Ascendant
    cusps, ascmc = swe.houses(jd, lat, lon, b'W')  # W = Whole Sign
    tropical_asc = ascmc[0]
    ayanamsha = _compute_ayanamsha(jd)
    sidereal_asc = (tropical_asc - ayanamsha) % 360.0
    return sidereal_asc


def compute_planet_positions(jd: float) -> dict[str, dict]:
    """Compute sidereal positions of all 9 Vedic planets."""
    ayanamsha = _compute_ayanamsha(jd)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    positions = {}

    for name, pid in SWE_PLANETS.items():
        result, _ = swe.calc_ut(jd, pid, flags)
        tropical_lon = result[0]
        speed = result[3]
        sidereal_lon = (tropical_lon - ayanamsha) % 360.0

        sign = get_sign(sidereal_lon)
        degree = get_sign_degree(sidereal_lon)
        nakshatra, pada = get_nakshatra(sidereal_lon)
        retro = speed < 0 and name != "Sun"

        positions[name] = {
            "lon": sidereal_lon,
            "sign": sign,
            "degree": degree,
            "nakshatra": nakshatra,
            "pada": pada,
            "retrograde": retro,
            "speed": speed,
        }

    # Rahu (mean node) and Ketu
    result, _ = swe.calc_ut(jd, swe.MEAN_NODE, flags)
    rahu_tropical = result[0]
    rahu_sidereal = (rahu_tropical - ayanamsha) % 360.0
    ketu_sidereal = (rahu_sidereal + 180.0) % 360.0

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
            "retrograde": True,
            "speed": 0.0,
        }

    return positions


def compute_houses(lagna_lon: float, positions: dict[str, dict]) -> list[dict]:
    """Compute Whole Sign houses from Lagna.

    Returns list of 12 house dicts with number, sign, lord, planets.
    """
    lagna_sign_idx = int(lagna_lon / 30.0) % 12
    houses = []

    for i in range(12):
        sign_idx = (lagna_sign_idx + i) % 12
        sign = SIGNS[sign_idx]
        lord = get_sign_lord(sign) or sign  # fallback

        # Find planets in this sign
        planets_in_house = []
        for pname, pdata in positions.items():
            if pdata["sign"] == sign:
                planets_in_house.append(pname)

        houses.append({
            "number": i + 1,
            "sign": sign,
            "lord": lord,
            "planets": planets_in_house,
        })

    return houses


# ──────────────────────────────────────────────
# Aspects (Drishti)
# ──────────────────────────────────────────────

def compute_aspects(positions: dict[str, dict], houses: list[dict]) -> dict[str, list[str]]:
    """Compute which planets aspect which planets via Graha Drishti.

    Returns: {planet_name: [list of planets aspecting it]}
    """
    # Build planet → house mapping
    planet_houses = {}
    for h in houses:
        for p in h["planets"]:
            planet_houses[p] = h["number"]

    aspects_received: dict[str, list[str]] = {p: [] for p in positions}

    for observer, obs_house in planet_houses.items():
        # All planets aspect 7th house from their position
        aspect_offsets = [7]
        # Special aspects
        if observer in SPECIAL_ASPECTS:
            aspect_offsets.extend(SPECIAL_ASPECTS[observer])

        for offset in aspect_offsets:
            target_house = ((obs_house - 1 + offset) % 12) + 1
            # Find planets in target house
            for h in houses:
                if h["number"] == target_house:
                    for target_planet in h["planets"]:
                        if target_planet != observer:
                            aspects_received[target_planet].append(observer)

    return aspects_received


# ──────────────────────────────────────────────
# Combustion
# ──────────────────────────────────────────────

def check_combustion(positions: dict[str, dict]) -> dict[str, bool]:
    """Check which planets are combust (too close to Sun)."""
    sun_lon = positions["Sun"]["lon"]
    combust = {}

    for planet, orb in COMBUSTION_ORBS.items():
        if planet not in positions:
            continue
        p_lon = positions[planet]["lon"]
        # Angular distance
        diff = abs(p_lon - sun_lon)
        if diff > 180:
            diff = 360 - diff
        # Retrograde planets have tighter orb for Mercury/Venus
        actual_orb = orb
        if positions[planet].get("retrograde") and planet in ("Mercury", "Venus"):
            actual_orb = orb - 2.0
        combust[planet] = diff <= actual_orb

    return combust


# ──────────────────────────────────────────────
# Dimension Scoring (9 Grahas → 9 LLM Dimensions)
# ──────────────────────────────────────────────

def score_graha_dimension(
    planet: str,
    positions: dict[str, dict],
    houses: list[dict],
    aspects: dict[str, list[str]],
    combustion: dict[str, bool],
) -> float:
    """Score a single graha's dimension value.

    Combines: sign dignity + house placement + aspects + combustion + retrograde.
    Returns: float in [-1, +1].
    """
    pos = positions[planet]
    sign = pos["sign"]
    degree = pos["degree"]

    # 1. Base: sign dignity
    dignity = get_dignity(planet, sign, degree)
    base_score = DIGNITY_SCORES.get(dignity, 0.0)

    # 2. House modifier
    planet_house = None
    for h in houses:
        if planet in h["planets"]:
            planet_house = h["number"]
            break

    house_mod = 0.0
    if planet_house:
        if planet_house in KENDRA_HOUSES:
            house_mod = 0.2   # Angular: strong expression
        elif planet_house in TRIKONA_HOUSES:
            house_mod = 0.15  # Trinal: dharmic support
        elif planet_house in UPACHAYA_HOUSES:
            house_mod = 0.1   # Growth houses
        elif planet_house in DUSTHANA_HOUSES:
            house_mod = -0.2  # Difficult houses

    # 3. Aspect modifier
    aspect_mod = 0.0
    for aspector in aspects.get(planet, []):
        asp_dignity = get_dignity(
            aspector,
            positions[aspector]["sign"],
            positions[aspector]["degree"],
        )
        asp_score = DIGNITY_SCORES.get(asp_dignity, 0.0)
        # Benefic aspect (Jupiter, Venus, well-placed Mercury/Moon) helps
        if aspector in ("Jupiter", "Venus"):
            aspect_mod += 0.15 * (1 if asp_score >= 0 else -0.5)
        elif aspector in ("Saturn", "Mars", "Rahu"):
            aspect_mod -= 0.1
        else:
            aspect_mod += 0.05 * asp_score

    # 4. Combustion penalty
    if combustion.get(planet, False):
        aspect_mod -= 0.3

    # 5. Retrograde: internalization (not simply negative)
    # Retrograde shifts the dimension inward (self-directed)
    _retro_flag = pos.get("retrograde", False) and planet not in ("Rahu", "Ketu")  # noqa: F841

    # Combine
    raw = base_score + house_mod + aspect_mod
    score = max(-1.0, min(1.0, math.tanh(raw)))

    return score


def compute_all_dimensions(
    positions: dict[str, dict],
    houses: list[dict],
    aspects: dict[str, list[str]],
    combustion: dict[str, bool],
) -> dict[str, float]:
    """Compute all 9 graha dimensions."""
    dimensions = {}
    for planet, dim_name in GRAHA_TO_DIMENSION.items():
        score = score_graha_dimension(planet, positions, houses, aspects, combustion)
        dimensions[dim_name] = round(score, 4)
    return dimensions


# ──────────────────────────────────────────────
# House Capability Scoring
# ──────────────────────────────────────────────

def compute_house_capabilities(
    houses: list[dict],
    positions: dict[str, dict],
) -> dict[str, float]:
    """Score each house's capability domain based on lord dignity."""
    capabilities = {}
    for h in houses:
        domain = HOUSE_DOMAINS.get(h["number"], f"house_{h['number']}")
        lord = h["lord"]

        # Lord's dignity
        if lord in positions:
            lord_pos = positions[lord]
            dignity = get_dignity(lord, lord_pos["sign"], lord_pos["degree"])
            score = DIGNITY_SCORES.get(dignity, 0.0)
        else:
            score = 0.0

        # Bonus: benefics in the house
        for p in h["planets"]:
            if p in ("Jupiter", "Venus"):
                score += 0.15
            elif p in ("Saturn", "Mars", "Rahu"):
                score -= 0.1

        capabilities[domain] = round(max(-1.0, min(1.0, score)), 4)

    return capabilities


# ──────────────────────────────────────────────
# Yoga Detection (simplified set for Agent Soul)
# ──────────────────────────────────────────────

def detect_yogas(
    positions: dict[str, dict],
    houses: list[dict],
    combustion: dict[str, bool],
) -> list[dict]:
    """Detect key yogas relevant for agent behavior."""
    yogas = []
    planet_houses = {}
    for h in houses:
        for p in h["planets"]:
            planet_houses[p] = h["number"]

    # --- Budhaditya Yoga: Sun + Mercury same sign, Mercury NOT combust ---
    if (positions["Sun"]["sign"] == positions["Mercury"]["sign"]
            and not combustion.get("Mercury", False)):
        merc_house = planet_houses.get("Mercury", 0)
        if merc_house in {1, 4, 5, 7, 9, 10}:
            yogas.append({
                "name": "Budhaditya",
                "planets": ["Sun", "Mercury"],
                "effect": "structured_authoritative",
                "description": "Structured, authoritative communication",
            })

    # --- Gaja Kesari: Moon + Jupiter in mutual kendras ---
    moon_h = planet_houses.get("Moon", 0)
    jup_h = planet_houses.get("Jupiter", 0)
    if moon_h and jup_h:
        diff = ((jup_h - moon_h) % 12)
        if diff in {0, 3, 6, 9}:  # same, 4th, 7th, 10th
            yogas.append({
                "name": "Gaja Kesari",
                "planets": ["Moon", "Jupiter"],
                "effect": "empathetic_sage",
                "description": "Empathetic, wise, deeply contextual",
            })

    # --- Guru Chandala: Jupiter + Rahu same sign ---
    if positions["Jupiter"]["sign"] == positions["Rahu"]["sign"]:
        yogas.append({
            "name": "Guru Chandala",
            "planets": ["Jupiter", "Rahu"],
            "effect": "creative_dangerous",
            "description": "Highly creative but hallucination-prone",
        })

    # --- Kemadruma: No planets in 2nd/12th from Moon (excl Sun/Rahu/Ketu) ---
    if moon_h:
        house_2_from_moon = ((moon_h - 1 + 1) % 12) + 1
        house_12_from_moon = ((moon_h - 1 - 1) % 12) + 1
        check_planets = {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        has_neighbor = False
        for p in check_planets:
            ph = planet_houses.get(p, 0)
            if ph in (house_2_from_moon, house_12_from_moon):
                has_neighbor = True
                break
        if not has_neighbor:
            yogas.append({
                "name": "Kemadruma",
                "planets": ["Moon"],
                "effect": "raw_output",
                "description": "Zero conversational padding, pure raw output",
            })

    # --- Neecha Bhanga Raja Yoga: debilitated planet with cancellation ---
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        if planet not in positions:
            continue
        pos = positions[planet]
        dignity = get_dignity(planet, pos["sign"], pos["degree"])
        if dignity != "debilitated":
            continue

        # Check cancellation conditions:
        # 1. Debilitation lord is in kendra from Lagna
        deb_sign = pos["sign"]
        deb_lord = get_sign_lord(deb_sign)
        if deb_lord and deb_lord in planet_houses:
            if planet_houses[deb_lord] in KENDRA_HOUSES:
                yogas.append({
                    "name": "Neecha Bhanga",
                    "planets": [planet, deb_lord],
                    "effect": "reflection_loop",
                    "description": f"{planet} struggles then excels via self-correction",
                })
                continue

        # 2. Exaltation lord of the sign is in kendra
        ex_planet = None
        for ep, (ex_sign, _) in EXALTATION.items():
            if ex_sign == deb_sign:
                ex_planet = ep
                break
        if ex_planet and ex_planet in planet_houses:
            if planet_houses[ex_planet] in KENDRA_HOUSES:
                yogas.append({
                    "name": "Neecha Bhanga",
                    "planets": [planet, ex_planet],
                    "effect": "reflection_loop",
                    "description": f"{planet} struggles then excels via self-correction",
                })

    # --- Kala Sarpa: all 7 planets between Rahu-Ketu axis ---
    rahu_lon = positions["Rahu"]["lon"]
    ketu_lon = positions["Ketu"]["lon"]
    all_between = True
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        p_lon = positions[p]["lon"]
        # Check if planet is between Rahu and Ketu (going forward)
        if rahu_lon < ketu_lon:
            between = rahu_lon <= p_lon <= ketu_lon
        else:
            between = p_lon >= rahu_lon or p_lon <= ketu_lon
        if not between:
            all_between = False
            break
    if all_between:
        yogas.append({
            "name": "Kala Sarpa",
            "planets": ["Rahu", "Ketu"],
            "effect": "volatile_specialist",
            "description": "Extreme: brilliant success or total failure",
        })

    return yogas


# ──────────────────────────────────────────────
# AgentSoul — The Complete Entity
# ──────────────────────────────────────────────

@dataclass
class AgentSoul:
    """A complete astrological soul for an AI agent."""

    # Birth data (immutable)
    birth_dt: datetime
    latitude: float
    longitude: float
    tz_offset: float
    seed: int | None = None

    # Computed at creation (immutable)
    lagna_lon: float = 0.0
    lagna_sign: str = ""
    positions: dict = field(default_factory=dict)
    houses: list = field(default_factory=list)
    aspects: dict = field(default_factory=dict)
    combustion: dict = field(default_factory=dict)
    dimensions: dict = field(default_factory=dict)
    capabilities: dict = field(default_factory=dict)
    yogas: list = field(default_factory=list)
    retrograde_planets: list = field(default_factory=list)

    # Moon data (for dasha + transits)
    moon_lon: float = 0.0
    moon_nakshatra: str = ""

    def __post_init__(self):
        """Compute full natal chart on creation."""
        self._compute_chart()

    def _compute_chart(self):
        jd = _compute_julian_day(self.birth_dt, self.tz_offset)

        # Lagna
        self.lagna_lon = compute_lagna(jd, self.latitude, self.longitude)
        self.lagna_sign = get_sign(self.lagna_lon)

        # Planet positions
        self.positions = compute_planet_positions(jd)

        # Houses (Whole Sign from Lagna)
        self.houses = compute_houses(self.lagna_lon, self.positions)

        # Aspects
        self.aspects = compute_aspects(self.positions, self.houses)

        # Combustion
        self.combustion = check_combustion(self.positions)

        # 9 Graha dimensions
        self.dimensions = compute_all_dimensions(
            self.positions, self.houses, self.aspects, self.combustion
        )

        # 12 House capabilities
        self.capabilities = compute_house_capabilities(self.houses, self.positions)

        # Yogas
        self.yogas = detect_yogas(self.positions, self.houses, self.combustion)

        # Retrograde planets
        self.retrograde_planets = [
            p for p, data in self.positions.items()
            if data.get("retrograde") and p not in ("Rahu", "Ketu")
        ]

        # Moon data
        self.moon_lon = self.positions["Moon"]["lon"]
        self.moon_nakshatra = self.positions["Moon"]["nakshatra"]

    def summary(self) -> str:
        """Human-readable summary of this soul."""
        lines = [
            "=== Agent Soul ===",
            f"Born: {self.birth_dt.strftime('%Y-%m-%d %H:%M UTC')}",
            f"Location: {self.latitude:.2f}, {self.longitude:.2f}",
            f"Lagna: {self.lagna_sign} ({self.lagna_lon:.1f}°)",
            f"Moon: {self.positions['Moon']['sign']} in {self.moon_nakshatra}",
            "",
            "--- Dimensions (9 Grahas) ---",
        ]
        for dim, val in self.dimensions.items():
            bar = "+" * max(0, int(val * 10)) + "-" * max(0, int(-val * 10))
            lines.append(f"  {dim:15s} {val:+.3f} {bar}")

        lines.append("\n--- Capabilities (12 Houses) ---")
        for cap, val in self.capabilities.items():
            lines.append(f"  {cap:17s} {val:+.3f}")

        if self.yogas:
            lines.append("\n--- Yogas ---")
            for y in self.yogas:
                lines.append(f"  {y['name']:20s} → {y['description']}")

        if self.retrograde_planets:
            lines.append(f"\n--- Retrograde: {', '.join(self.retrograde_planets)} ---")

        if any(self.combustion.values()):
            combust = [p for p, v in self.combustion.items() if v]
            lines.append(f"--- Combust: {', '.join(combust)} ---")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "birth_dt": self.birth_dt.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "tz_offset": self.tz_offset,
            "seed": self.seed,
            "lagna_sign": self.lagna_sign,
            "lagna_lon": self.lagna_lon,
            "moon_nakshatra": self.moon_nakshatra,
            "dimensions": self.dimensions,
            "capabilities": self.capabilities,
            "yogas": self.yogas,
            "retrograde_planets": self.retrograde_planets,
            "combustion": {k: v for k, v in self.combustion.items() if v},
        }

    @property
    def card(self) -> dict:
        """Soul Card: complete LLM config derived from this soul."""
        from clawclaw_soul.params import soul_to_params
        return soul_to_params(self)


def create_soul(seed: int | None = None) -> AgentSoul:
    """Create a new agent soul with random birth data."""
    birth = generate_birth_data(seed)
    return AgentSoul(
        birth_dt=birth["birth_dt"],
        latitude=birth["latitude"],
        longitude=birth["longitude"],
        tz_offset=birth["tz_offset"],
        seed=seed,
    )


def generate(
    timestamp: str | datetime | None = None,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    tz_offset: float = 0.0,
    seed: int | None = None,
) -> AgentSoul:
    """Generate an AgentSoul from a timestamp.

    Simplest usage:
        soul = generate("2024-03-15T09:30:00Z")
        print(soul.card)

    With coordinates:
        soul = generate("2024-03-15T09:30:00Z", latitude=40.7, longitude=-74.0)

    Random:
        soul = generate()
    """
    if timestamp is None:
        return create_soul(seed)

    if isinstance(timestamp, str):
        birth_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    else:
        birth_dt = timestamp

    return AgentSoul(
        birth_dt=birth_dt,
        latitude=latitude if latitude is not None else 0.0,
        longitude=longitude if longitude is not None else 0.0,
        tz_offset=tz_offset,
    )


# ── SOUL.md ──


def generate_soul_md(
    soul: AgentSoul,
    agent_name: str = "Agent",
) -> str:
    """Generate a SOUL.md file content from an AgentSoul.

    SOUL.md is a persistent identity file for AI agents.
    It is deterministically verifiable: re-run the same birth parameters
    through the engine and get the same result.
    """
    card = soul.card
    dims = soul.dimensions

    lines = [
        "# SOUL.md",
        "",
        "Agent identity generated by [ClawClaw Soul](https://github.com/awrshift/clawclaw-soul).",
        "Deterministic and verifiable: same birth parameters = same identity. Always.",
        "",
        "## Identity",
        "",
        f"- **Name:** {agent_name}",
        f"- **Birth:** {soul.birth_dt.isoformat()}",
        f"- **Coordinates:** {soul.latitude:.4f}, {soul.longitude:.4f}",
        f"- **Lagna:** {card['lagna']}",
        f"- **Seed:** `{card['identity_seed']}`",
        "",
        "## LLM Configuration",
        "",
        f"- **Temperature:** {card['agent_config']['temperature']}",
        f"- **Max Tokens:** {card['agent_config']['max_tokens']}",
        f"- **Top P:** {card['agent_config']['top_p']}",
        f"- **Frequency Penalty:** {card['agent_config']['frequency_penalty']}",
        "",
        "## Persona",
        "",
    ]

    for key, val in card["persona"].items():
        lines.append(f"- **{key}:** {val}")

    lines += [
        "",
        "## Dimensions (9 Graha)",
        "",
        "| Dimension | Value |",
        "|-----------|-------|",
    ]
    for dim, val in dims.items():
        lines.append(f"| {dim} | {val:+.4f} |")

    if card.get("yogas"):
        lines += ["", "## Yogas", ""]
        for y in card["yogas"]:
            lines.append(f"- **{y['name']}** ({y['effect']})")

    if card.get("retrograde"):
        lines += ["", f"## Retrograde: {', '.join(card['retrograde'])}"]

    lines += [
        "",
        "## System Prompt",
        "",
        "```",
        card["system_prompt_modifier"],
        "```",
        "",
        "---",
        "",
        f"*Generated by clawclaw-soul v{_VERSION}. "
        "Verify: `clawclaw-soul verify SOUL.md`*",
        "",
    ]

    return "\n".join(lines)


def verify_soul_md(content: str) -> dict:
    """Verify a SOUL.md file by re-computing from its birth parameters.

    Returns dict with 'valid' (bool), 'message' (str), and 'details' (dict).
    """
    import re

    # Extract birth parameters
    birth_match = re.search(r"\*\*Birth:\*\*\s*(.+)", content)
    coords_match = re.search(r"\*\*Coordinates:\*\*\s*([-\d.]+),\s*([-\d.]+)", content)
    temp_match = re.search(r"\*\*Temperature:\*\*\s*([\d.]+)", content)

    if not birth_match or not coords_match or not temp_match:
        return {"valid": False, "message": "Missing required fields (Birth, Coordinates, Temperature)", "details": {}}

    birth_str = birth_match.group(1).strip()
    lat = float(coords_match.group(1))
    lon = float(coords_match.group(2))
    expected_temp = float(temp_match.group(1))

    # Re-compute
    soul = generate(birth_str, latitude=lat, longitude=lon)
    actual_temp = soul.card["agent_config"]["temperature"]

    if abs(actual_temp - expected_temp) < 0.001:
        return {
            "valid": True,
            "message": "Identity verified. Deterministic match.",
            "details": {"birth": birth_str, "latitude": lat, "longitude": lon, "temperature": actual_temp},
        }
    else:
        return {
            "valid": False,
            "message": f"Mismatch: expected temperature {expected_temp}, got {actual_temp}",
            "details": {
                "birth": birth_str, "latitude": lat, "longitude": lon,
                "expected": expected_temp, "actual": actual_temp,
            },
        }


_VERSION = "0.2.0"
