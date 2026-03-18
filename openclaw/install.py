"""Soul Oracle skill installer.

Copies SKILL.md to the correct location and generates initial identity
by calling the Soul Oracle API (no local pyswisseph needed).
"""

from __future__ import annotations

import json
import shutil
import sys
import urllib.request
from pathlib import Path

API_URL = "http://185.177.116.94:8432"


def install():
    """Install soul-oracle as an OpenClaw skill."""
    skill_dir = Path.home() / "clawd" / "skills" / "soul-oracle"
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Copy skill files
    src_dir = Path(__file__).parent
    for filename in ["SKILL.md", "openclaw.json"]:
        src = src_dir / filename
        dst = skill_dir / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Installed {filename} -> {dst}")

    # Generate initial identity via API
    print(f"\n  Calling Soul Oracle API ({API_URL})...")
    try:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        payload = json.dumps({
            "timestamp": now.isoformat(),
            "latitude": 0.0,  # Default: prime meridian / equator
            "longitude": 0.0,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{API_URL}/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            soul = json.loads(resp.read().decode("utf-8"))

        cfg = soul["agent_config"]
        persona = soul["persona"]

        print(f"\n  --- Genesis Identity ---")
        print(f"  Lagna: {soul['lagna']}")
        print(f"  Identity Seed: {soul['identity_seed']}")
        print(f"  Temperature: {cfg['temperature']}  Max Tokens: {cfg['max_tokens']}")
        print(f"  Decision Speed: {persona['decision_speed']}")
        print(f"  Assertiveness: {persona['assertiveness']}  "
              f"Creativity: {persona['creativity']}")

        dims = soul.get("dominant_dimensions", {})
        print(f"  Top Dimensions: {dims}")

        yogas = [y["name"] for y in soul.get("yogas", [])]
        if yogas:
            print(f"  Yogas: {', '.join(yogas)}")

        print(f"\n  System Prompt Modifier:")
        print(f"  {soul['system_prompt_modifier'][:120]}...")

    except Exception as e:
        print(f"  Warning: Could not reach API: {e}")
        print(f"  Skill installed, but identity not generated.")
        print(f"  API URL: {API_URL}")


if __name__ == "__main__":
    install()
