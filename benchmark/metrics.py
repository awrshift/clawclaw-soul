"""PVI (Personality Variance Index) computation.

PVI_day = 0.4 * mean_cosine_distance + 0.3 * (1 - selfBLEU) + 0.3 * MATTR
"""

from __future__ import annotations

import re
from collections import Counter

import numpy as np


def cosine_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine distance between two vectors."""
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm == 0:
        return 1.0
    return 1.0 - dot / norm


def mean_cosine_distance(embeddings: list[np.ndarray]) -> float:
    """Compute mean pairwise cosine distance across a set of embeddings.

    Args:
        embeddings: List of embedding vectors (one per response)

    Returns:
        Mean cosine distance in [0, 1]. Higher = more diverse.
    """
    if len(embeddings) < 2:
        return 0.0

    distances = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            distances.append(cosine_distance(embeddings[i], embeddings[j]))

    return float(np.mean(distances))


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r'\b\w+\b', text.lower())


def _ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    """Extract n-grams from token list."""
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def self_bleu(texts: list[str], max_n: int = 4) -> float:
    """Compute self-BLEU score across a set of texts.

    Self-BLEU measures how similar texts are to each other.
    Lower self-BLEU = more diverse.

    Args:
        texts: List of response texts
        max_n: Maximum n-gram order

    Returns:
        Self-BLEU score in [0, 1]. Lower = more diverse.
    """
    if len(texts) < 2:
        return 0.0

    tokenized = [_tokenize(t) for t in texts]
    scores = []

    for i, hypothesis in enumerate(tokenized):
        if len(hypothesis) == 0:
            continue

        # All other texts are references
        references = [t for j, t in enumerate(tokenized) if j != i and len(t) > 0]
        if not references:
            continue

        # Compute modified precision for each n-gram order
        precisions = []
        for n in range(1, max_n + 1):
            hyp_ngrams = _ngrams(hypothesis, n)
            if not hyp_ngrams:
                break

            hyp_counts = Counter(hyp_ngrams)

            # Max counts from any single reference
            max_ref_counts: Counter = Counter()
            for ref in references:
                ref_counts = Counter(_ngrams(ref, n))
                for ng in hyp_counts:
                    max_ref_counts[ng] = max(max_ref_counts.get(ng, 0), ref_counts.get(ng, 0))

            # Clipped counts
            clipped = sum(min(hyp_counts[ng], max_ref_counts.get(ng, 0)) for ng in hyp_counts)
            total = sum(hyp_counts.values())

            if total == 0:
                break
            precisions.append(clipped / total)

        if precisions:
            # Geometric mean of precisions (BLEU formula without brevity penalty)
            log_avg = sum(np.log(max(p, 1e-10)) for p in precisions) / len(precisions)
            scores.append(np.exp(log_avg))

    return float(np.mean(scores)) if scores else 0.0


def mattr(texts: list[str], window_size: int = 50) -> float:
    """Compute Moving Average Type-Token Ratio across texts.

    MATTR measures lexical diversity. Higher = more diverse vocabulary.

    Args:
        texts: List of response texts
        window_size: Window size for MATTR computation

    Returns:
        MATTR score in [0, 1]. Higher = more diverse.
    """
    # Concatenate all tokens
    all_tokens = []
    for text in texts:
        all_tokens.extend(_tokenize(text))

    if len(all_tokens) < window_size:
        if len(all_tokens) == 0:
            return 0.0
        # Use full text as single window
        return len(set(all_tokens)) / len(all_tokens)

    # Sliding window TTR
    ttrs = []
    for i in range(len(all_tokens) - window_size + 1):
        window = all_tokens[i:i + window_size]
        ttr = len(set(window)) / window_size
        ttrs.append(ttr)

    return float(np.mean(ttrs))


def compute_pvi(
    embeddings: list[np.ndarray],
    texts: list[str],
    w_cosine: float = 0.4,
    w_bleu: float = 0.3,
    w_mattr: float = 0.3,
) -> dict:
    """Compute Personality Variance Index.

    PVI = w_cosine * mean_cosine_distance + w_bleu * (1 - selfBLEU) + w_mattr * MATTR

    Args:
        embeddings: Embedding vectors for each response
        texts: Raw response texts
        w_cosine: Weight for cosine distance component
        w_bleu: Weight for self-BLEU component
        w_mattr: Weight for MATTR component

    Returns:
        Dict with PVI score and component breakdown
    """
    mcd = mean_cosine_distance(embeddings)
    sb = self_bleu(texts)
    mt = mattr(texts)

    pvi = w_cosine * mcd + w_bleu * (1 - sb) + w_mattr * mt

    return {
        "pvi": pvi,
        "cosine_distance": mcd,
        "self_bleu": sb,
        "mattr": mt,
    }
