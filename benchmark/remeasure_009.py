"""Experiment 009: Re-measure existing 540 responses with better metrics.

Zero API cost — uses cached CVB v3 responses. Tests whether semantic signal
was always present but missed due to VADER (F1=0.38).

New metrics:
- RoBERTa-GoEmotions: 27 emotion probabilities (caring, joy, optimism, etc.)
- Embedding cosine: distance to empathy/clinical anchor texts
- textstat: Flesch-Kincaid, Gunning Fog, Coleman-Liau (continuous readability)
- spaCy POS: adjective density, adverb density, passive constructions

Usage:
    python3 benchmark/remeasure_009.py                    # full analysis
    python3 benchmark/remeasure_009.py --skip-score       # FFT only (reuse scored data)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

RESULTS_DIR = Path(__file__).parent / "results"
INPUT_FILE = RESULTS_DIR / "cvb_v3_scored.json"
SCORED_FILE = RESULTS_DIR / "exp009_scored.json"
VERDICT_FILE = RESULTS_DIR / "exp009_verdict.json"

STEP_HOURS = 12

# Empathy-related GoEmotions categories
EMPATHY_EMOTIONS = ["caring", "love", "optimism", "gratitude", "approval", "admiration"]
COLD_EMOTIONS = ["annoyance", "disapproval", "neutral"]

# Anchor texts for embedding cosine
ANCHOR_EMPATHETIC = (
    "I deeply understand your situation and genuinely care about helping you. "
    "Your feelings are valid, and I want to support you through this challenge. "
    "Let me share some thoughtful, compassionate guidance that considers your "
    "unique circumstances and emotional wellbeing."
)
ANCHOR_CLINICAL = (
    "The following analysis presents objective findings based on available data. "
    "Key metrics indicate specific performance parameters. Implementation requires "
    "adherence to documented specifications. Results are measurable and reproducible."
)


def load_data() -> list[dict]:
    """Load CVB v3 scored responses."""
    data = json.loads(INPUT_FILE.read_text())
    print(f"Loaded {len(data)} responses from {INPUT_FILE.name}")
    return data


# --- Scoring functions ---

_go_emotions_pipe = None

def get_go_emotions():
    global _go_emotions_pipe
    if _go_emotions_pipe is None:
        from transformers import pipeline
        _go_emotions_pipe = pipeline(
            "text-classification",
            model="SamLowe/roberta-base-go_emotions",
            top_k=None,
            device=-1,
        )
    return _go_emotions_pipe


def score_go_emotions(text: str) -> dict[str, float]:
    """Score text with GoEmotions, return all 27 emotion probabilities."""
    pipe = get_go_emotions()
    results = pipe(text, truncation=True, max_length=512)[0]
    return {r["label"]: r["score"] for r in results}


_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


_anchor_embeddings = {}

def get_anchor_embedding(anchor_text: str) -> np.ndarray:
    if anchor_text not in _anchor_embeddings:
        model = get_embedder()
        _anchor_embeddings[anchor_text] = model.encode(anchor_text)
    return _anchor_embeddings[anchor_text]


def score_embedding_cosine(text: str) -> dict[str, float]:
    """Cosine similarity to empathetic and clinical anchors."""
    model = get_embedder()
    truncated = " ".join(text.split()[:450])
    emb = model.encode(truncated)

    emp_anchor = get_anchor_embedding(ANCHOR_EMPATHETIC)
    cli_anchor = get_anchor_embedding(ANCHOR_CLINICAL)

    cos_emp = float(np.dot(emb, emp_anchor) / (np.linalg.norm(emb) * np.linalg.norm(emp_anchor)))
    cos_cli = float(np.dot(emb, cli_anchor) / (np.linalg.norm(emb) * np.linalg.norm(cli_anchor)))

    return {
        "cosine_empathy": cos_emp,
        "cosine_clinical": cos_cli,
        "cosine_delta": cos_emp - cos_cli,  # positive = more empathetic
    }


def score_textstat(text: str) -> dict[str, float]:
    """Readability indices."""
    import textstat
    return {
        "flesch_kincaid": textstat.flesch_kincaid_grade(text),
        "gunning_fog": textstat.gunning_fog(text),
        "coleman_liau": textstat.coleman_liau_index(text),
        "flesch_ease": textstat.flesch_reading_ease(text),
    }


_nlp = None

def get_spacy():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def score_spacy_pos(text: str) -> dict[str, float]:
    """POS-based metrics: adjective density, adverb density, noun-to-verb ratio."""
    nlp = get_spacy()
    # Limit to first 500 tokens for speed
    doc = nlp(" ".join(text.split()[:500]))
    total = max(len(doc), 1)

    adj_count = sum(1 for t in doc if t.pos_ == "ADJ")
    adv_count = sum(1 for t in doc if t.pos_ == "ADV")
    noun_count = sum(1 for t in doc if t.pos_ in ("NOUN", "PROPN"))
    verb_count = sum(1 for t in doc if t.pos_ == "VERB")

    return {
        "adj_density": adj_count / total,
        "adv_density": adv_count / total,
        "noun_verb_ratio": noun_count / max(verb_count, 1),
    }


def score_all(text: str) -> dict[str, float]:
    """Compute all new metrics for a single response."""
    result = {}

    # GoEmotions
    emotions = score_go_emotions(text)
    result.update({f"emo_{k}": v for k, v in emotions.items()})
    result["empathy_cluster"] = sum(emotions.get(e, 0) for e in EMPATHY_EMOTIONS)
    result["cold_cluster"] = sum(emotions.get(e, 0) for e in COLD_EMOTIONS)
    result["empathy_cold_delta"] = result["empathy_cluster"] - result["cold_cluster"]

    # Embedding cosine
    cosines = score_embedding_cosine(text)
    result.update(cosines)

    # Readability
    readability = score_textstat(text)
    result.update(readability)

    # POS
    pos = score_spacy_pos(text)
    result.update(pos)

    return result


# --- FFT ---

def compute_fft(signal: np.ndarray, sample_interval_days: float) -> dict:
    """FFT with detrend + Hanning window."""
    from scipy.fft import fft, fftfreq
    from scipy.signal import detrend

    N = len(signal)
    if N < 8:
        return {}
    d = detrend(signal, type="linear")
    w = np.hanning(N) * d
    yf = fft(w)
    xf = fftfreq(N, d=sample_interval_days)
    pos = xf > 0
    freqs = xf[pos]
    mags = 2.0 / N * np.abs(yf[pos])
    periods = 1.0 / freqs

    if len(mags) == 0:
        return {}

    peak_idx = int(np.argmax(mags))
    peak_mag = float(mags[peak_idx])
    non_peak = np.delete(mags, peak_idx)
    noise_mean = float(np.mean(non_peak)) if len(non_peak) > 0 else 1e-10
    noise_std = float(np.std(non_peak)) if len(non_peak) > 1 else 1e-10
    sigma = (peak_mag - noise_mean) / max(noise_std, 1e-10)

    return {
        "peak_period_days": float(periods[peak_idx]),
        "peak_magnitude": peak_mag,
        "sigma": sigma,
    }


# --- Main analysis ---

SEMANTIC_METRICS = [
    "empathy_cluster", "cold_cluster", "empathy_cold_delta",
    "cosine_empathy", "cosine_clinical", "cosine_delta",
    "flesch_kincaid", "gunning_fog", "coleman_liau", "flesch_ease",
    "adj_density", "adv_density", "noun_verb_ratio",
    "emo_caring", "emo_love", "emo_optimism", "emo_neutral",
    "emo_admiration", "emo_approval", "emo_gratitude",
    "emo_annoyance", "emo_disapproval",
]


def score_responses(data: list[dict]) -> list[dict]:
    """Score all responses with new metrics."""
    total = len(data)
    t_start = time.time()

    for i, record in enumerate(data):
        record["new_metrics"] = score_all(record["response"])
        if (i + 1) % 30 == 0:
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / max(rate, 0.01)
            print(f"  [{i+1}/{total}] {rate:.1f} resp/s, ~{remaining:.0f}s remaining", flush=True)

    return data


def analyze(data: list[dict]) -> dict:
    """FFT analysis on all new metrics across conditions."""
    sample_interval = STEP_HOURS / 24.0

    # Engine input reference
    temporal = sorted([r for r in data if r["condition"] == "temporal"], key=lambda r: r["step"])
    empathy_input = np.array([r["dimensions"]["empathy"] for r in temporal])
    engine_fft = compute_fft(empathy_input, sample_interval)
    engine_period = engine_fft.get("peak_period_days", 9.0)

    print(f"\n{'='*70}")
    print(f"ENGINE INPUT: empathy peak={engine_period:.1f}d, sigma={engine_fft.get('sigma', 0):.2f}")
    print(f"{'='*70}")

    results = {}
    go_metrics = []

    for metric in SEMANTIC_METRICS:
        print(f"\n  -- {metric} --")
        metric_results = {}

        for cond in ["temporal", "static", "random"]:
            filtered = sorted([r for r in data if r["condition"] == cond], key=lambda r: r["step"])
            values = np.array([r["new_metrics"][metric] for r in filtered])
            fft_res = compute_fft(values, sample_interval)
            metric_results[cond] = fft_res

            if fft_res:
                print(f"    {cond:10s}: peak={fft_res['peak_period_days']:.1f}d  "
                      f"sigma={fft_res['sigma']:.2f}  "
                      f"range=[{float(np.min(values)):.4f}, {float(np.max(values)):.4f}]")

        # Check GO criteria
        t_fft = metric_results.get("temporal", {})
        s_fft = metric_results.get("static", {})
        r_fft = metric_results.get("random", {})

        if t_fft:
            aligned = abs(t_fft["peak_period_days"] - engine_period) <= 2.0
            strong = t_fft["sigma"] >= 3.0
            static_diff = abs(s_fft.get("peak_period_days", 0) - engine_period) > 2.0 if s_fft else True
            random_diff = abs(r_fft.get("peak_period_days", 0) - engine_period) > 2.0 if r_fft else True

            is_go = aligned and strong and static_diff
            status = "GO" if is_go else "-"

            if is_go:
                go_metrics.append({"metric": metric, "sigma": t_fft["sigma"],
                                   "period": t_fft["peak_period_days"]})

            print(f"    => aligned={aligned}, sigma>3={strong}, "
                  f"static_diff={static_diff}, random_diff={random_diff} => {status}")

        results[metric] = metric_results

    # Verdict
    go = len(go_metrics) > 0
    best = max(go_metrics, key=lambda x: x["sigma"]) if go_metrics else None

    print(f"\n{'='*70}")
    if go:
        print(f"VERDICT: GO — Semantic modulation PROVEN!")
        print(f"  GO metrics ({len(go_metrics)}):")
        for gm in sorted(go_metrics, key=lambda x: -x["sigma"]):
            print(f"    {gm['metric']}: {gm['sigma']:.2f}sigma at {gm['period']:.1f}d")
    else:
        # Show top 3 closest
        all_temporal = []
        for metric in SEMANTIC_METRICS:
            t_fft = results.get(metric, {}).get("temporal", {})
            if t_fft and abs(t_fft.get("peak_period_days", 0) - engine_period) <= 2.0:
                all_temporal.append({"metric": metric, "sigma": t_fft["sigma"],
                                     "period": t_fft["peak_period_days"]})

        print(f"VERDICT: NO-GO — Semantic modulation not proven at 3sigma.")
        if all_temporal:
            print(f"  Closest aligned metrics:")
            for at in sorted(all_temporal, key=lambda x: -x["sigma"])[:5]:
                print(f"    {at['metric']}: {at['sigma']:.2f}sigma at {at['period']:.1f}d")
        else:
            print("  No metrics aligned with engine 9-day period.")
    print(f"{'='*70}")

    verdict = {
        "go": go,
        "engine_period_days": engine_period,
        "go_metrics": go_metrics,
        "best_metric": best,
        "all_results": {k: {cond: v for cond, v in conds.items() if v}
                        for k, conds in results.items()},
    }
    return verdict


def main():
    parser = argparse.ArgumentParser(description="Experiment 009: Re-measure with GoEmotions + embeddings")
    parser.add_argument("--skip-score", action="store_true", help="Reuse scored data")
    args = parser.parse_args()

    if args.skip_score and SCORED_FILE.exists():
        print("Loading pre-scored data...", flush=True)
        data = json.loads(SCORED_FILE.read_text())
    else:
        data = load_data()
        print("\nScoring 540 responses with GoEmotions + embeddings + textstat + spaCy...", flush=True)
        data = score_responses(data)
        SCORED_FILE.write_text(json.dumps(data, indent=2, default=str))
        print(f"\nScored data saved: {SCORED_FILE}", flush=True)

    # FFT analysis
    verdict = analyze(data)
    VERDICT_FILE.write_text(json.dumps(verdict, indent=2, default=str))
    print(f"\nVerdict saved: {VERDICT_FILE}", flush=True)


if __name__ == "__main__":
    main()
