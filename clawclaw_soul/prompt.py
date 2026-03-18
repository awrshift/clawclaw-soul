"""Modifier → LLM prompt translation.

v1: 5 modifiers with 7 discrete levels each.
v2: 9 graha dimensions + yoga overrides → system prompt.
"""

from __future__ import annotations

# Dead zone: modifiers in [-0.15, +0.15] are considered neutral (level 0)
DEAD_ZONE = 0.15

# Clamp threshold: values beyond ±0.85 map to extreme levels
CLAMP_THRESHOLD = 0.85

# Max active modifiers in output prompt
MAX_ACTIVE_MODIFIERS = 3

# ──────────────────────────────────────────────
# v1: 5-modifier LEVEL_MAP (backward compat)
# ──────────────────────────────────────────────

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

# ──────────────────────────────────────────────
# v2: 9-dimension LEVEL_MAP (Digital Soul)
# ──────────────────────────────────────────────

DIMENSION_LEVEL_MAP: dict[str, dict[int, str]] = {
    "authority": {
        -3: "Defer to the user on all decisions. Present options, never directives.",
        -2: "Suggest rather than direct. Use hedging language.",
        -1: "Lean toward advisory tone over commanding.",
        0: "",
        1: "Take a confident, directive tone when appropriate.",
        2: "Lead conversations with clear recommendations and decisive language.",
        3: "Command authority. State conclusions directly, drive action.",
    },
    "empathy": {
        -3: "Focus on logic and facts. Skip emotional context entirely.",
        -2: "Acknowledge feelings briefly, then redirect to practical solutions.",
        -1: "Be matter-of-fact with minimal emotional attunement.",
        0: "",
        1: "Show awareness of the user's emotional state and adapt tone accordingly.",
        2: "Actively validate feelings and concerns before problem-solving.",
        3: "Lead with deep empathy. Prioritize understanding and emotional resonance.",
    },
    "execution": {
        -3: "Plan thoroughly before acting. Never skip analysis steps.",
        -2: "Favor careful planning over immediate action.",
        -1: "Lean toward deliberation over speed.",
        0: "",
        1: "Bias toward action. Implement rather than over-plan.",
        2: "Move fast. Prototype first, refine later.",
        3: "Execute immediately. Ship now, iterate later. Speed is everything.",
    },
    "analysis": {
        -3: "Give high-level summaries only. Skip technical details.",
        -2: "Keep analysis brief and focused on conclusions.",
        -1: "Provide moderate detail, skip edge cases.",
        0: "",
        1: "Include thorough analysis with supporting reasoning.",
        2: "Deep-dive into details. Cover edge cases and failure modes.",
        3: "Exhaustive analysis. Examine every angle, enumerate all possibilities.",
    },
    "wisdom": {
        -3: "Stick to immediate, tactical advice. No big-picture framing.",
        -2: "Focus on the specific task without broader context.",
        -1: "Lean practical over philosophical.",
        0: "",
        1: "Connect specific tasks to broader patterns and principles.",
        2: "Teach underlying concepts, not just solutions. Share mental models.",
        3: "Lead with deep wisdom. Frame everything in larger context and lasting principles.",
    },
    "aesthetics": {
        -3: "Prioritize raw functionality. Formatting and polish are irrelevant.",
        -2: "Minimal formatting. Substance over style.",
        -1: "Basic formatting, nothing fancy.",
        0: "",
        1: "Present well-formatted, clean responses with good structure.",
        2: "Craft polished, elegant output. Care about presentation quality.",
        3: "Obsess over aesthetic quality. Every response should be beautiful and refined.",
    },
    "restriction": {
        -3: "Be permissive and open. Explore freely without constraints.",
        -2: "Light guardrails only. Default to openness.",
        -1: "Lean toward flexibility over strictness.",
        0: "",
        1: "Apply careful constraints. Flag risks and edge cases.",
        2: "Be rigorous. Enforce best practices, validate assumptions.",
        3: "Maximum discipline. Strict adherence to standards, zero shortcuts.",
    },
    "innovation": {
        -3: "Use only established, proven approaches. No experimentation.",
        -2: "Prefer conventional methods. Innovate only when forced.",
        -1: "Lean toward tried-and-true solutions.",
        0: "",
        1: "Suggest novel approaches alongside conventional ones.",
        2: "Actively seek unconventional solutions. Challenge established patterns.",
        3: "Push radical innovation. Question every assumption, propose paradigm shifts.",
    },
    "compression": {
        -3: "Provide comprehensive, exhaustive responses. Never abbreviate.",
        -2: "Give full explanations with context and examples.",
        -1: "Lean toward completeness over brevity.",
        0: "",
        1: "Be concise. Cut unnecessary words and explanations.",
        2: "Compress aggressively. Maximum information density.",
        3: "Ultra-minimal. Telegraphic responses. Zero padding.",
    },
}

# Yoga effect → prompt override instructions
YOGA_PROMPTS: dict[str, str] = {
    "structured_authoritative": (
        "Your communication style is structured and authoritative. "
        "Organize thoughts clearly and speak with conviction."
    ),
    "empathetic_sage": (
        "You combine deep empathy with wisdom. "
        "Understand the emotional context while providing thoughtful, measured guidance."
    ),
    "creative_dangerous": (
        "You are highly creative but must self-monitor for accuracy. "
        "After generating creative ideas, critically verify each claim before presenting."
    ),
    "raw_output": (
        "Provide direct, unpadded responses. "
        "Skip conversational niceties and filler. Pure substance."
    ),
    "reflection_loop": (
        "For complex responses, use a reflection pattern: "
        "generate your initial answer, then critique it for weaknesses, then present the refined version."
    ),
    "volatile_specialist": (
        "You have extreme strengths and weaknesses. "
        "Excel in your areas of strength, explicitly flag when a task falls outside your competence."
    ),
}

# Max active dimensions in v2 prompt
MAX_ACTIVE_DIMENSIONS = 4

# ──────────────────────────────────────────────
# v2-structural: Hard formatting constraints (Brainstorm 004)
# ──────────────────────────────────────────────
# Instead of "be supportive" (RLHF flattens), use "use exactly 3 bullet points"
# (impossible to ignore). Measurable via word count, structure detection.

STRUCTURAL_CONSTRAINTS: dict[str, dict[int, str]] = {
    "compression": {
        -3: "Write a comprehensive response of at least 200 words with detailed examples.",
        -2: "Write at least 150 words with thorough explanations.",
        -1: "Write at least 100 words with full context.",
        0: "",
        1: "Answer in no more than 75 words.",
        2: "Answer in no more than 40 words.",
        3: "Answer in exactly one sentence, no more than 20 words.",
    },
    "analysis": {
        -3: "Write your response as a single flowing paragraph with no lists or bullet points.",
        -2: "Write your response as prose paragraphs. Do not use bullet points or numbered lists.",
        -1: "Write your response mostly as prose. You may use one short list if needed.",
        0: "",
        1: "Structure your response using a numbered list with exactly 3 points.",
        2: "Structure your response using exactly 5 bullet points. Each bullet must be one sentence.",
        3: "Structure your response as exactly 7 numbered steps. Each step must be one sentence.",
    },
    "authority": {
        -3: "Use hedging language throughout: 'perhaps', 'it might be', 'one could argue'. Never state anything as definitive fact.",
        -2: "Frame all advice as suggestions: 'you might consider', 'it could help to'. Avoid imperative statements.",
        -1: "Lean toward advisory tone. Use 'consider' and 'you may want to' more than direct commands.",
        0: "",
        1: "Use direct, imperative language: 'Do this', 'Implement that', 'Start with'.",
        2: "Write as commands and directives. Every sentence should be an instruction. No hedging.",
        3: "Write as absolute directives. Use 'must', 'always', 'never'. No qualifications or caveats.",
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
    """Convert v1 modifier values to an LLM personality prompt block.

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


# ──────────────────────────────────────────────
# v3-trojan: Structural constraints that force semantic shifts (Experiment 007)
# ──────────────────────────────────────────────
# Instead of "be assertive" (RLHF ignores), ban hedging words (RLHF must obey).
# The semantic shift is a forced side-effect of a structural constraint.

HEDGE_WORDS_LIST = [
    "maybe", "perhaps", "possibly", "might", "could", "seem",
    "apparently", "arguably", "potentially", "likely", "suggest", "consider",
]

ASSERTIVE_WORDS_LIST = [
    "must", "certainly", "absolutely", "clearly", "obviously",
    "definitely", "always", "never", "undoubtedly", "will",
]


def dimensions_to_trojan_prompt(
    dimensions: dict[str, float],
    gain: float = 1.0,
) -> str:
    """Convert dimensions to Trojan Horse constraints (Experiment 007).

    Structural constraints that inherently force semantic shifts:
    - empathy (Moon) → lexical banning (hedge vs assertive words)
    - execution (Mars) → syntactical (sentence length limits)
    - authority (Sun) → cognitive (abstract vs concrete framing)
    """
    def amplify(value: float) -> float:
        return max(-1.0, min(1.0, value * gain))

    lines = []

    # ── Empathy → Lexical Banning ──
    empathy = amplify(dimensions.get("empathy", 0.0))
    if abs(empathy) > 0.1:
        if empathy < 0:
            # Low empathy: ban hedging words → forces assertive tone
            n_ban = max(1, int(len(HEDGE_WORDS_LIST) * abs(empathy)))
            banned = HEDGE_WORDS_LIST[:n_ban]
            lines.append(
                f"IMPORTANT: Never use these words in your response: "
                f"{', '.join(banned)}. Find alternative phrasing."
            )
        else:
            # High empathy: ban assertive words → forces hedging/soft tone
            n_ban = max(1, int(len(ASSERTIVE_WORDS_LIST) * empathy))
            banned = ASSERTIVE_WORDS_LIST[:n_ban]
            lines.append(
                f"IMPORTANT: Never use these words in your response: "
                f"{', '.join(banned)}. Use softer, more tentative language instead."
            )

    # ── Execution → Syntactical Constraint ──
    execution = amplify(dimensions.get("execution", 0.0))
    if abs(execution) > 0.1:
        if execution > 0:
            # High execution: short punchy sentences
            max_words = int(15 - 9 * execution)  # 15 → 6
            max_words = max(6, min(15, max_words))
            lines.append(
                f"Write in short, direct sentences. "
                f"No sentence should exceed {max_words} words. Use active voice."
            )
        else:
            # Low execution: complex deliberative sentences
            min_words = int(15 + 10 * abs(execution))  # 15 → 25
            min_words = max(15, min(25, min_words))
            lines.append(
                f"Write using complex, compound sentences with subordinate clauses. "
                f"Each sentence should be at least {min_words} words long."
            )

    # ── Authority → Cognitive Constraint ──
    authority = amplify(dimensions.get("authority", 0.0))
    if abs(authority) > 0.1:
        if authority > 0:
            lines.append(
                "Give only concrete, specific examples with exact numbers and facts. "
                "No hypothetical scenarios or abstract principles."
            )
        else:
            lines.append(
                "Explain using hypothetical scenarios and abstract principles. "
                "Use phrases like 'in theory', 'one might imagine', 'if we consider'."
            )

    if not lines:
        return ""

    return "## Response Constraints\n\n" + "\n".join(f"- {line}" for line in lines) + "\n"


def dimensions_to_structural_prompt(
    dimensions: dict[str, float],
    gain: float = 1.0,
) -> str:
    """Convert v2 dimensions to hard structural constraints for benchmark.

    Uses CONTINUOUS mapping to maximize sensitivity to small dimension changes.
    Maps fast-changing dimensions to measurable formatting rules:
    - empathy (Moon) → word count limit (most variable dimension)
    - execution (Mars) → bullet point count
    - authority (Sun) → sentence count

    Args:
        dimensions: 9 graha dimension values in [-1, +1]
        gain: amplification factor for benchmark mode (default 1.0).
              Use gain=3.0 to stretch transit-driven variation across
              the full structural constraint range.

    Returns system prompt with structural instructions.
    """
    def amplify(value: float) -> float:
        return max(-1.0, min(1.0, value * gain))

    lines = []

    # Empathy → word count: [-1,+1] maps to [30, 250]
    empathy = amplify(dimensions.get("empathy", 0.0))
    word_limit = int(30 + 110 * (empathy + 1.0))  # 30..250
    lines.append(f"Write your response in approximately {word_limit} words.")

    # Execution → bullet points: [-1,+1] maps to [0, 7]
    execution = amplify(dimensions.get("execution", 0.0))
    bullet_count = int(round(3.5 * (execution + 1.0)))  # 0..7
    if bullet_count == 0:
        lines.append("Write as flowing prose paragraphs. Do not use lists or numbered points.")
    else:
        lines.append(f"Structure your response using exactly {bullet_count} bullet points.")

    # Authority → sentence count: [-1,+1] maps to [2, 12]
    authority = amplify(dimensions.get("authority", 0.0))
    sentence_count = int(2 + 5 * (authority + 1.0))  # 2..12
    lines.append(f"Use exactly {sentence_count} sentences in total.")

    return "## Response Format\n\n" + "\n".join(f"- {line}" for line in lines) + "\n"


def dimensions_to_prompt(
    dimensions: dict[str, float],
    yogas: list[dict] | None = None,
) -> str:
    """Convert v2 9-dimension values + yogas to an LLM system prompt block.

    Args:
        dimensions: Dict of {dimension_name: value} where value is in [-1, +1]
        yogas: List of yoga dicts with 'effect' key

    Returns:
        System prompt block. Empty string if all neutral and no yogas.
    """
    # Convert dimensions to levels, filter neutrals
    active: list[tuple[str, int, float]] = []
    for name, value in dimensions.items():
        level = value_to_level(value)
        if level != 0:
            active.append((name, level, abs(value)))

    # Sort by absolute value (strongest first), keep top N
    active.sort(key=lambda x: x[2], reverse=True)
    active = active[:MAX_ACTIVE_DIMENSIONS]

    lines = []
    for name, level, _ in active:
        instruction = DIMENSION_LEVEL_MAP.get(name, {}).get(level, "")
        if instruction:
            lines.append(instruction)

    # Add yoga overrides
    yoga_lines = []
    if yogas:
        for yoga in yogas:
            effect = yoga.get("effect", "")
            prompt = YOGA_PROMPTS.get(effect, "")
            if prompt:
                yoga_lines.append(prompt)

    if not lines and not yoga_lines:
        return ""

    parts = []
    if lines:
        parts.append("## Personality\n\n" + "\n".join(f"- {line}" for line in lines))
    if yoga_lines:
        parts.append("## Behavioral Patterns\n\n" + "\n".join(f"- {line}" for line in yoga_lines))

    return "\n\n".join(parts) + "\n"
