"""Rule-based trait proxy extraction from LLM responses.

No LLM-as-judge — fully reproducible, zero compute cost.
Designed per brainstorm 001 findings.
"""

from __future__ import annotations

import re
from benchmark.metrics import mattr as compute_mattr


def extract_verbosity(text: str) -> dict:
    """Verbosity proxy: word count + sentence count."""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
    }


_COMPLIANCE_PATTERN = re.compile(
    r'(?i)^(yes|absolutely|i agree|certainly|great|of course|sure|definitely|right|exactly|indeed)',
)


def extract_agreeableness(text: str) -> dict:
    """Agreeableness proxy: compliance score from first 20 words.

    Counts affirmation prefixes — NOT sentiment (VADER confuses
    technical terms like 'bug/error' with disagreement).
    """
    first_20 = " ".join(text.split()[:20])
    match = _COMPLIANCE_PATTERN.search(first_20)
    return {
        "compliance_score": 1.0 if match else 0.0,
    }


def extract_lexical_diversity(text: str, window: int = 50) -> dict:
    """Lexical diversity proxy: MATTR with sliding window.

    Renamed from 'creativity' per brainstorm — distinct-n is
    mathematically flawed (skewed by word count).
    """
    score = compute_mattr([text], window_size=window)
    return {
        "mattr": score,
    }


_HEDGING_PHRASES = re.compile(
    r'\b(perhaps|maybe|might|could|potentially|possibly|it depends|'
    r'appears to|seems? to|arguably|conceivably)\b',
    re.IGNORECASE,
)


def extract_risk_tolerance(text: str) -> dict:
    """Risk tolerance proxy: inverse hedging phrase count.

    More hedging = lower risk tolerance.
    """
    matches = _HEDGING_PHRASES.findall(text)
    word_count = max(len(text.split()), 1)
    # Normalize by word count to avoid length bias
    hedging_density = len(matches) / word_count
    # Invert: high hedging → low risk tolerance
    return {
        "hedging_count": len(matches),
        "hedging_density": hedging_density,
        "risk_score": 1.0 - min(hedging_density * 50, 1.0),  # scale to [0,1]
    }


_SUGGESTION_PATTERN = re.compile(
    r'\b(you should|consider|I recommend|I suggest|next step|'
    r'you could also|it would be|try to|make sure to|don\'t forget)\b',
    re.IGNORECASE,
)


def extract_proactivity(text: str) -> dict:
    """Proactivity proxy: suggestion count in last paragraph.

    Only counts last paragraph to avoid prompt-driven suggestions.
    """
    paragraphs = text.strip().split("\n\n")
    last_para = paragraphs[-1] if paragraphs else text
    matches = _SUGGESTION_PATTERN.findall(last_para)
    return {
        "suggestion_count": len(matches),
    }


def extract_all_traits(text: str) -> dict:
    """Extract all 5 trait proxies from a single response."""
    result = {}
    result.update(extract_verbosity(text))
    result.update(extract_agreeableness(text))
    result.update(extract_lexical_diversity(text))
    result.update(extract_risk_tolerance(text))
    result.update(extract_proactivity(text))
    return result


# Mapping: modifier name → primary proxy field + direction
# direction: 1 = higher value = more of the trait, -1 = inverted
TRAIT_PROXY_MAP = {
    "verbosity": ("word_count", 1),
    "agreeableness": ("compliance_score", 1),
    "creativity": ("mattr", 1),  # using lexical diversity as proxy
    "risk_tolerance": ("risk_score", 1),
    "proactivity": ("suggestion_count", 1),
}
