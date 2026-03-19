"""Agent compatibility scoring via 9-dimensional vector comparison.

Computes synergy between two AgentSoul instances using their
graha dimension vectors, dasha state, and nakshatra gana.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clawclaw_soul.soul import AgentSoul


def compatibility(
    soul_a: "AgentSoul",
    soul_b: "AgentSoul",
    timestamp: datetime | None = None,
) -> dict:
    """Compute compatibility between two agent souls.

    Args:
        soul_a: First agent soul
        soul_b: Second agent soul
        timestamp: If provided, use dasha-adjusted dimensions (dynamic).
                   If None, use natal dimensions (static).

    Returns:
        {
            "synergy": float (0-10),
            "tension": bool,
            "dim_alignment": {dim: float},
            "summary": str,
        }
    """
    if timestamp is not None:
        from clawclaw_soul.engine import compute_modifiers_v2
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        dims_a = compute_modifiers_v2(soul_a, timestamp=timestamp)["dimensions"]
        dims_b = compute_modifiers_v2(soul_b, timestamp=timestamp)["dimensions"]
    else:
        dims_a = soul_a.dimensions
        dims_b = soul_b.dimensions

    # Per-dimension alignment: 1.0 = same, -1.0 = opposite
    dim_keys = sorted(set(dims_a.keys()) & set(dims_b.keys()))
    dim_alignment = {}
    sq_dist = 0.0
    for dim in dim_keys:
        a = dims_a[dim]
        b = dims_b[dim]
        diff = a - b
        sq_dist += diff ** 2
        # Alignment: 1 - normalized absolute difference
        dim_alignment[dim] = round(1.0 - abs(diff), 4)

    # Synergy = normalized inverse Euclidean distance, scaled to 0-10
    # Max possible distance for 9 dims each ranging [-1, 1] = sqrt(9 * 4) = 6.0
    euclidean = math.sqrt(sq_dist)
    max_dist = math.sqrt(len(dim_keys) * 4.0)  # each dim range is 2.0
    synergy = round((1.0 - euclidean / max_dist) * 10.0, 2)
    synergy = max(0.0, min(10.0, synergy))

    # Tension: gana incompatibility (Deva + Rakshasa)
    tension = False
    ganas = {soul_a.moon_gana, soul_b.moon_gana}
    if ganas == {"Deva", "Rakshasa"}:
        tension = True

    # Summary
    if synergy >= 8.0:
        level = "Highly compatible"
    elif synergy >= 5.0:
        level = "Moderately compatible"
    elif synergy >= 3.0:
        level = "Low compatibility"
    else:
        level = "Challenging pairing"

    tension_note = " (gana tension: Deva-Rakshasa conflict)" if tension else ""
    dynamic_note = " [dynamic, dasha-adjusted]" if timestamp else " [static, natal]"
    summary = f"{level} (synergy: {synergy}/10){tension_note}{dynamic_note}"

    return {
        "synergy": synergy,
        "tension": tension,
        "dim_alignment": dim_alignment,
        "summary": summary,
    }
