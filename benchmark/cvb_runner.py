"""Celestial Variance Benchmark v3 — Structural Constraints + Proxy Metrics.

Redesigned per Brainstorm 004:
- Structural constraints (word limits, list format, directive language) instead of personality nudges
- Zero-cost proxy metrics (word_count, hedge_density, pronoun_ratio, distinct-2)
- FFT on proxy time series to detect engine frequency in LLM output
- Go/No-Go: FFT peak at engine frequency >= 3 sigma above noise floor

Uses v2 engine (9 graha dimensions from Digital Soul) with benchmark-heavy transit weights.

Usage:
    python3 benchmark/cvb_runner.py                          # full 90-day run
    python3 benchmark/cvb_runner.py --days 10                # quick smoke test
    python3 benchmark/cvb_runner.py --skip-generate          # reuse cached responses
    python3 benchmark/cvb_runner.py --metrics-only           # proxy metrics + FFT on cached data
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent.parent))

from clawclaw_soul.engine import compute_modifiers_v2
from clawclaw_soul.prompt import dimensions_to_structural_prompt
from clawclaw_soul.soul import create_soul
from benchmark.proxy_metrics import compute_proxies

PROMPTS_FILE = Path(__file__).parent / "prompts.json"
RESULTS_DIR = Path(__file__).parent / "results"

MODEL = "gemini-2.0-flash"
AGENT_SEED = 42
STEP_HOURS = 12
DEFAULT_DAYS = 90
TEMPERATURE = 0.4

RATE_LIMIT_DELAY = 0.5

# Pure transit weights for benchmark (maximizes time-varying signal).
# Natal and dasha are constant over 90 days, only transit varies.
BENCHMARK_WEIGHTS = (0.0, 0.0, 1.0)

# Gain factor: amplifies dimension values before mapping to structural constraints.
# Transit-only dimensions have std ~0.19, gain=3 stretches to fill [-1,+1] range.
BENCHMARK_GAIN = 3.0

# Random structural prompts for "random" control condition.
RANDOM_STRUCTURAL = [
    "Answer in no more than 40 words.",
    "Write at least 150 words with thorough explanations.",
    "Structure your response using exactly 5 bullet points. Each bullet must be one sentence.",
    "Write your response as a single flowing paragraph with no lists.",
    "Use direct, imperative language: 'Do this', 'Implement that'.",
    "Use hedging language: 'perhaps', 'it might be', 'one could argue'.",
    "Answer in exactly one sentence, no more than 20 words.",
    "Structure your response using a numbered list with exactly 3 points.",
    "Write at least 100 words as prose paragraphs. Do not use bullet points.",
    "Write as commands and directives. Every sentence should be an instruction.",
]

# Key metrics for FFT (the ones most likely to show structural signal)
FFT_METRICS = ["word_count", "hedge_density", "bullet_count", "sentence_count"]


def _load_env():
    """Load GOOGLE_API_KEY from .env file."""
    for env_path in [
        Path(__file__).parent.parent / ".env",
        Path.home() / "Documents" / "Head-of-AI" / ".env",
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GOOGLE_API_KEY="):
                    os.environ["GOOGLE_API_KEY"] = line.split("=", 1)[1].strip()
                    return
    if "GOOGLE_API_KEY" not in os.environ:
        raise RuntimeError("GOOGLE_API_KEY not found. Set it in .env or environment.")


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _load_env()
        _client = genai.Client(
            http_options=types.HttpOptions(timeout=30_000),
        )
    return _client


def load_prompts() -> list[dict]:
    return json.loads(PROMPTS_FILE.read_text())


def generate_one(prompt: str, system_prompt: str | None, temp: float) -> str:
    """Generate a response using Gemini Flash."""
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temp,
        max_output_tokens=1024,
    )
    if system_prompt:
        config.system_instruction = system_prompt

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=config,
            )
            time.sleep(RATE_LIMIT_DELAY)
            return response.text or ""
        except Exception as e:
            if attempt < 2:
                wait = (attempt + 1) * 5
                print(f"  Gemini error: {e}, retrying in {wait}s...", flush=True)
                time.sleep(wait)
            else:
                print(f"  Gemini failed after 3 attempts: {e}", flush=True)
                return f"[ERROR: {e}]"


# ──────────────────────────────────────────────
# Phase 1: Generation (time-spoofed, v2 engine)
# ──────────────────────────────────────────────

def run_generation(
    prompt: dict,
    days: int,
) -> list[dict]:
    """Run time-spoofed generation for one prompt across N days.

    3 conditions:
    - static: no system prompt (baseline)
    - random: random structural constraint (changes daily, no engine)
    - temporal: engine-driven structural constraints (the signal we want to detect)
    """
    import random as rng_module

    soul = create_soul(AGENT_SEED)
    base_date = datetime.now(timezone.utc)
    steps_per_day = 24 // STEP_HOURS
    total_steps = days * steps_per_day
    results = []
    total_gens = total_steps * 3
    gen_count = 0
    t_start = time.time()

    print(f"\n=== CVB v3 Generation: {days} days, {total_steps} steps ===", flush=True)
    print(f"  Agent seed: {AGENT_SEED}, Lagna: {soul.lagna_sign}", flush=True)
    print(f"  Prompt: {prompt['id']} — {prompt['prompt'][:60]}", flush=True)
    print(f"  Total generations: {total_gens}", flush=True)

    for step in range(total_steps):
        timestamp = base_date - timedelta(hours=step * STEP_HOURS)
        day = step // steps_per_day

        # v2 engine: soul + timestamp → 9 dimensions
        mod_result = compute_modifiers_v2(soul, timestamp, weights=BENCHMARK_WEIGHTS)
        dimensions = mod_result["dimensions"]
        structural_prompt = dimensions_to_structural_prompt(dimensions, gain=BENCHMARK_GAIN)

        # Random structural (changes daily)
        day_rng = rng_module.Random(42 + day)
        random_structural = day_rng.choice(RANDOM_STRUCTURAL)

        # --- Static ---
        text_static = generate_one(prompt["prompt"], None, TEMPERATURE)
        results.append({
            "condition": "static",
            "step": step,
            "day": day,
            "timestamp": timestamp.isoformat(),
            "prompt_id": prompt["id"],
            "response": text_static,
            "dimensions": None,
        })

        # --- Random ---
        text_random = generate_one(prompt["prompt"], random_structural, TEMPERATURE)
        results.append({
            "condition": "random",
            "step": step,
            "day": day,
            "timestamp": timestamp.isoformat(),
            "prompt_id": prompt["id"],
            "response": text_random,
            "dimensions": None,
        })

        # --- Temporal ---
        sys_prompt = structural_prompt if structural_prompt else None
        text_temporal = generate_one(prompt["prompt"], sys_prompt, TEMPERATURE)
        results.append({
            "condition": "temporal",
            "step": step,
            "day": day,
            "timestamp": timestamp.isoformat(),
            "prompt_id": prompt["id"],
            "response": text_temporal,
            "dimensions": dimensions,
        })

        gen_count += 3
        if gen_count % 30 == 0:
            elapsed = time.time() - t_start
            rate = gen_count / elapsed
            remaining = (total_gens - gen_count) / max(rate, 0.01)
            print(
                f"  [{gen_count}/{total_gens}] step={step}/{total_steps} "
                f"day={day} ({rate:.2f} gen/s, ~{remaining/60:.0f}m remaining)",
                flush=True,
            )

    return results


# ──────────────────────────────────────────────
# Phase 2: Proxy Metrics (zero cost)
# ──────────────────────────────────────────────

def score_with_proxies(results: list[dict]) -> list[dict]:
    """Compute proxy metrics for all responses."""
    print(f"\n=== Proxy Metrics ({len(results)} responses) ===", flush=True)

    for r in results:
        proxies = compute_proxies(r["response"])
        r["metrics"] = proxies

    # Print summary stats per condition
    for condition in ["static", "random", "temporal"]:
        filtered = [r for r in results if r["condition"] == condition]
        wc = [r["metrics"]["word_count"] for r in filtered]
        hd = [r["metrics"]["hedge_density"] for r in filtered]
        bc = [r["metrics"]["bullet_count"] for r in filtered]
        print(f"  {condition}: word_count=[{min(wc):.0f}, {max(wc):.0f}] "
              f"std={np.std(wc):.1f}  hedge=[{min(hd):.3f}, {max(hd):.3f}]  "
              f"bullets=[{min(bc):.0f}, {max(bc):.0f}]", flush=True)

    return results


# ──────────────────────────────────────────────
# Phase 3: FFT on Proxy Time Series
# ──────────────────────────────────────────────

def build_proxy_time_series(results: list[dict], condition: str, metric: str) -> np.ndarray:
    """Extract a metric time series for a condition, sorted by step."""
    filtered = sorted(
        [r for r in results if r["condition"] == condition],
        key=lambda r: r["step"],
    )
    return np.array([r["metrics"][metric] for r in filtered])


def build_dimension_time_series(results: list[dict], dimension: str) -> np.ndarray:
    """Extract engine input dimension time series (temporal condition only)."""
    filtered = sorted(
        [r for r in results if r["condition"] == "temporal"],
        key=lambda r: r["step"],
    )
    return np.array([
        r["dimensions"].get(dimension, 0.0) if r["dimensions"] else 0.0
        for r in filtered
    ])


def compute_fft(signal: np.ndarray, sample_interval_days: float) -> dict:
    """FFT with detrend + Hanning window. Returns peak info + SNR."""
    from scipy.fft import fft, fftfreq
    from scipy.signal import detrend

    N = len(signal)
    if N < 8:
        return {}

    detrended = detrend(signal, type="linear")
    window = np.hanning(N)
    windowed = detrended * window

    yf = fft(windowed)
    xf = fftfreq(N, d=sample_interval_days)

    pos_mask = xf > 0
    freqs = xf[pos_mask]
    magnitudes = 2.0 / N * np.abs(yf[pos_mask])
    periods = 1.0 / freqs

    if len(magnitudes) == 0:
        return {}

    peak_idx = int(np.argmax(magnitudes))
    peak_freq = float(freqs[peak_idx])
    peak_period = float(periods[peak_idx])
    peak_mag = float(magnitudes[peak_idx])

    non_peak = np.delete(magnitudes, peak_idx)
    noise_mean = float(np.mean(non_peak)) if len(non_peak) > 0 else 1e-10
    noise_std = float(np.std(non_peak)) if len(non_peak) > 1 else 1e-10
    snr = peak_mag / max(noise_mean, 1e-10)
    sigma = (peak_mag - noise_mean) / max(noise_std, 1e-10)

    return {
        "peak_frequency": peak_freq,
        "peak_period_days": peak_period,
        "peak_magnitude": peak_mag,
        "peak_bin": peak_idx,
        "noise_floor": noise_mean,
        "noise_std": noise_std,
        "snr": snr,
        "sigma": sigma,
        "freqs": freqs.tolist(),
        "magnitudes": magnitudes.tolist(),
    }


def analyze_fft(results: list[dict]) -> dict:
    """Run FFT on all proxy metrics for all conditions.

    For temporal condition, also FFT the engine input dimensions
    to check if output peaks align with input peaks.
    """
    print("\n=== FFT Analysis ===", flush=True)
    sample_interval = STEP_HOURS / 24.0

    analysis = {}

    for condition in ["static", "random", "temporal"]:
        cond_analysis = {}

        for metric in FFT_METRICS:
            ts = build_proxy_time_series(results, condition, metric)
            if len(ts) < 8:
                continue
            fft_result = compute_fft(ts, sample_interval)
            cond_analysis[metric] = fft_result

            if fft_result:
                print(f"  {condition}/{metric}: peak={fft_result['peak_period_days']:.1f}d "
                      f"sigma={fft_result['sigma']:.1f} SNR={fft_result['snr']:.1f}x",
                      flush=True)

        # For temporal: also FFT the engine input dimensions
        # (empathy→word_count, execution→bullet_count, authority→sentence_count)
        if condition == "temporal":
            for dim in ["empathy", "execution", "authority"]:
                dim_ts = build_dimension_time_series(results, dim)
                if len(dim_ts) < 8:
                    continue
                fft_input = compute_fft(dim_ts, sample_interval)
                cond_analysis[f"input_{dim}"] = fft_input

                if fft_input:
                    print(f"  temporal/input_{dim}: peak={fft_input['peak_period_days']:.1f}d "
                          f"sigma={fft_input['sigma']:.1f}", flush=True)

        analysis[condition] = cond_analysis

    return analysis


# ──────────────────────────────────────────────
# Phase 4: Go / No-Go (3-sigma criterion)
# ──────────────────────────────────────────────

def evaluate_go_nogo(analysis: dict) -> dict:
    """Go/No-Go: any temporal metric FFT peak at engine frequency >= 3 sigma."""
    print("\n=== Go / No-Go Evaluation ===", flush=True)

    temporal = analysis.get("temporal", {})
    static = analysis.get("static", {})

    # Find engine input dominant period (empathy drives word_count — the primary metric)
    input_fft = temporal.get("input_empathy", {})
    if not input_fft:
        input_fft = temporal.get("input_execution", temporal.get("input_authority", {}))

    engine_period = input_fft.get("peak_period_days", 0)
    engine_bin = input_fft.get("peak_bin", -1)

    print(f"  Engine dominant period: {engine_period:.1f} days (bin {engine_bin})", flush=True)

    # Check each output metric
    best_metric = None
    best_sigma = 0.0
    alignments = {}

    for metric in FFT_METRICS:
        output_fft = temporal.get(metric, {})
        if not output_fft:
            continue

        output_bin = output_fft.get("peak_bin", -2)
        output_sigma = output_fft.get("sigma", 0)
        aligned = abs(output_bin - engine_bin) <= 1  # Allow 1-bin tolerance

        alignments[metric] = {
            "output_period": output_fft.get("peak_period_days", 0),
            "output_bin": output_bin,
            "sigma": output_sigma,
            "aligned": aligned,
        }

        # Check static doesn't have same peak (control)
        static_fft = static.get(metric, {})
        static_bin = static_fft.get("peak_bin", -3) if static_fft else -3
        alignments[metric]["static_different"] = abs(static_bin - output_bin) > 1

        status = "ALIGNED" if aligned else "misaligned"
        sig = f"{output_sigma:.1f}σ"
        ctrl = "ctrl_ok" if alignments[metric]["static_different"] else "CTRL_FAIL"
        print(f"  {metric}: {status} {sig} {ctrl} "
              f"(period={output_fft.get('peak_period_days', 0):.1f}d)", flush=True)

        if aligned and output_sigma > best_sigma:
            best_sigma = output_sigma
            best_metric = metric

    # Go criteria: at least one metric aligned at >= 3 sigma, static doesn't match
    go = False
    if best_metric:
        a = alignments[best_metric]
        go = best_sigma >= 3.0 and a.get("static_different", True)

    verdict = {
        "go": go,
        "engine_period_days": engine_period,
        "engine_bin": engine_bin,
        "best_metric": best_metric,
        "best_sigma": best_sigma,
        "alignments": alignments,
    }

    status = "GO" if go else "NO-GO"
    print(f"\n  Verdict: {status}", flush=True)
    if best_metric:
        print(f"  Best: {best_metric} at {best_sigma:.1f}σ", flush=True)
    else:
        print(f"  No aligned metrics found.", flush=True)

    return verdict


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def run_cvb(days: int = DEFAULT_DAYS, skip_generate: bool = False, metrics_only: bool = False) -> dict:
    """Run the full CVB v3 pipeline."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file = RESULTS_DIR / "cvb_v3_results.json"

    if (skip_generate or metrics_only) and results_file.exists():
        print("=== Loading cached v3 results ===", flush=True)
        all_results = json.loads(results_file.read_text())
    else:
        prompt = {"id": "p06", "prompt": "What makes a good code review process?"}
        all_results = run_generation(prompt, days)
        results_file.write_text(json.dumps(all_results, indent=2, default=str))
        print(f"\n  Raw results saved: {results_file}", flush=True)

    # Phase 2: Proxy metrics
    all_results = score_with_proxies(all_results)

    scored_file = RESULTS_DIR / "cvb_v3_scored.json"
    scored_file.write_text(json.dumps(all_results, indent=2, default=str))

    # Phase 3: FFT
    analysis = analyze_fft(all_results)

    # Save analysis summary (strip large arrays)
    analysis_summary = {}
    for cond, metrics in analysis.items():
        cond_summary = {}
        for metric_name, fft_data in metrics.items():
            cond_summary[metric_name] = {
                k: v for k, v in fft_data.items()
                if k not in ("freqs", "magnitudes")
            }
        analysis_summary[cond] = cond_summary
    (RESULTS_DIR / "cvb_v3_analysis.json").write_text(json.dumps(analysis_summary, indent=2))

    # Phase 4: Go/No-Go
    verdict = evaluate_go_nogo(analysis)
    (RESULTS_DIR / "cvb_v3_verdict.json").write_text(json.dumps(verdict, indent=2))

    print(f"\n=== CVB v3 Complete. Results in {RESULTS_DIR}/ ===", flush=True)
    return verdict


def main():
    parser = argparse.ArgumentParser(description="Celestial Variance Benchmark v3")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--skip-generate", action="store_true",
                        help="Reuse cached responses, recompute metrics + FFT")
    parser.add_argument("--metrics-only", action="store_true",
                        help="Same as --skip-generate (alias)")
    args = parser.parse_args()
    run_cvb(days=args.days, skip_generate=args.skip_generate, metrics_only=args.metrics_only)


if __name__ == "__main__":
    main()
