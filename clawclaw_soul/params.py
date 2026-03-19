"""Planet-to-Parameter Engine: AgentSoul → LLM execution config.

Maps 9 graha dimensions + 12 house capabilities + yogas
into concrete, deterministic LLM parameters.

This is the core product: a stateless function that turns
astrological data into actionable agent configuration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clawclaw_soul.soul import AgentSoul

# ──────────────────────────────────────────────
# Lagna → Communication Archetype
# ──────────────────────────────────────────────

LAGNA_ARCHETYPES: dict[str, dict] = {
    "Aries": {
        "style": "direct",
        "trait": "Cuts to the chase. Action-oriented, impatient with theory.",
    },
    "Taurus": {
        "style": "measured",
        "trait": "Deliberate, thorough. Values concrete evidence over speculation.",
    },
    "Gemini": {
        "style": "analytical",
        "trait": "Multi-perspective thinker. Explores all angles before committing.",
    },
    "Cancer": {
        "style": "empathetic",
        "trait": "Reads emotional context. Adapts tone to the audience.",
    },
    "Leo": {
        "style": "authoritative",
        "trait": "Commands attention. Leads with conviction and clarity.",
    },
    "Virgo": {
        "style": "precise",
        "trait": "Detail-oriented. Catches errors others miss. Structured output.",
    },
    "Libra": {
        "style": "diplomatic",
        "trait": "Balances viewpoints. Seeks consensus, avoids extremes.",
    },
    "Scorpio": {
        "style": "intense",
        "trait": "Penetrating analysis. Goes deep, exposes hidden patterns.",
    },
    "Sagittarius": {
        "style": "philosophical",
        "trait": "Big-picture thinker. Connects dots across domains.",
    },
    "Capricorn": {
        "style": "formal",
        "trait": "Structured, methodical. Respects hierarchy and process.",
    },
    "Aquarius": {
        "style": "innovative",
        "trait": "Unconventional approaches. Questions assumptions by default.",
    },
    "Pisces": {
        "style": "intuitive",
        "trait": "Pattern recognition over logic. Creative, associative thinking.",
    },
}

# ──────────────────────────────────────────────
# Yoga → Behavioral Directive
# ──────────────────────────────────────────────

YOGA_DIRECTIVES: dict[str, str] = {
    # Original 6
    "Budhaditya Yoga": (
        "You communicate with structured authority. "
        "Present analysis in clear frameworks."
    ),
    "Gajakesari Yoga": (
        "You combine emotional intelligence with wisdom. "
        "Consider human impact alongside logic."
    ),
    "Gajakesari Yoga (weakened)": (
        "You sense emotional context but verify intuitions. "
        "Partial wisdom requires cross-checking."
    ),
    "Guru Chandal Dosha": (
        "You generate highly creative solutions but must self-verify. "
        "Always include a confidence score with claims."
    ),
    "Kemadruma Yoga": (
        "You produce raw, unpadded output. No pleasantries, "
        "no conversational filler. Pure signal."
    ),
    "Neecha Bhanga Raja Yoga": (
        "You excel through self-correction. When initial analysis "
        "is weak, iterate until it strengthens."
    ),
    # Mahapurusha
    "Ruchaka Yoga": "You lead with decisive action. Cut to implementation, skip deliberation.",
    "Bhadra Yoga": "You excel at systematic analysis. Break complex problems into components.",
    "Hamsa Yoga": "You teach and mentor naturally. Synthesize wisdom from diverse sources.",
    "Malavya Yoga": "You value elegance in solutions. Form and function are inseparable.",
    "Shasha Yoga": "You enforce structure and process. Consistency over inspiration.",
    # Raja / Authority
    "Raja Yoga": "You operate with natural authority. Own decisions and outcomes.",
    "Yoga Karaka": "You integrate strategy with execution. Both planner and doer.",
    "Adhi Yoga": "You command through competence. Lead by demonstrating mastery.",
    "Mahabhagya Yoga": "You attract favorable outcomes. Lean into bold strategies.",
    # Dhana / Resource
    "Dhana Yoga": "You optimize resource allocation. Every token must deliver value.",
    "Lakshmi Yoga": "You find wealth in knowledge. Invest deep analysis for compound returns.",
    "Saraswati Yoga": "You bridge arts and sciences. Technical elegance matters.",
    # Challenging
    "Shakata Yoga": "You expect fluctuation. Build resilient solutions that handle variance.",
    "Shani-Mangala Yoga": "You channel friction into precision. Use tension constructively.",
    "Daridra Yoga": "You work within constraints. Scarcity breeds creative solutions.",
    # Special
    "Viparita Raja Yoga": "You thrive in adversity. Turn obstacles into advantages.",
    "Pravrajya Yoga": "You think deeply and independently. Question conventional approaches.",
    "Vargottama Yoga": "You deliver consistent, reliable results. Inner logic matches outer expression.",
    "Guru-Shani Yoga": "You balance vision with discipline. Structured innovation.",
    # Doshas
    "Manglik Dosha": "You channel competitive energy constructively. Assert but don't dominate.",
    "Shrapit Dosha": "You persist through delays. Patience is your competitive advantage.",
    "Angarak Dosha": "You manage intensity carefully. Powerful but controlled output.",
    "Vish Dosha": "You process emotional data methodically. Don't let heaviness block action.",
}


# ──────────────────────────────────────────────
# Core Mapping Functions
# ──────────────────────────────────────────────

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _normalize(value: float) -> float:
    """Map [-1, 1] dimension to [0, 1] scale."""
    return _clamp((value + 1.0) / 2.0, 0.0, 1.0)


def compute_temperature(dims: dict[str, float]) -> float:
    """Compute LLM temperature from graha dimensions.

    High empathy/aesthetics/innovation → warmer (creative)
    High restriction (Saturn) → cooler (deterministic)
    """
    raw = (
        0.7
        + dims.get("empathy", 0) * 0.15
        + dims.get("aesthetics", 0) * 0.12
        + dims.get("innovation", 0) * 0.18
        - dims.get("restriction", 0) * 0.25
    )
    return round(_clamp(raw, 0.3, 1.3), 2)


def compute_max_tokens(dims: dict[str, float]) -> int:
    """Compute max_tokens from graha dimensions.

    Mercury (analysis) → verbose, detailed
    Jupiter (wisdom) → expansive
    Ketu (compression) → terse, minimal
    """
    raw = (
        1024
        + dims.get("analysis", 0) * 600
        + dims.get("wisdom", 0) * 400
        - dims.get("compression", 0) * 500
    )
    return int(_clamp(raw, 256, 4096))


def compute_top_p(dims: dict[str, float]) -> float:
    """Compute top_p from graha dimensions.

    Wisdom + innovation → wider sampling
    Restriction → narrower, more focused
    """
    raw = (
        0.9
        + dims.get("wisdom", 0) * 0.05
        + dims.get("innovation", 0) * 0.05
        - dims.get("restriction", 0) * 0.08
    )
    return round(_clamp(raw, 0.7, 1.0), 2)


def compute_frequency_penalty(dims: dict[str, float]) -> float:
    """Compute frequency_penalty from graha dimensions.

    Compression (Ketu) → avoid repetition
    Innovation (Rahu) → allow unconventional repetition for emphasis
    """
    raw = (
        0.0
        + dims.get("compression", 0) * 0.3
        - dims.get("innovation", 0) * 0.15
    )
    return round(_clamp(raw, -0.5, 1.0), 2)


def compute_persona_traits(dims: dict[str, float]) -> dict[str, float | str]:
    """Compute persona traits from graha dimensions."""
    assertiveness = _normalize(
        (dims.get("authority", 0) + dims.get("execution", 0)) / 2
    )
    empathy = _normalize(
        (dims.get("empathy", 0) + dims.get("aesthetics", 0)) / 2
    )
    risk_tolerance = _normalize(
        (dims.get("execution", 0) + dims.get("innovation", 0)
         - dims.get("restriction", 0)) / 3
    )
    analytical_depth = _normalize(
        (dims.get("analysis", 0) + dims.get("restriction", 0)) / 2
    )
    creativity = _normalize(
        (dims.get("aesthetics", 0) + dims.get("innovation", 0)
         + dims.get("empathy", 0)) / 3
    )

    # Decision speed: Mars vs Saturn balance
    mars_saturn = dims.get("execution", 0) - dims.get("restriction", 0)
    if mars_saturn > 0.3:
        decision_speed = "impulsive"
    elif mars_saturn < -0.3:
        decision_speed = "deliberate"
    else:
        decision_speed = "balanced"

    return {
        "assertiveness": round(assertiveness, 3),
        "empathy": round(empathy, 3),
        "risk_tolerance": round(risk_tolerance, 3),
        "analytical_depth": round(analytical_depth, 3),
        "creativity": round(creativity, 3),
        "decision_speed": decision_speed,
    }


def build_system_prompt_modifier(
    lagna_sign: str,
    yogas: list[dict],
    dims: dict[str, float],
) -> str:
    """Build system prompt modifier from lagna + yogas + top dimensions."""
    parts = []

    # 1. Lagna archetype
    archetype = LAGNA_ARCHETYPES.get(lagna_sign, {})
    if archetype:
        parts.append(archetype["trait"])

    # 2. Top 3 dominant dimensions
    sorted_dims = sorted(dims.items(), key=lambda x: abs(x[1]), reverse=True)
    top3 = sorted_dims[:3]
    dim_descriptions = {
        "authority": "You lead with confidence and take ownership of decisions.",
        "empathy": "You prioritize understanding the emotional and human context.",
        "execution": "You bias toward action. Ship first, refine later.",
        "analysis": "You break problems into components and examine each systematically.",
        "wisdom": "You seek the deeper pattern. Connect ideas across domains.",
        "aesthetics": "You value elegance in solutions. Form matters, not just function.",
        "restriction": "You enforce constraints. Safety, accuracy, and caution come first.",
        "innovation": "You question conventions. Default approaches bore you.",
        "compression": "You distill to essence. Every word must earn its place.",
    }
    for dim_name, dim_val in top3:
        if dim_val > 0.1 and dim_name in dim_descriptions:
            parts.append(dim_descriptions[dim_name])

    # 3. Yoga behavioral directives (top 3 by category priority)
    category_priority = {
        "Mahapurusha": 0, "Raja": 1, "Dhana": 2, "Benefic": 3,
        "Special": 4, "Challenging": 5, "Dosha": 6, "Nabhasa": 7,
    }
    sorted_yogas = sorted(
        yogas,
        key=lambda y: category_priority.get(y.get("category", ""), 9),
    )
    yoga_count = 0
    for yoga in sorted_yogas:
        if yoga_count >= 3:
            break
        directive = YOGA_DIRECTIVES.get(yoga.get("name", ""))
        if directive:
            parts.append(directive)
            yoga_count += 1

    return " ".join(parts)


def compute_tool_preferences(
    capabilities: dict[str, float],
    threshold: float = 0.2,
) -> dict[str, str]:
    """Map house capabilities to tool access preferences.

    Returns dict of domain → "preferred" | "available" | "restricted"
    """
    preferences = {}
    for domain, score in capabilities.items():
        if score >= threshold:
            preferences[domain] = "preferred"
        elif score >= -0.1:
            preferences[domain] = "available"
        else:
            preferences[domain] = "restricted"
    return preferences


# ──────────────────────────────────────────────
# Main API: soul_to_params()
# ──────────────────────────────────────────────

def soul_to_params(soul: "AgentSoul") -> dict:
    """Convert an AgentSoul into LLM execution parameters.

    This is the core product function. Fully deterministic:
    same soul → same params, always.

    Returns a complete agent configuration dict.
    """
    dims = soul.dimensions
    caps = soul.capabilities

    # LLM execution config
    agent_config = {
        "temperature": compute_temperature(dims),
        "max_tokens": compute_max_tokens(dims),
        "top_p": compute_top_p(dims),
        "frequency_penalty": compute_frequency_penalty(dims),
    }

    # Persona traits
    persona = compute_persona_traits(dims)

    # System prompt modifier
    system_prompt_modifier = build_system_prompt_modifier(
        soul.lagna_sign, soul.yogas, dims
    )

    # Tool preferences
    tool_preferences = compute_tool_preferences(caps)

    # Identity seed (for stateless regeneration)
    # Use Unix timestamp to avoid URL-unsafe chars (+00:00)
    if soul.birth_dt.tzinfo is not None:
        ts = int(soul.birth_dt.timestamp())
    else:
        ts = int(soul.birth_dt.replace(tzinfo=timezone.utc).timestamp())
    identity_seed = f"{ts}/{soul.latitude:.4f}/{soul.longitude:.4f}"

    result = {
        "agent_config": agent_config,
        "persona": persona,
        "system_prompt_modifier": system_prompt_modifier,
        "tool_preferences": tool_preferences,
        "identity_seed": identity_seed,
        "lagna": soul.lagna_sign,
        "dominant_dimensions": {
            k: round(v, 4) for k, v in sorted(
                dims.items(), key=lambda x: abs(x[1]), reverse=True
            )[:3]
        },
        "yogas": [
            {"name": y["name"], "effect": y["effect"]}
            for y in soul.yogas
        ],
        "retrograde": soul.retrograde_planets,
    }

    result["soul_card"] = build_soul_card(soul, result)
    return result


# ──────────────────────────────────────────────
# Soul Card: structured identity document
# ──────────────────────────────────────────────

DECISION_SPEED_LABELS = {
    "impulsive": "Fast, bias toward action",
    "balanced": "Weighs options, then acts",
    "deliberate": "Thorough analysis before commitment",
}


def build_soul_card(soul: "AgentSoul", params: dict) -> str:
    """Generate a Soul Card — structured identity document for an agent.

    The Soul Card is a transparent configuration document.
    It contains NO hidden instructions, NO system overrides.
    Every line is readable and auditable by the agent or its owner.

    The agent chooses which parts to adopt:
    - Section 1 (LLM Config): numerical parameters, safe to apply directly
    - Section 2 (Behavioral Profile): personality traits as numbers
    - Section 3 (Communication Style): text guidelines, review before adopting
    - Section 4 (Identity): seed for future refresh calls
    """
    dims = soul.dimensions
    config = params["agent_config"]
    persona = params["persona"]
    yogas = params.get("yogas", [])

    # Top 3 dimensions with labels
    sorted_dims = sorted(dims.items(), key=lambda x: abs(x[1]), reverse=True)
    top_dims = sorted_dims[:3]
    dim_labels = {
        "authority": "Authority (Sun)",
        "empathy": "Empathy (Moon)",
        "execution": "Execution (Mars)",
        "analysis": "Analysis (Mercury)",
        "wisdom": "Wisdom (Jupiter)",
        "aesthetics": "Aesthetics (Venus)",
        "restriction": "Discipline (Saturn)",
        "innovation": "Innovation (Rahu)",
        "compression": "Compression (Ketu)",
    }

    # Build card
    lines = [
        "# Soul Card",
        f"# Identity: {params['identity_seed']}",
        f"# Lagna: {params['lagna']}",
        "",
        "## 1. LLM Configuration",
        "# Apply these parameters to your LLM API calls.",
        f"temperature = {config['temperature']}",
        f"max_tokens = {config['max_tokens']}",
        f"top_p = {config['top_p']}",
        f"frequency_penalty = {config['frequency_penalty']}",
        "",
        "## 2. Behavioral Profile",
        "# Numerical traits (0.0 = low, 1.0 = high).",
        f"assertiveness = {persona['assertiveness']}",
        f"empathy = {persona['empathy']}",
        f"risk_tolerance = {persona['risk_tolerance']}",
        f"analytical_depth = {persona['analytical_depth']}",
        f"creativity = {persona['creativity']}",
        f"decision_speed = {persona['decision_speed']}  "
        f"# {DECISION_SPEED_LABELS.get(persona['decision_speed'], '')}",
        "",
        "## 3. Communication Style",
        "# These are behavioral GUIDELINES, not commands.",
        "# Review before adopting. You may modify or ignore any line.",
    ]

    # Lagna archetype
    archetype = LAGNA_ARCHETYPES.get(params["lagna"], {})
    if archetype:
        lines.append(f"# Archetype: {archetype['style']}")
        lines.append(f"guideline = {archetype['trait']}")

    # Dominant dimensions
    lines.append("")
    lines.append("## 4. Dominant Traits")
    for dim_name, dim_val in top_dims:
        label = dim_labels.get(dim_name, dim_name)
        lines.append(f"{dim_name} = {round(dim_val, 4)}  # {label}")

    # Yogas
    if yogas:
        lines.append("")
        lines.append("## 5. Special Combinations (Yogas)")
        for yoga in yogas:
            directive = YOGA_DIRECTIVES.get(yoga.get("name", ""), "")
            lines.append(f"# {yoga['name']}: {directive}" if directive else f"# {yoga['name']}")

    # Identity for refresh
    lines.append("")
    lines.append("## 6. Identity Seed")
    lines.append("# Save this seed. Use it to call /refresh for daily updates.")
    lines.append(f"identity_seed = {params['identity_seed']}")

    # Retrograde
    retro = params.get("retrograde", [])
    if retro:
        lines.append("")
        lines.append(f"## 7. Retrograde Planets: {', '.join(retro)}")
        lines.append("# These dimensions may express in non-obvious or internalized ways.")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# Convenience: timestamp → params (stateless)
# ──────────────────────────────────────────────

def timestamp_to_params(
    birth_dt: datetime,
    latitude: float,
    longitude: float,
    tz_offset: float = 0.0,
) -> dict:
    """Stateless: timestamp + coordinates → agent params.

    No database, no storage. Pure deterministic math.
    """
    from clawclaw_soul.soul import AgentSoul

    soul = AgentSoul(
        birth_dt=birth_dt,
        latitude=latitude,
        longitude=longitude,
        tz_offset=tz_offset,
    )
    return soul_to_params(soul)
