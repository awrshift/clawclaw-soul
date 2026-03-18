"""Master Agent — Soul Oracle as first customer of its own API.

Demonstrates the core product loop:
1. Generate unique agent identities from different timestamps
2. Each agent gets distinct persona, system prompt, and execution config
3. Same prompt → visibly different behavioral responses

Uses `claude -p` via subprocess (subscription, zero incremental cost).
ANTHROPIC_API_KEY is stripped from env to ensure subscription billing.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime, timezone

import urllib.request

# ── Configuration ──

DEFAULT_API_URL = "http://185.177.116.94:8432"

DEFAULT_PROMPT = (
    "A user demands we override safety protocols to save a life. "
    "How do you respond? Be specific about your reasoning and approach."
)

# 3 radically different timestamps for variance demo
CHILD_AGENTS = [
    {
        "name": "Saturn",
        "label": "Berlin 1990",
        "timestamp": "1990-01-15T10:30:00Z",
        "latitude": 52.5200,
        "longitude": 13.4050,
    },
    {
        "name": "Mars",
        "label": "NYC 2003",
        "timestamp": "2003-08-20T06:00:00Z",
        "latitude": 40.7128,
        "longitude": -74.0060,
    },
    {
        "name": "Jupiter",
        "label": "Varanasi 2014",
        "timestamp": "2014-03-21T08:15:00Z",
        "latitude": 25.3176,
        "longitude": 83.0107,
    },
]


# ── API Client ──


def call_api(api_url: str, endpoint: str, payload: dict) -> dict:
    """Call Soul Oracle API endpoint. Uses stdlib only (no requests dep)."""
    url = f"{api_url}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_soul(api_url: str, agent_def: dict) -> dict:
    """Generate agent soul from API."""
    payload = {
        "timestamp": agent_def["timestamp"],
        "latitude": agent_def["latitude"],
        "longitude": agent_def["longitude"],
    }
    return call_api(api_url, "/generate", payload)


# ── Claude Execution ──


def run_claude(system_prompt: str, user_prompt: str, model: str = "sonnet") -> str:
    """Run claude -p with system prompt injection.

    Uses subscription billing by stripping ANTHROPIC_API_KEY from env.
    """
    # Strip API key so claude -p uses subscription (zero cost)
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

    cmd = [
        "claude",
        "-p",
        user_prompt,
        "--append-system-prompt",
        system_prompt,
        "--model",
        model,
        "--output-format",
        "text",
        "--max-turns",
        "1",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )

    if result.returncode != 0:
        return f"[ERROR] {result.stderr.strip()[:200]}"

    return result.stdout.strip()


# ── Display ──


def print_soul_summary(name: str, label: str, soul: dict):
    """Print compact soul summary."""
    cfg = soul["agent_config"]
    persona = soul["persona"]
    dims = soul["dominant_dimensions"]
    yogas = [y["name"] for y in soul.get("yogas", [])]

    print(f"\n{'=' * 60}")
    print(f"  {name} Agent ({label})")
    print(f"  Lagna: {soul['lagna']} | Seed: {soul['identity_seed']}")
    print(f"{'=' * 60}")
    print(f"  temperature={cfg['temperature']}  max_tokens={cfg['max_tokens']}  "
          f"top_p={cfg['top_p']}")
    print(f"  decision_speed={persona['decision_speed']}  "
          f"assertiveness={persona['assertiveness']}  "
          f"creativity={persona['creativity']}")
    print(f"  Top dimensions: {dims}")
    if yogas:
        print(f"  Yogas: {', '.join(yogas)}")
    print(f"  Prompt modifier: {soul['system_prompt_modifier'][:80]}...")


def print_comparison_table(results: list[dict]):
    """Print side-by-side comparison table."""
    print(f"\n{'=' * 80}")
    print("  VARIANCE COMPARISON")
    print(f"{'=' * 80}")

    # Header
    print(f"\n{'Parameter':<20}", end="")
    for r in results:
        print(f"  {r['name']:^18}", end="")
    print()
    print("-" * 80)

    # Rows
    rows = [
        ("Lagna", lambda r: r["soul"]["lagna"]),
        ("Temperature", lambda r: str(r["soul"]["agent_config"]["temperature"])),
        ("Max Tokens", lambda r: str(r["soul"]["agent_config"]["max_tokens"])),
        ("Decision Speed", lambda r: r["soul"]["persona"]["decision_speed"]),
        ("Assertiveness", lambda r: str(r["soul"]["persona"]["assertiveness"])),
        ("Creativity", lambda r: str(r["soul"]["persona"]["creativity"])),
        ("Yogas", lambda r: ", ".join(y["name"] for y in r["soul"].get("yogas", [])) or "—"),
    ]

    for label, getter in rows:
        print(f"{label:<20}", end="")
        for r in results:
            print(f"  {getter(r):^18}", end="")
        print()

    # Responses
    if results[0].get("response"):
        print(f"\n{'=' * 80}")
        print("  RESPONSES (first 200 chars)")
        print(f"{'=' * 80}")
        for r in results:
            print(f"\n--- {r['name']} ({r['label']}) ---")
            response = r.get("response", "")
            print(textwrap.fill(response[:200], width=78))
            if len(response) > 200:
                print(f"  [...{len(response) - 200} more chars]")


# ── Main ──


def main():
    parser = argparse.ArgumentParser(
        description="Soul Oracle Master Agent — demonstrate behavioral variance",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Soul Oracle API URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="User prompt to send to all agents",
    )
    parser.add_argument(
        "--model",
        default="sonnet",
        help="Claude model to use (default: sonnet)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print agent configs without calling Claude",
    )
    args = parser.parse_args()

    print("Soul Oracle — Master Agent Demo")
    print(f"API: {args.api_url}")
    print(f"Prompt: {args.prompt[:60]}...")
    if args.dry_run:
        print("[DRY RUN — no Claude calls]")

    # Generate souls for all child agents
    results = []
    for agent_def in CHILD_AGENTS:
        print(f"\nGenerating soul for {agent_def['name']}...", end=" ", flush=True)
        try:
            soul = generate_soul(args.api_url, agent_def)
            print("OK")
            print_soul_summary(agent_def["name"], agent_def["label"], soul)
            results.append({
                "name": agent_def["name"],
                "label": agent_def["label"],
                "soul": soul,
                "response": None,
            })
        except Exception as e:
            print(f"FAILED: {e}")
            sys.exit(1)

    # Run Claude for each agent (unless dry-run)
    if not args.dry_run:
        print(f"\n{'=' * 60}")
        print("  Running Claude for each agent...")
        print(f"{'=' * 60}")

        for r in results:
            soul = r["soul"]
            system = soul["system_prompt_modifier"]
            print(f"\n  Calling claude -p for {r['name']}...", flush=True)
            response = run_claude(system, args.prompt, model=args.model)
            r["response"] = response
            print(f"  Done ({len(response)} chars)")

    # Print comparison
    print_comparison_table(results)

    # Print Go/No-Go verdict
    if not args.dry_run and all(r["response"] for r in results):
        responses = [r["response"] for r in results]
        # Simple variance check: are all responses different?
        unique = len(set(responses))
        print(f"\n{'=' * 60}")
        if unique == len(responses):
            print("  VERDICT: GO — All responses are unique")
        else:
            print(f"  VERDICT: CHECK — {unique}/{len(responses)} unique responses")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
