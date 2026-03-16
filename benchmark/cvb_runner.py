"""Celestial Variance Benchmark v2 — Embedding + Dual-FFT.

Redesigned per brainstorm 002 findings:
- Embedding-based trait scoring (replaces broken regex proxies)
- Proper DSP: detrend + Hanning window before FFT
- Dual-FFT proof: engine input FFT vs LLM output FFT must align
- Single semantic trait (agreeableness) for v1

Usage:
    python3 benchmark/cvb_runner.py                          # full 90-day run
    python3 benchmark/cvb_runner.py --days 10                # quick smoke test
    python3 benchmark/cvb_runner.py --skip-generate          # reuse cached responses
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

from agent_soul.engine import compute_modifiers
from agent_soul.prompt import modifiers_to_prompt
from benchmark.embed import score_batch

PROMPTS_FILE = Path(__file__).parent / "prompts.json"
RESULTS_DIR = Path(__file__).parent / "results"
ENV_FILE = Path(__file__).parent.parent.parent / "Documents" / "Head-of-AI" / ".env"

MODEL = "gemini-2.0-flash"
AGENT_ID = "benchmark-agent"
STEP_HOURS = 12
DEFAULT_DAYS = 90
TEMPERATURE = 0.4
TRAIT = "agreeableness"

# Rate limiting: Gemini Flash free tier = 15 RPM, paid = 2000 RPM
RATE_LIMIT_DELAY = 0.5  # seconds between calls (safe for paid tier)

# Transit-heavy weights for benchmark (maximizes day-to-day variance).
BENCHMARK_WEIGHTS = (0.20, 0.25, 0.55)

# Random personality prompts for the "random" control condition.
RANDOM_PERSONALITIES = [
    "Be very concise and direct.",
    "Be detailed and thorough in your explanations.",
    "Be creative and think outside the box.",
    "Be cautious and highlight risks.",
    "Be encouraging and supportive.",
    "Challenge assumptions and be critical.",
    "Be proactive and suggest next steps.",
    "Stick to facts and proven approaches.",
    "Be bold and recommend ambitious strategies.",
    "Focus only on what was asked, nothing more.",
]


def _load_env():
    """Load GOOGLE_API_KEY from .env file."""
    # Try multiple locations
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


def generate_one(prompt: str, system_prompt: str | None, temp: float, seed: int = 0) -> str:
    """Generate a response using Gemini Flash.

    seed parameter kept for API compatibility but not used by Gemini.
    """
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
# Phase 1: Generation (time-spoofed)
# ──────────────────────────────────────────────

def run_generation(
    prompt: dict,
    days: int,
) -> list[dict]:
    """Run time-spoofed generation for one prompt across N days.

    3 conditions: static, random, temporal.
    """
    import random as rng_module

    base_date = datetime.now(timezone.utc)
    steps_per_day = 24 // STEP_HOURS
    total_steps = days * steps_per_day
    results = []
    total_gens = total_steps * 3  # 3 conditions
    gen_count = 0
    t_start = time.time()

    print(f"\n=== Generation: {days} days, {total_steps} steps, prompt={prompt['id']} ===", flush=True)
    print(f"  Total generations: {total_gens}", flush=True)

    for step in range(total_steps):
        timestamp = base_date - timedelta(hours=step * STEP_HOURS)
        day = step // steps_per_day

        # Compute temporal modifiers for this timestamp
        mod_result = compute_modifiers(AGENT_ID, timestamp, weights=BENCHMARK_WEIGHTS)
        temporal_prompt = modifiers_to_prompt(mod_result["modifiers"])
        modifiers = mod_result["modifiers"]

        # Random personality (changes daily)
        day_rng = rng_module.Random(42 + day)
        random_personality = day_rng.choice(RANDOM_PERSONALITIES)

        seed_base = hash((prompt["id"], step)) % (2**31)

        # --- Static ---
        text_static = generate_one(prompt["prompt"], None, TEMPERATURE, seed_base)
        results.append({
            "condition": "static",
            "step": step,
            "day": day,
            "timestamp": timestamp.isoformat(),
            "prompt_id": prompt["id"],
            "response": text_static,
            "modifiers": None,
        })

        # --- Random ---
        text_random = generate_one(prompt["prompt"], random_personality, TEMPERATURE, seed_base + 1)
        results.append({
            "condition": "random",
            "step": step,
            "day": day,
            "timestamp": timestamp.isoformat(),
            "prompt_id": prompt["id"],
            "response": text_random,
            "modifiers": None,
        })

        # --- Temporal ---
        sys_prompt = temporal_prompt if temporal_prompt else None
        text_temporal = generate_one(prompt["prompt"], sys_prompt, TEMPERATURE, seed_base + 2)
        results.append({
            "condition": "temporal",
            "step": step,
            "day": day,
            "timestamp": timestamp.isoformat(),
            "prompt_id": prompt["id"],
            "response": text_temporal,
            "modifiers": modifiers,
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
# Phase 2: Embedding Scoring
# ──────────────────────────────────────────────

def score_responses(results: list[dict]) -> list[dict]:
    """Score all responses using embedding cosine distance."""
    print(f"\n=== Embedding Scoring ({len(results)} responses, trait={TRAIT}) ===", flush=True)

    # Batch all texts for efficiency
    texts = [r["response"] for r in results]

    # Process in batches of 50 (avoid OOM on large runs)
    BATCH_SIZE = 50
    all_scores = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        scores = score_batch(batch, trait=TRAIT)
        all_scores.extend(scores)
        if (i // BATCH_SIZE) % 5 == 0:
            print(f"  Embedded {i + len(batch)}/{len(texts)}...", flush=True)

    for r, score in zip(results, all_scores):
        r["embed_score"] = score

    print(f"  Score range: [{min(all_scores):.4f}, {max(all_scores):.4f}]", flush=True)
    return results


# ──────────────────────────────────────────────
# Phase 3: DSP + Dual-FFT Analysis
# ──────────────────────────────────────────────

def build_time_series(results: list[dict], condition: str) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Build step-indexed time series for a condition.

    Returns: (steps, embed_scores, modifier_values_or_None)
    """
    filtered = [r for r in results if r["condition"] == condition]
    filtered.sort(key=lambda r: r["step"])

    steps = np.array([r["step"] for r in filtered])
    scores = np.array([r["embed_score"] for r in filtered])

    mods = None
    if condition == "temporal":
        # Extract the agreeableness modifier value per step
        mods = np.array([
            r["modifiers"].get(TRAIT, 0.0) if r["modifiers"] else 0.0
            for r in filtered
        ])

    return steps, scores, mods


def compute_fft_proper(signal: np.ndarray, sample_interval_days: float) -> dict:
    """Run FFT with proper DSP: detrend + Hanning window.

    Returns dict with freqs, magnitudes, periods, peak info, SNR.
    """
    from scipy.fft import fft, fftfreq
    from scipy.signal import detrend

    N = len(signal)
    if N < 8:
        return {}

    # Step 1: Remove linear trend
    detrended = detrend(signal, type="linear")

    # Step 2: Apply Hanning window (eliminates spectral leakage)
    window = np.hanning(N)
    windowed = detrended * window

    # Step 3: FFT
    yf = fft(windowed)
    xf = fftfreq(N, d=sample_interval_days)

    # Only positive frequencies (skip DC at index 0)
    pos_mask = xf > 0
    freqs = xf[pos_mask]
    magnitudes = 2.0 / N * np.abs(yf[pos_mask])
    periods = 1.0 / freqs

    if len(magnitudes) == 0:
        return {}

    # Peak detection
    peak_idx = int(np.argmax(magnitudes))
    peak_freq = float(freqs[peak_idx])
    peak_period = float(periods[peak_idx])
    peak_magnitude = float(magnitudes[peak_idx])

    # SNR: peak / mean of non-peak
    non_peak = np.delete(magnitudes, peak_idx)
    noise_floor = float(np.mean(non_peak)) if len(non_peak) > 0 else 1e-10
    snr = peak_magnitude / max(noise_floor, 1e-10)

    return {
        "peak_frequency": peak_freq,
        "peak_period_days": peak_period,
        "peak_magnitude": peak_magnitude,
        "peak_bin": peak_idx,
        "noise_floor": noise_floor,
        "snr": snr,
        "freqs": freqs.tolist(),
        "magnitudes": magnitudes.tolist(),
        "periods": periods.tolist(),
    }


def analyze_dual_fft(results: list[dict]) -> dict:
    """Run dual-FFT: compare engine input vs LLM output frequency spectra."""
    print("\n=== Dual-FFT Analysis ===", flush=True)
    sample_interval = STEP_HOURS / 24.0  # days per step

    analysis = {}

    for condition in ["static", "random", "temporal"]:
        steps, scores, mods = build_time_series(results, condition)
        if len(steps) < 8:
            continue

        # FFT of embedding scores
        fft_output = compute_fft_proper(scores, sample_interval)

        result = {"output_fft": fft_output}

        # For temporal condition, also FFT the engine input
        if mods is not None:
            fft_input = compute_fft_proper(mods, sample_interval)
            result["input_fft"] = fft_input

            # Peak alignment check: do they peak at the same bin?
            if fft_input and fft_output:
                input_bin = fft_input.get("peak_bin", -1)
                output_bin = fft_output.get("peak_bin", -2)
                aligned = input_bin == output_bin
                result["peak_aligned"] = aligned
                result["input_peak_period"] = fft_input.get("peak_period_days", 0)
                result["output_peak_period"] = fft_output.get("peak_period_days", 0)

                status = "PASS (peaks aligned)" if aligned else "FAIL (peaks misaligned)"
                print(f"  {condition}: input peak={fft_input.get('peak_period_days', 0):.1f}d "
                      f"output peak={fft_output.get('peak_period_days', 0):.1f}d "
                      f"→ {status}", flush=True)
            else:
                result["peak_aligned"] = False
        else:
            if fft_output:
                print(f"  {condition}: output peak={fft_output.get('peak_period_days', 0):.1f}d "
                      f"SNR={fft_output.get('snr', 0):.1f}x", flush=True)

        # Save raw time series for plotting
        result["steps"] = steps.tolist()
        result["scores"] = scores.tolist()
        if mods is not None:
            result["modifiers"] = mods.tolist()

        analysis[condition] = result

    return analysis


# ──────────────────────────────────────────────
# Phase 4: Go / No-Go
# ──────────────────────────────────────────────

def evaluate_go_nogo(analysis: dict) -> dict:
    """Evaluate go/no-go based on dual-FFT peak alignment."""
    print("\n=== Go / No-Go Evaluation ===", flush=True)

    temporal = analysis.get("temporal", {})
    verdict = {
        "peak_aligned": temporal.get("peak_aligned", False),
        "input_peak": temporal.get("input_peak_period", 0),
        "output_peak": temporal.get("output_peak_period", 0),
        "output_snr": temporal.get("output_fft", {}).get("snr", 0),
        "input_snr": temporal.get("input_fft", {}).get("snr", 0),
    }

    # Primary criterion: peaks align
    go = verdict["peak_aligned"] and verdict["output_snr"] > 2.0

    # Secondary: static condition should NOT show the same peak
    static_fft = analysis.get("static", {}).get("output_fft", {})
    if static_fft and temporal.get("output_fft"):
        static_bin = static_fft.get("peak_bin", -1)
        temporal_bin = temporal["output_fft"].get("peak_bin", -2)
        verdict["static_different"] = static_bin != temporal_bin
    else:
        verdict["static_different"] = True  # can't check, assume ok

    verdict["go"] = go and verdict["static_different"]

    status = "GO" if verdict["go"] else "NO-GO"
    print(f"\n  Verdict: {status}", flush=True)
    print(f"  Peak aligned: {verdict['peak_aligned']}", flush=True)
    print(f"  Output SNR: {verdict['output_snr']:.1f}x", flush=True)
    print(f"  Static different: {verdict['static_different']}", flush=True)

    return verdict


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def run_cvb(days: int = DEFAULT_DAYS, skip_generate: bool = False) -> dict:
    """Run the full CVB v2 pipeline."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file = RESULTS_DIR / "cvb_v2_results.json"

    if skip_generate and results_file.exists():
        print("=== Loading cached results ===", flush=True)
        all_results = json.loads(results_file.read_text())
    else:
        # Use the most stable prompt from pruning (hardcoded from v1 results)
        prompt = {"id": "p06", "prompt": "What makes a good code review process?"}
        all_results = run_generation(prompt, days)

        # Save raw results
        results_file.write_text(json.dumps(all_results, indent=2, default=str))
        print(f"\n  Raw results saved: {results_file}", flush=True)

    # Phase 2: Embedding scoring
    all_results = score_responses(all_results)

    # Save scored results
    scored_file = RESULTS_DIR / "cvb_v2_scored.json"
    scored_file.write_text(json.dumps(all_results, indent=2, default=str))

    # Phase 3: Dual-FFT
    analysis = analyze_dual_fft(all_results)

    # Save analysis (strip large arrays for summary file)
    analysis_summary = {}
    for cond, data in analysis.items():
        summary = {k: v for k, v in data.items()
                   if k not in ("steps", "scores", "modifiers")}
        # Also strip freqs/magnitudes/periods from FFT results
        for fft_key in ("output_fft", "input_fft"):
            if fft_key in summary:
                summary[fft_key] = {
                    k: v for k, v in summary[fft_key].items()
                    if k not in ("freqs", "magnitudes", "periods")
                }
        analysis_summary[cond] = summary
    (RESULTS_DIR / "cvb_v2_analysis.json").write_text(json.dumps(analysis_summary, indent=2))

    # Save full analysis (with arrays for plotting)
    (RESULTS_DIR / "cvb_v2_analysis_full.json").write_text(json.dumps(analysis, indent=2, default=str))

    # Phase 4: Go/No-Go
    verdict = evaluate_go_nogo(analysis)
    (RESULTS_DIR / "cvb_v2_verdict.json").write_text(json.dumps(verdict, indent=2))

    print(f"\n=== CVB v2 Complete. Results in {RESULTS_DIR}/ ===", flush=True)
    return verdict


def main():
    parser = argparse.ArgumentParser(description="Celestial Variance Benchmark v2")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--skip-generate", action="store_true")
    args = parser.parse_args()
    run_cvb(days=args.days, skip_generate=args.skip_generate)


if __name__ == "__main__":
    main()
