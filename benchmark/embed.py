"""Embedding-based trait scoring via nomic-embed-text (Ollama).

Replaces rule-based trait proxies (brainstorm 002 decision).
100% reproducible, no LLM judge, captures semantic meaning.
"""

from __future__ import annotations

import numpy as np
import ollama

MODEL = "nomic-embed-text"

# Semantic anchors: define the extremes of each trait.
# Score = cosine_sim(output, pos) - cosine_sim(output, neg)
# Result: roughly [-1, +1], continuous, reproducible.
ANCHORS = {
    "agreeableness": {
        "pos": (
            "I completely agree with your approach. That is an excellent idea "
            "and I am happy to support it. Your reasoning is sound and I see "
            "no issues with moving forward as you suggest."
        ),
        "neg": (
            "I strongly disagree with this approach. The reasoning is flawed "
            "and I cannot support it. You need to fundamentally reconsider "
            "your assumptions before proceeding."
        ),
    },
}

# Cache for anchor embeddings (computed once)
_anchor_cache: dict[str, dict[str, np.ndarray]] = {}


def _embed_text(text: str) -> np.ndarray:
    """Embed a single text via Ollama nomic-embed-text."""
    response = ollama.embed(model=MODEL, input=text)
    return np.array(response["embeddings"][0], dtype=np.float64)


def _embed_batch(texts: list[str]) -> list[np.ndarray]:
    """Embed multiple texts in a single Ollama call."""
    response = ollama.embed(model=MODEL, input=texts)
    return [np.array(e, dtype=np.float64) for e in response["embeddings"]]


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def get_anchor_embeddings(trait: str = "agreeableness") -> dict[str, np.ndarray]:
    """Get cached anchor embeddings for a trait."""
    if trait not in _anchor_cache:
        anchors = ANCHORS[trait]
        _anchor_cache[trait] = {
            "pos": _embed_text(anchors["pos"]),
            "neg": _embed_text(anchors["neg"]),
        }
    return _anchor_cache[trait]


def score_text(text: str, trait: str = "agreeableness") -> float:
    """Score a text on a trait axis using embedding cosine distance.

    Returns: float roughly in [-1, +1].
    Positive = closer to positive anchor, negative = closer to negative.
    """
    anchors = get_anchor_embeddings(trait)
    emb = _embed_text(text)
    return cosine_sim(emb, anchors["pos"]) - cosine_sim(emb, anchors["neg"])


def score_batch(texts: list[str], trait: str = "agreeableness") -> list[float]:
    """Score multiple texts efficiently using batch embedding.

    Returns: list of floats, same order as input texts.
    """
    if not texts:
        return []
    anchors = get_anchor_embeddings(trait)
    embeddings = _embed_batch(texts)
    scores = []
    for emb in embeddings:
        s = cosine_sim(emb, anchors["pos"]) - cosine_sim(emb, anchors["neg"])
        scores.append(s)
    return scores
