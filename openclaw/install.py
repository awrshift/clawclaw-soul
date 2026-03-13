"""OpenClaw integration installer.

Copies SKILL.md and openclaw.json to the correct locations,
runs initial compute, and displays genesis state.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def install():
    """Install agent-soul as an OpenClaw skill."""
    skill_dir = Path.home() / "clawd" / "skills" / "agent-soul"
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Copy skill files
    src_dir = Path(__file__).parent
    for filename in ["SKILL.md", "openclaw.json"]:
        src = src_dir / filename
        dst = skill_dir / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Installed {filename} -> {dst}")

    # Run initial computation (genesis)
    try:
        from agent_soul.engine import compute_modifiers
        from agent_soul.temporal_md import generate_temporal_md, write_temporal_md

        result = compute_modifiers("default-agent")
        path = write_temporal_md(result)

        print(f"\n  TEMPORAL.md written to {path}")
        print(f"\n--- Genesis State ---")
        print(f"  Agent born: {result['genesis_timestamp']}")
        print(f"  Phase: {result['phase']}")
        print(f"  Volatility: {result['volatility']:.2f}")
        print(f"  Modifiers:")
        for name, value in result["modifiers"].items():
            bar = "+" * max(0, int(value * 10)) + "-" * max(0, int(-value * 10))
            print(f"    {name:20s} {value:+.3f}  {bar}")

    except Exception as e:
        print(f"  Warning: Could not run genesis computation: {e}")
        print("  Run 'python -m agent_soul.refresh' manually after install.")


if __name__ == "__main__":
    install()
