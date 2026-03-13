"""Vimshottari dasha computation — pure math, zero external dependencies."""

from __future__ import annotations

from datetime import datetime, timedelta

from agent_soul.tables import DASHA_SEQUENCE, MAHADASHA_YEARS, NAKSHATRA_RULERS

TOTAL_DASHA_YEARS = 120  # Sum of all mahadasha years


def _nakshatra_index(moon_lon: float) -> int:
    """Get nakshatra index (0-26) from sidereal Moon longitude."""
    nak_span = 360.0 / 27.0
    return int(moon_lon / nak_span) % 27


def _balance_of_dasha(moon_lon: float) -> tuple[str, float]:
    """Compute remaining balance of birth dasha.

    Returns:
        (ruler_planet, balance_fraction) where balance_fraction is in [0, 1]
    """
    nak_span = 360.0 / 27.0
    nak_index = _nakshatra_index(moon_lon)
    ruler = NAKSHATRA_RULERS[nak_index]

    pos_in_nak = moon_lon % nak_span
    # Balance = remaining portion of nakshatra
    balance_fraction = (nak_span - pos_in_nak) / nak_span

    return ruler, balance_fraction


def compute_dasha_timeline(
    birth_dt: datetime, moon_lon: float
) -> list[dict]:
    """Compute full Vimshottari dasha timeline (MD + AD + PD).

    Args:
        birth_dt: Birth datetime (UTC)
        moon_lon: Sidereal Moon longitude at birth (0-360)

    Returns:
        List of dicts with keys: mahadasha, antardasha, start, end
    """
    ruler, balance = _balance_of_dasha(moon_lon)

    # Find starting position in dasha sequence
    start_idx = DASHA_SEQUENCE.index(ruler)
    current_date = birth_dt

    timeline = []

    # Generate 120 years of dashas (full cycle)
    for cycle_offset in range(9):  # 9 mahadashas cover 120 years
        md_idx = (start_idx + cycle_offset) % 9
        md_lord = DASHA_SEQUENCE[md_idx]
        md_years = MAHADASHA_YEARS[md_lord]

        # First MD gets balance, rest get full duration
        if cycle_offset == 0:
            md_duration_years = md_years * balance
        else:
            md_duration_years = md_years

        if md_duration_years <= 0:
            continue

        md_start = current_date

        # Generate antardashas within this mahadasha
        ad_start = md_start
        for ad_offset in range(9):
            ad_idx = (md_idx + ad_offset) % 9
            ad_lord = DASHA_SEQUENCE[ad_idx]
            ad_years = MAHADASHA_YEARS[ad_lord]

            # AD duration = (MD years * AD years) / 120
            ad_duration_years = (md_duration_years * ad_years) / TOTAL_DASHA_YEARS
            ad_duration_days = ad_duration_years * 365.25
            ad_end = ad_start + timedelta(days=ad_duration_days)

            timeline.append({
                "mahadasha": md_lord,
                "antardasha": ad_lord,
                "start": ad_start,
                "end": ad_end,
            })

            ad_start = ad_end

        current_date = ad_start

    return timeline


def find_active_period(
    timeline: list[dict], target_dt: datetime
) -> dict | None:
    """Find the active dasha period for a given datetime.

    Args:
        timeline: Output from compute_dasha_timeline
        target_dt: Target datetime to find period for

    Returns:
        Dict with mahadasha, antardasha, start, end — or None if outside range
    """
    for period in timeline:
        if period["start"] <= target_dt < period["end"]:
            return period

    # If target is after all periods, return last period
    if timeline and target_dt >= timeline[-1]["end"]:
        return timeline[-1]

    return None
