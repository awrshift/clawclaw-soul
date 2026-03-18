"""30-day simulation benchmark harness.

3 conditions x 20 prompts x 5 reps x 30 days = 9000 generations.
Runs against local Ollama with llama3.1:8b.
"""

from __future__ import annotations

import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import ollama

# Add parent dir so we can import agent_soul
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_soul.engine import compute_modifiers
from agent_soul.prompt import modifiers_to_prompt

PROMPTS_FILE = Path(__file__).parent / "prompts.json"
RESULTS_DIR = Path(__file__).parent / "results"

MODEL = "llama3.1:8b"
EMBED_MODEL = "nomic-embed-text"
TEMPERATURE = 0.7
NUM_DAYS = 30
NUM_REPS = 5
MAX_WORKERS = 4

# Random personality system prompts for the "random" condition
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


def load_prompts() -> list[dict]:
    """Load benchmark prompts."""
    return json.loads(PROMPTS_FILE.read_text())


def generate_response(
    prompt: str,
    system_prompt: str | None = None,
    seed: int | None = None,
) -> str:
    """Generate a single response via Ollama."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    options = {"temperature": TEMPERATURE}
    if seed is not None:
        options["seed"] = seed

    response = ollama.chat(
        model=MODEL,
        messages=messages,
        options=options,
    )
    return response["message"]["content"]


def get_embedding(text: str) -> np.ndarray:
    """Get embedding for a text via Ollama."""
    response = ollama.embed(model=EMBED_MODEL, input=text)
    return np.array(response["embeddings"][0])


def run_static_condition(
    prompts: list[dict],
    day: int,
    reps: int,
    seed_base: int,
) -> list[dict]:
    """Static condition: no system prompt, just raw LLM."""
    results = []
    for p in prompts:
        for rep in range(reps):
            seed = seed_base + day * 1000 + int(p["id"][1:]) * 10 + rep
            text = generate_response(p["prompt"], system_prompt=None, seed=seed)
            results.append({
                "condition": "static",
                "day": day,
                "prompt_id": p["id"],
                "rep": rep,
                "response": text,
                "system_prompt": None,
            })
    return results


def run_random_condition(
    prompts: list[dict],
    day: int,
    reps: int,
    seed_base: int,
) -> list[dict]:
    """Random condition: random personality each day."""
    rng = random.Random(seed_base + day)
    personality = rng.choice(RANDOM_PERSONALITIES)

    results = []
    for p in prompts:
        for rep in range(reps):
            seed = seed_base + day * 1000 + int(p["id"][1:]) * 10 + rep
            text = generate_response(p["prompt"], system_prompt=personality, seed=seed)
            results.append({
                "condition": "random",
                "day": day,
                "prompt_id": p["id"],
                "rep": rep,
                "response": text,
                "system_prompt": personality,
            })
    return results


def run_temporal_condition(
    prompts: list[dict],
    day: int,
    reps: int,
    seed_base: int,
    agent_id: str = "benchmark-agent",
) -> list[dict]:
    """Temporal condition: agent-soul modifiers change each day."""
    # Compute modifiers for this day
    base_date = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    timestamp = base_date + timedelta(days=day)

    modifiers_result = compute_modifiers(agent_id, timestamp)
    personality = modifiers_to_prompt(modifiers_result["modifiers"])

    results = []
    for p in prompts:
        for rep in range(reps):
            seed = seed_base + day * 1000 + int(p["id"][1:]) * 10 + rep
            sys_prompt = personality if personality else None
            text = generate_response(p["prompt"], system_prompt=sys_prompt, seed=seed)
            results.append({
                "condition": "temporal",
                "day": day,
                "prompt_id": p["id"],
                "rep": rep,
                "response": text,
                "system_prompt": personality or "(neutral)",
                "modifiers": modifiers_result["modifiers"],
                "phase": modifiers_result["phase"],
            })
    return results


def run_day(
    prompts: list[dict],
    day: int,
    seed_base: int,
) -> list[dict]:
    """Run all 3 conditions for one day."""
    results = []
    results.extend(run_static_condition(prompts, day, NUM_REPS, seed_base))
    results.extend(run_random_condition(prompts, day, NUM_REPS, seed_base))
    results.extend(run_temporal_condition(prompts, day, NUM_REPS, seed_base))
    return results


def compute_embeddings(results: list[dict]) -> list[dict]:
    """Add embeddings to all results."""
    total = len(results)
    for i, r in enumerate(results):
        if i % 100 == 0:
            print(f"  Embedding {i}/{total}...")
        r["embedding"] = get_embedding(r["response"]).tolist()
    return results


def run_benchmark(seed_base: int = 42) -> Path:
    """Run full 30-day benchmark.

    Returns path to results JSON file.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    prompts = load_prompts()

    all_results = []
    total_start = time.time()

    for day in range(NUM_DAYS):
        day_start = time.time()
        print(f"\n=== Day {day + 1}/{NUM_DAYS} ===")

        day_results = run_day(prompts, day, seed_base)
        all_results.extend(day_results)

        elapsed = time.time() - day_start
        total_elapsed = time.time() - total_start
        est_remaining = (total_elapsed / (day + 1)) * (NUM_DAYS - day - 1)
        print(f"  {len(day_results)} responses in {elapsed:.0f}s "
              f"(total: {total_elapsed / 60:.1f}m, est remaining: {est_remaining / 60:.1f}m)")

    # Compute embeddings
    print(f"\n=== Computing embeddings for {len(all_results)} responses ===")
    all_results = compute_embeddings(all_results)

    # Save results
    output_file = RESULTS_DIR / f"benchmark_seed{seed_base}.json"
    output_file.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved to {output_file}")
    print(f"Total time: {(time.time() - total_start) / 60:.1f} minutes")

    return output_file


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agent Soul Variance Wave Benchmark")
    parser.add_argument("--seed", type=int, default=42, help="Random seed base")
    parser.add_argument("--days", type=int, default=None, help="Override number of days")
    parser.add_argument("--reps", type=int, default=None, help="Override number of reps")
    args = parser.parse_args()

    global NUM_DAYS, NUM_REPS
    if args.days:
        NUM_DAYS = args.days
    if args.reps:
        NUM_REPS = args.reps

    run_benchmark(seed_base=args.seed)


if __name__ == "__main__":
    main()
