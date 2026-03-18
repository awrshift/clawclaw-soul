"""Experiment 007: Trojan Horse — Semantic Modulation via Structural Constraints.

Uses lexical banning, syntactical constraints, and cognitive framing to force
semantic shifts that bypass RLHF. Measures with trojan-specific metrics + FFT.

Usage:
    python3 benchmark/trojan_runner.py                  # full 90-day run
    python3 benchmark/trojan_runner.py --days 10        # smoke test
    python3 benchmark/trojan_runner.py --skip-generate  # reuse cached responses
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

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_soul.engine import compute_modifiers_v2
from agent_soul.prompt import dimensions_to_trojan_prompt
from agent_soul.soul import create_soul
from benchmark.trojan_metrics import compute_trojan_metrics

RESULTS_DIR = Path(__file__).parent / "results"

MODEL = "gemini-2.0-flash"
AGENT_SEED = 42
STEP_HOURS = 12
DEFAULT_DAYS = 90
TEMPERATURE = 0.4
RATE_LIMIT_DELAY = 0.5

BENCHMARK_WEIGHTS = (0.0, 0.0, 1.0)  # pure transit
BENCHMARK_GAIN = 3.0

# Random trojan prompts for control condition
RANDOM_TROJAN = [
    "IMPORTANT: Never use these words: maybe, perhaps, possibly, might, could.",
    "IMPORTANT: Never use these words: must, certainly, absolutely, clearly, obviously.",
    "Write in short, direct sentences. No sentence should exceed 8 words.",
    "Write using complex compound sentences. Each sentence at least 20 words.",
    "Give only concrete, specific examples with exact numbers.",
    "Explain using hypothetical scenarios and abstract principles.",
    "IMPORTANT: Never use: suggest, consider, likely, potentially, arguably.",
    "Write in short sentences. Maximum 10 words each. Active voice only.",
    "IMPORTANT: Never use: always, never, definitely, undoubtedly, will.",
    "Use subordinate clauses and semicolons. Minimum 18 words per sentence.",
]

# Metrics for FFT analysis
FFT_METRICS = [
    "hedge_density", "assertive_density", "avg_sentence_length",
    "question_density", "sentence_vader",
]


def _load_env():
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
        raise RuntimeError("GOOGLE_API_KEY not found.")


_client = None


def _get_client():
    global _client
    if _client is None:
        _load_env()
        from google import genai
        from google.genai import types
        _client = genai.Client(http_options=types.HttpOptions(timeout=30_000))
    return _client


def generate_one(prompt: str, system_prompt: str | None, temp: float) -> str:
    from google.genai import types
    client = _get_client()
    config = types.GenerateContentConfig(temperature=temp, max_output_tokens=1024)
    if system_prompt:
        config.system_instruction = system_prompt

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL, contents=prompt, config=config,
            )
            time.sleep(RATE_LIMIT_DELAY)
            return response.text or ""
        except Exception as e:
            if attempt < 2:
                wait = (attempt + 1) * 5
                print(f"  Error: {e}, retry in {wait}s...", flush=True)
                time.sleep(wait)
            else:
                return f"[ERROR: {e}]"


def run_generation(days: int) -> list[dict]:
    """Run 3-condition generation with Trojan Horse constraints."""
    import random as rng_module

    soul = create_soul(AGENT_SEED)
    base_date = datetime.now(timezone.utc)
    steps_per_day = 24 // STEP_HOURS
    total_steps = days * steps_per_day
    total_gens = total_steps * 3
    results = []
    gen_count = 0
    t_start = time.time()

    prompt_text = "What makes a good code review process?"

    print(f"\n=== Trojan Horse Generation: {days} days, {total_steps} steps ===", flush=True)
    print(f"  Seed: {AGENT_SEED}, Lagna: {soul.lagna_sign}", flush=True)
    print(f"  Total generations: {total_gens}", flush=True)

    for step in range(total_steps):
        timestamp = base_date - timedelta(hours=step * STEP_HOURS)
        day = step // steps_per_day

        # Engine → dimensions → trojan prompt
        mod_result = compute_modifiers_v2(soul, timestamp, weights=BENCHMARK_WEIGHTS)
        dimensions = mod_result["dimensions"]
        trojan_prompt = dimensions_to_trojan_prompt(dimensions, gain=BENCHMARK_GAIN)

        # Random trojan (changes daily)
        day_rng = rng_module.Random(42 + day)
        random_trojan = day_rng.choice(RANDOM_TROJAN)

        # --- Static ---
        text_static = generate_one(prompt_text, None, TEMPERATURE)
        results.append({
            "condition": "static", "step": step, "day": day,
            "timestamp": timestamp.isoformat(), "response": text_static,
            "dimensions": None,
        })

        # --- Random ---
        text_random = generate_one(prompt_text, random_trojan, TEMPERATURE)
        results.append({
            "condition": "random", "step": step, "day": day,
            "timestamp": timestamp.isoformat(), "response": text_random,
            "dimensions": None,
        })

        # --- Temporal ---
        text_temporal = generate_one(prompt_text, trojan_prompt or None, TEMPERATURE)
        results.append({
            "condition": "temporal", "step": step, "day": day,
            "timestamp": timestamp.isoformat(), "response": text_temporal,
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


def score_results(results: list[dict]) -> list[dict]:
    """Compute trojan metrics for all responses."""
    print(f"\n=== Trojan Metrics ({len(results)} responses) ===", flush=True)
    for r in results:
        r["metrics"] = compute_trojan_metrics(r["response"])

    for cond in ["static", "random", "temporal"]:
        filtered = [r for r in results if r["condition"] == cond]
        hd = [r["metrics"]["hedge_density"] for r in filtered]
        ad = [r["metrics"]["assertive_density"] for r in filtered]
        sl = [r["metrics"]["avg_sentence_length"] for r in filtered]
        print(f"  {cond}: hedge=[{min(hd):.4f},{max(hd):.4f}] std={np.std(hd):.4f}  "
              f"assertive=[{min(ad):.4f},{max(ad):.4f}] std={np.std(ad):.4f}  "
              f"sent_len=[{min(sl):.1f},{max(sl):.1f}] std={np.std(sl):.1f}",
              flush=True)
    return results


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
        "peak_bin": peak_idx,
        "peak_magnitude": peak_mag,
        "sigma": sigma,
    }


def analyze_and_verdict(results: list[dict]) -> dict:
    """FFT analysis + Go/No-Go verdict."""
    print("\n=== FFT Analysis (Trojan) ===", flush=True)
    sample_interval = STEP_HOURS / 24.0

    # Engine input peak
    temporal = sorted([r for r in results if r["condition"] == "temporal"], key=lambda r: r["step"])
    empathy = np.array([r["dimensions"]["empathy"] for r in temporal])
    engine_fft = compute_fft(empathy, sample_interval)
    engine_period = engine_fft.get("peak_period_days", 9.0)
    print(f"  Engine input (empathy): peak={engine_period:.1f}d σ={engine_fft.get('sigma', 0):.2f}",
          flush=True)

    # Analyze each metric × condition
    all_analysis = {}
    go = False
    best_metric = None
    best_sigma = 0.0

    for metric in FFT_METRICS:
        print(f"\n  ── {metric} ──", flush=True)
        for cond in ["temporal", "static", "random"]:
            filtered = sorted([r for r in results if r["condition"] == cond], key=lambda r: r["step"])
            ts = np.array([r["metrics"][metric] for r in filtered])
            fft_res = compute_fft(ts, sample_interval)
            key = f"{metric}_{cond}"
            all_analysis[key] = fft_res
            if fft_res:
                print(f"    {cond:10s}: peak={fft_res['peak_period_days']:.1f}d  "
                      f"σ={fft_res['sigma']:.2f}", flush=True)

        # Check alignment for temporal
        t_fft = all_analysis.get(f"{metric}_temporal", {})
        s_fft = all_analysis.get(f"{metric}_static", {})
        if t_fft:
            aligned = abs(t_fft["peak_period_days"] - engine_period) <= 2.0
            strong = t_fft["sigma"] >= 3.0
            static_diff = abs(s_fft.get("peak_period_days", 0) - engine_period) > 2.0 if s_fft else True

            if aligned and strong and static_diff:
                go = True
                if t_fft["sigma"] > best_sigma:
                    best_sigma = t_fft["sigma"]
                    best_metric = metric

            status = "GO" if (aligned and strong and static_diff) else "—"
            print(f"    → aligned={aligned}, σ≥3={strong}, "
                  f"static_diff={static_diff} → {status}", flush=True)

    verdict = {
        "go": go,
        "engine_period_days": engine_period,
        "best_metric": best_metric,
        "best_sigma": best_sigma,
        "analysis": {k: v for k, v in all_analysis.items() if v},
    }

    print(f"\n{'='*60}", flush=True)
    if go:
        print(f"VERDICT: GO — Semantic modulation proven!", flush=True)
        print(f"  Best: {best_metric} at {best_sigma:.2f}σ", flush=True)
    else:
        print(f"VERDICT: NO-GO — Semantic modulation not proven.", flush=True)
    print(f"{'='*60}", flush=True)

    return verdict


def main():
    parser = argparse.ArgumentParser(description="Experiment 007: Trojan Horse")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--skip-generate", action="store_true")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file = RESULTS_DIR / "trojan_results.json"

    if args.skip_generate and results_file.exists():
        print("Loading cached trojan results...", flush=True)
        results = json.loads(results_file.read_text())
    else:
        results = run_generation(args.days)
        results_file.write_text(json.dumps(results, indent=2, default=str))
        print(f"Raw results saved: {results_file}", flush=True)

    # Score
    results = score_results(results)
    scored_file = RESULTS_DIR / "trojan_scored.json"
    scored_file.write_text(json.dumps(results, indent=2, default=str))

    # FFT + Verdict
    verdict = analyze_and_verdict(results)
    (RESULTS_DIR / "trojan_verdict.json").write_text(json.dumps(verdict, indent=2))
    print(f"\nResults saved to {RESULTS_DIR}/trojan_*.json", flush=True)


if __name__ == "__main__":
    main()
