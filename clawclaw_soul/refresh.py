"""Refresh module — called by OpenClaw heartbeat or manually.

Usage:
    python -m clawclaw_soul.refresh [--agent-id ID] [--output PATH] [--strict]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from clawclaw_soul.engine import compute_modifiers
from clawclaw_soul.temporal_md import generate_temporal_md, write_temporal_md

CACHE_PATH = Path(os.environ.get("AGENT_SOUL_CACHE", Path.home() / ".agent-soul")) / "cache.json"


def _get_agent_id() -> str:
    """Determine agent ID from environment or hostname."""
    agent_id = os.environ.get("AGENT_SOUL_ID")
    if agent_id:
        return agent_id

    import socket
    return f"agent-{socket.gethostname()}"


def _load_cache() -> dict:
    """Load cache from disk."""
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def _save_cache(cache: dict) -> None:
    """Save cache to disk."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _cache_key(agent_id: str, timestamp: datetime) -> str:
    """Create cache key with 4-hour bucketing."""
    bucket = timestamp.replace(
        hour=(timestamp.hour // 4) * 4,
        minute=0, second=0, microsecond=0
    )
    return f"{agent_id}_{bucket.isoformat()}"


def refresh(
    agent_id: str | None = None,
    output_path: str | Path | None = None,
    strict_mode: bool = False,
    use_cache: bool = True,
) -> dict:
    """Compute modifiers and write TEMPORAL.md.

    Args:
        agent_id: Agent identifier (auto-detected if None)
        output_path: Where to write TEMPORAL.md
        strict_mode: Clamp modifiers to ±0.6
        use_cache: Use cached result if available

    Returns:
        The compute_modifiers result dict
    """
    if agent_id is None:
        agent_id = _get_agent_id()

    now = datetime.now(timezone.utc)
    key = _cache_key(agent_id, now)

    # Check cache
    if use_cache:
        cache = _load_cache()
        if key in cache:
            result = cache[key]
            write_temporal_md(result, output_path)
            return result

    # Compute fresh
    result = compute_modifiers(agent_id, now, strict_mode=strict_mode)

    # Update cache
    cache = _load_cache()
    cache[key] = result
    # Keep only last 24 entries (4 days)
    if len(cache) > 24:
        keys = sorted(cache.keys())
        for old_key in keys[:-24]:
            del cache[old_key]
    _save_cache(cache)

    # Write TEMPORAL.md
    write_temporal_md(result, output_path)

    return result


def main():
    parser = argparse.ArgumentParser(description="Agent Soul — refresh personality modifiers")
    parser.add_argument("--agent-id", help="Agent identifier")
    parser.add_argument("--output", help="Output path for TEMPORAL.md")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode (±0.6 clamp)")
    parser.add_argument("--no-cache", action="store_true", help="Skip cache")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of TEMPORAL.md")
    args = parser.parse_args()

    result = refresh(
        agent_id=args.agent_id,
        output_path=args.output,
        strict_mode=args.strict,
        use_cache=not args.no_cache,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(generate_temporal_md(result))


if __name__ == "__main__":
    main()
