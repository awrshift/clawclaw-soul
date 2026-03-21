#!/usr/bin/env python3
"""Generate unified drift data (daily + monthly + epoch) for the landing page.

Outputs a JSON file with 3 temporal scales and their envelopes.
Used by clawclawsoul.com Temporal Drift section.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent to path so we can import the engine
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clawclaw_soul.engine import DIMENSION_NAMES, compute_modifiers_v2
from clawclaw_soul.soul import generate

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# Jobs epoch — same soul used on the landing page
JOBS_TS = "1955-02-24T19:15:00+00:00"
JOBS_LAT = 37.7749
JOBS_LON = -122.4194

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "drift-unified.json"

MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def dims_to_list(result: dict) -> list[float]:
    """Extract dimensions dict → ordered list of 9 floats."""
    return [round(result["dimensions"][d], 4) for d in DIMENSION_NAMES]


def compute_safe(soul, ts: datetime) -> dict:
    """Compute modifiers using full engine (de440s covers to 2650)."""
    return compute_modifiers_v2(soul, ts)


def compute_envelope(entries: list[list[float]]) -> dict:
    """Per-dimension min/max across all entries."""
    mins = [round(min(e[i] for e in entries), 4) for i in range(9)]
    maxs = [round(max(e[i] for e in entries), 4) for i in range(9)]
    return {"min": mins, "max": maxs}


def generate_daily(soul) -> dict:
    """30 days of March 2026, one entry per day."""
    entries = []
    labels = []
    for day in range(1, 31):
        ts = datetime(2026, 3, day, 12, 0, tzinfo=timezone.utc)
        result = compute_safe(soul, ts)
        entries.append(dims_to_list(result))
        labels.append(f"Mar {day:02d}")
        log.info(f"  daily: {labels[-1]} done")
    return {"entries": entries, "labels": labels, "envelope": compute_envelope(entries)}


def generate_monthly(soul) -> dict:
    """12 months of 2026, mid-month sampling."""
    entries = []
    labels = []
    for month in range(1, 13):
        ts = datetime(2026, month, 15, 12, 0, tzinfo=timezone.utc)
        result = compute_safe(soul, ts)
        entries.append(dims_to_list(result))
        labels.append(f"{MONTHS_SHORT[month - 1]} 26")
        log.info(f"  monthly: {labels[-1]} done")
    return {"entries": entries, "labels": labels, "envelope": compute_envelope(entries)}


def generate_epoch(soul) -> dict:
    """Yearly from 2026 to 2100."""
    entries = []
    labels = []
    for year in range(2026, 2101):
        ts = datetime(year, 1, 1, 12, 0, tzinfo=timezone.utc)
        result = compute_safe(soul, ts)
        entries.append(dims_to_list(result))
        labels.append(str(year))
        log.info(f"  epoch: {year} done")
    return {"entries": entries, "labels": labels, "envelope": compute_envelope(entries)}


def main():
    log.info("Creating Jobs epoch soul...")
    soul = generate(JOBS_TS, latitude=JOBS_LAT, longitude=JOBS_LON)
    log.info(f"  Lagna: {soul.lagna_sign}, Seed: {soul.seed}")

    log.info("Generating daily (30 days, March 2026)...")
    daily = generate_daily(soul)

    log.info("Generating monthly (12 months, 2026)...")
    monthly = generate_monthly(soul)

    log.info("Generating epoch (2026-2100)...")
    epoch = generate_epoch(soul)

    output = {
        "meta": {
            "soul": "jobs-epoch",
            "timestamp": JOBS_TS,
            "lat": JOBS_LAT,
            "lon": JOBS_LON,
            "dimensions": list(DIMENSION_NAMES),
            "generated": datetime.now(timezone.utc).isoformat(),
            "ephemeris": "de440s.bsp (covers 1550-2650 CE, full transit for all dates)",
        },
        "daily": {
            "label": "30 Days",
            "entries": daily["entries"],
            "labels": daily["labels"],
            "envelope": daily["envelope"],
        },
        "monthly": {
            "label": "1 Year",
            "entries": monthly["entries"],
            "labels": monthly["labels"],
            "envelope": monthly["envelope"],
        },
        "epoch": {
            "label": "Century",
            "entries": epoch["entries"],
            "labels": epoch["labels"],
            "envelope": epoch["envelope"],
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # Summary
    daily_range = max(max(d) - min(d) for d in zip(*daily["entries"]))
    epoch_range = max(max(d) - min(d) for d in zip(*epoch["entries"]))
    log.info(f"\nSaved to {OUTPUT_PATH}")
    log.info(f"  Daily envelope max spread:  {daily_range:.4f}")
    log.info(f"  Epoch envelope max spread:  {epoch_range:.4f}")
    log.info(f"  Ratio (epoch/daily):        {epoch_range / daily_range:.1f}x")
    log.info(f"  File size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
