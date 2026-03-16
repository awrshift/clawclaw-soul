"""Zero-cost proxy metrics for CVB v3 (Brainstorm 004).

Measures structural properties of LLM output that structural constraints
should directly affect. No API calls, no embeddings — pure text analysis.

Metrics:
- word_count: total words
- hedge_density: fraction of hedging words (perhaps, might, could...)
- pronoun_ratio: first-person / second-person pronouns
- distinct_2: fraction of unique bigrams (vocabulary diversity)
"""

from __future__ import annotations

import re
from collections import Counter


HEDGE_WORDS = frozenset({
    "maybe", "perhaps", "possibly", "might", "could", "seem", "seems",
    "apparently", "arguably", "potentially", "likely", "unlikely",
    "suggest", "suggests", "consider", "tends", "tend",
})

FIRST_PERSON = frozenset({"i", "me", "my", "mine", "we", "us", "our", "ours"})
SECOND_PERSON = frozenset({"you", "your", "yours", "yourself"})


def compute_proxies(text: str) -> dict[str, float]:
    """Compute all proxy metrics for a single response.

    Returns dict with: word_count, hedge_density, pronoun_ratio, distinct_2,
    bullet_count, sentence_count.
    """
    words = text.lower().split()
    word_count = len(words)

    # Hedge density
    hedge_count = sum(1 for w in words if w.strip(".,;:!?()") in HEDGE_WORDS)
    hedge_density = hedge_count / max(word_count, 1)

    # Pronoun ratio (first / second person)
    first = sum(1 for w in words if w.strip(".,;:!?()") in FIRST_PERSON)
    second = sum(1 for w in words if w.strip(".,;:!?()") in SECOND_PERSON)
    pronoun_ratio = first / max(second, 1)

    # Distinct-2 (unique bigrams / total bigrams)
    if len(words) >= 2:
        bigrams = [(words[i], words[i + 1]) for i in range(len(words) - 1)]
        unique_bigrams = len(set(bigrams))
        distinct_2 = unique_bigrams / len(bigrams)
    else:
        distinct_2 = 0.0

    # Bullet/list detection (lines starting with - or number.)
    lines = text.strip().split("\n")
    bullet_count = sum(
        1 for line in lines
        if re.match(r"^\s*[-*•]\s", line) or re.match(r"^\s*\d+[.)]\s", line)
    )

    # Sentence count (rough: split on .!?)
    sentences = re.split(r"[.!?]+", text.strip())
    sentence_count = len([s for s in sentences if s.strip()])

    return {
        "word_count": float(word_count),
        "hedge_density": hedge_density,
        "pronoun_ratio": pronoun_ratio,
        "distinct_2": distinct_2,
        "bullet_count": float(bullet_count),
        "sentence_count": float(sentence_count),
    }


def compute_batch(texts: list[str]) -> list[dict[str, float]]:
    """Compute proxies for a batch of texts."""
    return [compute_proxies(t) for t in texts]
