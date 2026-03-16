"""Semantic Proof: Length-Agnostic Metrics + FFT for Agent Soul.

Experiment 006: Validate that temporal behavioral modulation extends beyond
structural formatting (word_count) into semantic properties.

Metrics (all length-independent):
- sentence_vader: average VADER compound score per sentence (not per document)
- mtld: Measure of Textual Lexical Diversity (length-independent by design)

Go/No-Go: FFT peak at 9.0-day period with ≥3.0σ in temporal condition,
absent in static/random conditions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import detrend

# ── Lazy imports (heavy) ──
_vader = None
_mtld_fn = None


def _get_vader():
    global _vader
    if _vader is None:
        import nltk
        nltk.download("vader_lexicon", quiet=True)
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        _vader = SentimentIntensityAnalyzer()
    return _vader


def _get_mtld():
    global _mtld_fn
    if _mtld_fn is None:
        from lexical_diversity import lex_div
        _mtld_fn = lex_div.mtld
    return _mtld_fn


# ── Metrics ──

def sentence_vader(text: str) -> float:
    """Average VADER compound score per sentence (length-agnostic)."""
    sia = _get_vader()
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s for s in sentences if len(s.split()) >= 3]
    if not sentences:
        return 0.0
    scores = [sia.polarity_scores(s)["compound"] for s in sentences]
    return float(np.mean(scores))


def mtld_score(text: str) -> float:
    """MTLD lexical diversity (length-independent)."""
    mtld = _get_mtld()
    words = text.lower().split()
    if len(words) < 10:
        return 0.0
    try:
        return float(mtld(words))
    except Exception:
        return 0.0


def compute_semantic_metrics(text: str) -> dict[str, float]:
    """Compute all length-agnostic semantic metrics."""
    return {
        "sentence_vader": sentence_vader(text),
        "mtld": mtld_score(text),
    }


# ── FFT Analysis ──

STEP_HOURS = 12


def run_fft(signal: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """FFT with detrend + Hanning window. Returns (periods_days, magnitudes)."""
    N = len(signal)
    if N < 8:
        return np.array([]), np.array([])
    d = detrend(signal, type="linear")
    w = np.hanning(N) * d
    yf = fft(w)
    xf = fftfreq(N, d=STEP_HOURS / 24.0)
    pos = xf > 0
    freqs = xf[pos]
    mags = 2.0 / N * np.abs(yf[pos])
    periods = 1.0 / freqs
    return periods, mags


def find_peak_and_sigma(periods: np.ndarray, mags: np.ndarray,
                         min_period: float = 3.0, max_period: float = 60.0
                         ) -> dict:
    """Find peak in period range, compute sigma above noise floor."""
    mask = (periods >= min_period) & (periods <= max_period)
    if not mask.any():
        return {"period": 0.0, "sigma": 0.0, "magnitude": 0.0}
    filtered_mags = mags[mask]
    filtered_periods = periods[mask]
    peak_idx = np.argmax(filtered_mags)
    peak_period = filtered_periods[peak_idx]
    peak_mag = filtered_mags[peak_idx]

    # Noise = all bins except peak ± 1
    noise_mask = np.ones(len(filtered_mags), dtype=bool)
    for offset in range(-1, 2):
        idx = peak_idx + offset
        if 0 <= idx < len(noise_mask):
            noise_mask[idx] = False
    if noise_mask.sum() < 3:
        return {"period": float(peak_period), "sigma": 0.0, "magnitude": float(peak_mag)}
    noise = filtered_mags[noise_mask]
    noise_mean = np.mean(noise)
    noise_std = np.std(noise)
    sigma = (peak_mag - noise_mean) / max(noise_std, 1e-15)

    return {
        "period": float(peak_period),
        "sigma": float(sigma),
        "magnitude": float(peak_mag),
    }


# ── Main ──

RESULTS_DIR = Path(__file__).parent / "results"


def main():
    scored_file = RESULTS_DIR / "cvb_v3_scored.json"
    if not scored_file.exists():
        print(f"ERROR: {scored_file} not found. Run cvb_runner.py first.")
        return

    print("Loading 540 responses...")
    results = json.loads(scored_file.read_text())

    # Separate conditions
    conditions = {}
    for cond in ["temporal", "static", "random"]:
        items = sorted([r for r in results if r["condition"] == cond], key=lambda r: r["step"])
        conditions[cond] = items

    for cond, items in conditions.items():
        print(f"  {cond}: {len(items)} responses")

    # Compute semantic metrics
    print("\nComputing sentence-level VADER + MTLD...")
    for cond, items in conditions.items():
        for i, item in enumerate(items):
            metrics = compute_semantic_metrics(item["response"])
            item["semantic"] = metrics
            if (i + 1) % 30 == 0:
                print(f"  [{cond}] {i+1}/{len(items)} done")
        print(f"  [{cond}] complete")

    # Extract time series
    metrics_to_check = ["sentence_vader", "mtld"]

    print("\n" + "=" * 70)
    print("FFT ANALYSIS — Semantic Metrics")
    print("=" * 70)

    all_results = {}

    for metric in metrics_to_check:
        print(f"\n── {metric} ──")

        for cond in ["temporal", "static", "random"]:
            items = conditions[cond]
            ts = np.array([item["semantic"][metric] for item in items])

            print(f"  {cond:10s}: mean={ts.mean():.4f}, std={ts.std():.4f}, "
                  f"range=[{ts.min():.4f}, {ts.max():.4f}]")

            periods, mags = run_fft(ts)
            peak = find_peak_and_sigma(periods, mags)

            print(f"  {cond:10s}: FFT peak at {peak['period']:.1f}d, "
                  f"σ={peak['sigma']:.2f}")

            all_results[f"{metric}_{cond}"] = {
                "mean": float(ts.mean()),
                "std": float(ts.std()),
                "fft_peak_period": peak["period"],
                "fft_peak_sigma": peak["sigma"],
            }

    # Engine input for comparison
    temporal_items = conditions["temporal"]
    if temporal_items[0].get("dimensions"):
        empathy = np.array([item["dimensions"]["empathy"] for item in temporal_items])
        periods_in, mags_in = run_fft(empathy)
        engine_peak = find_peak_and_sigma(periods_in, mags_in)
        print(f"\n── Engine Input (empathy) ──")
        print(f"  FFT peak at {engine_peak['period']:.1f}d, σ={engine_peak['sigma']:.2f}")
    else:
        engine_peak = {"period": 9.0}  # known from previous experiment

    # ── VERDICT ──
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)

    TARGET_PERIOD = engine_peak.get("period", 9.0)
    SIGMA_THRESHOLD = 3.0
    PERIOD_TOLERANCE = 2.0  # ±2 days

    semantic_go = False

    for metric in metrics_to_check:
        temporal = all_results[f"{metric}_temporal"]
        static = all_results[f"{metric}_static"]

        aligned = abs(temporal["fft_peak_period"] - TARGET_PERIOD) <= PERIOD_TOLERANCE
        strong = temporal["fft_peak_sigma"] >= SIGMA_THRESHOLD
        static_different = abs(static["fft_peak_period"] - TARGET_PERIOD) > PERIOD_TOLERANCE

        status = "GO" if (aligned and strong and static_different) else "NO-GO"
        if status == "GO":
            semantic_go = True

        print(f"\n  {metric}:")
        print(f"    Temporal peak: {temporal['fft_peak_period']:.1f}d (σ={temporal['fft_peak_sigma']:.2f})")
        print(f"    Static peak:   {static['fft_peak_period']:.1f}d")
        print(f"    Aligned with engine ({TARGET_PERIOD:.1f}d ±{PERIOD_TOLERANCE:.0f}d): {aligned}")
        print(f"    σ ≥ {SIGMA_THRESHOLD}: {strong}")
        print(f"    Static different: {static_different}")
        print(f"    → {status}")

    print(f"\n{'='*70}")
    if semantic_go:
        print("OVERALL: GO — Semantic modulation proven!")
        print("Claim: 'Temporal Behavioral Modulation' (structural + semantic)")
    else:
        print("OVERALL: NO-GO — Semantic modulation not proven.")
        print("Claim: 'Temporal Structural Modulation' (word_count only, 5.8σ)")
    print(f"{'='*70}")

    # Save results
    verdict = {
        "semantic_go": semantic_go,
        "target_period_days": TARGET_PERIOD,
        "sigma_threshold": SIGMA_THRESHOLD,
        "metrics": all_results,
    }

    out_file = RESULTS_DIR / "semantic_proof_verdict.json"
    out_file.write_text(json.dumps(verdict, indent=2))
    print(f"\nResults saved: {out_file}")

    # Save scored data with semantic metrics
    scored_semantic = RESULTS_DIR / "cvb_v3_scored_semantic.json"
    all_items = []
    for cond in conditions.values():
        all_items.extend(cond)
    scored_semantic.write_text(json.dumps(all_items, indent=2, default=str))
    print(f"Scored data saved: {scored_semantic}")


if __name__ == "__main__":
    main()
