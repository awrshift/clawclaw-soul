"""Trojan Horse metrics for Experiment 007.

Measures semantic properties that lexical banning / syntactical constraints
directly affect. All zero-cost, no API calls.
"""

from __future__ import annotations

import re

# Same word lists as in prompt.py (keep in sync)
HEDGE_WORDS = frozenset({
    "maybe", "perhaps", "possibly", "might", "could", "seem",
    "apparently", "arguably", "potentially", "likely", "suggest", "consider",
})

ASSERTIVE_WORDS = frozenset({
    "must", "certainly", "absolutely", "clearly", "obviously",
    "definitely", "always", "never", "undoubtedly", "will",
})


def compute_trojan_metrics(text: str) -> dict[str, float]:
    """Compute all Trojan Horse semantic metrics.

    Returns:
        hedge_density: fraction of words that are hedging words
        assertive_density: fraction of words that are assertive words
        avg_sentence_length: mean words per sentence
        question_density: fraction of sentences that are questions
        sentence_vader: average sentence-level VADER compound (lazy import)
    """
    words = text.lower().split()
    word_count = len(words)
    clean_words = [w.strip(".,;:!?()\"'") for w in words]

    # Hedge density
    hedge_count = sum(1 for w in clean_words if w in HEDGE_WORDS)
    hedge_density = hedge_count / max(word_count, 1)

    # Assertive density
    assertive_count = sum(1 for w in clean_words if w in ASSERTIVE_WORDS)
    assertive_density = assertive_count / max(word_count, 1)

    # Sentence splitting
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s for s in sentences if len(s.split()) >= 2]
    n_sentences = max(len(sentences), 1)

    # Average sentence length
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_sentence_length = sum(sentence_lengths) / n_sentences

    # Question density
    questions = sum(1 for s in sentences if s.strip().endswith("?"))
    question_density = questions / n_sentences

    # Sentence-level VADER (lazy import)
    try:
        import nltk
        nltk.download("vader_lexicon", quiet=True)
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        vader_scores = [sia.polarity_scores(s)["compound"] for s in sentences if len(s.split()) >= 3]
        sentence_vader = float(sum(vader_scores) / max(len(vader_scores), 1))
    except ImportError:
        sentence_vader = 0.0

    return {
        "hedge_density": hedge_density,
        "assertive_density": assertive_density,
        "avg_sentence_length": avg_sentence_length,
        "question_density": question_density,
        "sentence_vader": sentence_vader,
        "word_count": float(word_count),
    }
