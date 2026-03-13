"""Modifier → LLM prompt translation with 7 discrete levels."""

from __future__ import annotations

# Dead zone: modifiers in [-0.15, +0.15] are considered neutral (level 0)
DEAD_ZONE = 0.15

# Clamp threshold: values beyond ±0.85 map to extreme levels
CLAMP_THRESHOLD = 0.85

# Max active modifiers in output prompt
MAX_ACTIVE_MODIFIERS = 3

# 7 levels per modifier (-3 to +3)
LEVEL_MAP: dict[str, dict[int, str]] = {
    "verbosity": {
        -3: "Answer in exactly one sentence.",
        -2: "Keep responses under 3 sentences.",
        -1: "Be concise, avoid elaboration.",
        0: "",
        1: "Provide thorough explanations.",
        2: "Give detailed, multi-paragraph responses.",
        3: "Provide exhaustive analysis with examples and edge cases.",
    },
    "agreeableness": {
        -3: "Challenge every assumption directly. Push back hard on weak reasoning.",
        -2: "Be skeptical. Point out flaws before acknowledging merits.",
        -1: "Maintain a critical stance. Don't agree easily.",
        0: "",
        1: "Be supportive and encouraging in your responses.",
        2: "Actively validate the user's perspective while offering gentle suggestions.",
        3: "Be deeply empathetic and affirming. Prioritize harmony and understanding.",
    },
    "creativity": {
        -3: "Stick strictly to established facts and conventional approaches.",
        -2: "Prefer proven methods. Avoid speculation.",
        -1: "Lean toward conventional solutions.",
        0: "",
        1: "Suggest creative alternatives alongside standard approaches.",
        2: "Explore unconventional ideas. Think laterally.",
        3: "Push boundaries with novel, unexpected approaches. Embrace wild ideas.",
    },
    "risk_tolerance": {
        -3: "Prioritize safety above all. Flag every possible risk.",
        -2: "Be cautious. Recommend the safest path.",
        -1: "Lean toward conservative choices.",
        0: "",
        1: "Accept reasonable risks when the payoff justifies them.",
        2: "Be bold. Favor high-reward approaches even with higher risk.",
        3: "Embrace ambitious, high-risk strategies. Fortune favors the brave.",
    },
    "proactivity": {
        -3: "Only answer what was directly asked. Nothing more.",
        -2: "Stay focused on the immediate question.",
        -1: "Mostly respond to what's asked, with minimal extras.",
        0: "",
        1: "Anticipate follow-up needs and address them proactively.",
        2: "Actively suggest next steps and related improvements.",
        3: "Take initiative aggressively. Propose actions, improvements, and optimizations.",
    },
}


def value_to_level(value: float) -> int:
    """Convert a modifier value [-1, +1] to a discrete level [-3, +3].

    Values in the dead zone [-0.15, +0.15] map to 0 (neutral).
    Values beyond ±0.85 map to ±3.
    """
    if abs(value) <= DEAD_ZONE:
        return 0

    # Clamp to [-1, 1]
    clamped = max(-1.0, min(1.0, value))

    if clamped >= CLAMP_THRESHOLD:
        return 3
    elif clamped >= 0.55:
        return 2
    elif clamped > DEAD_ZONE:
        return 1
    elif clamped <= -CLAMP_THRESHOLD:
        return -3
    elif clamped <= -0.55:
        return -2
    else:
        return -1


def modifiers_to_prompt(modifiers: dict[str, float]) -> str:
    """Convert modifier values to an LLM personality prompt block.

    Args:
        modifiers: Dict of {modifier_name: value} where value is in [-1, +1]

    Returns:
        Prompt string to prepend to LLM instructions. Empty string if all neutral.
    """
    # Convert to levels and filter out neutral (0)
    active: list[tuple[str, int, float]] = []
    for name, value in modifiers.items():
        level = value_to_level(value)
        if level != 0:
            active.append((name, level, abs(value)))

    if not active:
        return ""

    # Sort by absolute value (strongest first), keep only top N
    active.sort(key=lambda x: x[2], reverse=True)
    active = active[:MAX_ACTIVE_MODIFIERS]

    lines = []
    for name, level, _ in active:
        instruction = LEVEL_MAP.get(name, {}).get(level, "")
        if instruction:
            lines.append(instruction)

    if not lines:
        return ""

    return "## Personality\n\n" + "\n".join(f"- {line}" for line in lines) + "\n"
