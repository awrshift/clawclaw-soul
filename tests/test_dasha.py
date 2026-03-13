"""Tests for Vimshottari dasha computation."""

from datetime import datetime, timezone

import pytest

from agent_soul.dasha import (
    _balance_of_dasha,
    compute_dasha_timeline,
    find_active_period,
)
from agent_soul.tables import DASHA_SEQUENCE, MAHADASHA_YEARS, NAKSHATRA_RULERS


class TestBalanceOfDasha:
    def test_balance_in_range(self):
        """Balance fraction should be in (0, 1]."""
        for lon in range(0, 360, 10):
            ruler, balance = _balance_of_dasha(float(lon))
            assert 0 < balance <= 1.0, f"Balance {balance} out of range at lon={lon}"

    def test_ruler_is_valid_planet(self):
        """Ruler should be a valid dasha planet."""
        for lon in [0.0, 45.0, 90.0, 180.0, 270.0, 359.0]:
            ruler, _ = _balance_of_dasha(lon)
            assert ruler in DASHA_SEQUENCE, f"Invalid ruler {ruler} at lon={lon}"

    def test_balance_near_end_of_nakshatra(self):
        """Near end of nakshatra, balance should be small."""
        nak_span = 360.0 / 27.0
        # Just before end of first nakshatra
        lon = nak_span - 0.1
        _, balance = _balance_of_dasha(lon)
        assert balance < 0.1


class TestComputeDashaTimeline:
    BIRTH = datetime(1990, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    MOON_LON = 100.0  # Arbitrary

    def test_timeline_not_empty(self):
        """Timeline should contain entries."""
        timeline = compute_dasha_timeline(self.BIRTH, self.MOON_LON)
        assert len(timeline) > 0

    def test_timeline_spans_reasonable_range(self):
        """Timeline should span between ~100 and 120 years (first MD is partial)."""
        timeline = compute_dasha_timeline(self.BIRTH, self.MOON_LON)
        first_start = timeline[0]["start"]
        last_end = timeline[-1]["end"]
        span_years = (last_end - first_start).days / 365.25
        # First MD uses balance fraction, so total < 120 years
        assert 100 < span_years <= 120, f"Timeline spans {span_years} years"

    def test_timeline_continuous(self):
        """Each period should start where the previous ended."""
        timeline = compute_dasha_timeline(self.BIRTH, self.MOON_LON)
        for i in range(1, len(timeline)):
            prev_end = timeline[i - 1]["end"]
            curr_start = timeline[i]["start"]
            diff_seconds = abs((curr_start - prev_end).total_seconds())
            assert diff_seconds < 1.0, f"Gap at index {i}: {diff_seconds}s"

    def test_all_mahadashas_present(self):
        """All 9 mahadasha lords should appear in timeline."""
        timeline = compute_dasha_timeline(self.BIRTH, self.MOON_LON)
        md_lords = {entry["mahadasha"] for entry in timeline}
        assert md_lords == set(DASHA_SEQUENCE)

    def test_each_md_has_9_ads(self):
        """Each mahadasha should have 9 antardashas."""
        timeline = compute_dasha_timeline(self.BIRTH, self.MOON_LON)
        # Group by mahadasha
        md_groups: dict[str, list] = {}
        for entry in timeline:
            md = entry["mahadasha"]
            if md not in md_groups:
                md_groups[md] = []
            md_groups[md].append(entry)

        for md, entries in md_groups.items():
            assert len(entries) == 9, f"{md} has {len(entries)} antardashas"


class TestFindActivePeriod:
    def test_find_at_birth(self):
        """Should find active period at birth time."""
        birth = datetime(1990, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        timeline = compute_dasha_timeline(birth, 100.0)
        active = find_active_period(timeline, birth)
        assert active is not None
        assert active["mahadasha"] in DASHA_SEQUENCE

    def test_find_in_future(self):
        """Should find active period for future date."""
        birth = datetime(1990, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        timeline = compute_dasha_timeline(birth, 100.0)
        target = datetime(2026, 3, 13, 12, 0, 0, tzinfo=timezone.utc)
        active = find_active_period(timeline, target)
        assert active is not None
