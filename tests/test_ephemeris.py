"""Tests for Skyfield ephemeris wrapper — accuracy, retrograde, ayanamsha."""

from datetime import datetime, timezone

import pytest

from clawclaw_soul.ephemeris import get_ayanamsha, get_planet_positions, is_retrograde


class TestGetPlanetPositions:
    def test_returns_all_nine_planets(self):
        """Should return positions for all 9 Vedic planets."""
        dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        positions = get_planet_positions(dt)
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        assert set(positions.keys()) == expected

    def test_position_structure(self):
        """Each planet position should have required fields."""
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        positions = get_planet_positions(dt)
        for planet, pos in positions.items():
            assert "lon" in pos, f"{planet} missing lon"
            assert "sign" in pos, f"{planet} missing sign"
            assert "degree" in pos, f"{planet} missing degree"
            assert "nakshatra" in pos, f"{planet} missing nakshatra"
            assert "pada" in pos, f"{planet} missing pada"
            assert "motion" in pos, f"{planet} missing motion"

    def test_longitude_range(self):
        """All longitudes should be in [0, 360)."""
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        positions = get_planet_positions(dt)
        for planet, pos in positions.items():
            assert 0 <= pos["lon"] < 360, f"{planet} lon {pos['lon']} out of range"

    def test_degree_range(self):
        """Degree within sign should be in [0, 30)."""
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        positions = get_planet_positions(dt)
        for planet, pos in positions.items():
            assert 0 <= pos["degree"] < 30, f"{planet} degree {pos['degree']} out of range"

    def test_pada_range(self):
        """Pada should be 1-4."""
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        positions = get_planet_positions(dt)
        for planet, pos in positions.items():
            assert 1 <= pos["pada"] <= 4, f"{planet} pada {pos['pada']} out of range"

    def test_rahu_ketu_opposite(self):
        """Rahu and Ketu should be ~180 degrees apart."""
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        positions = get_planet_positions(dt)
        diff = abs(positions["Rahu"]["lon"] - positions["Ketu"]["lon"])
        # Handle wraparound
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180) < 1.0, f"Rahu-Ketu difference: {diff}"

    def test_deterministic(self):
        """Same datetime → same positions."""
        dt = datetime(2024, 1, 15, 6, 30, 0, tzinfo=timezone.utc)
        pos1 = get_planet_positions(dt)
        pos2 = get_planet_positions(dt)
        for planet in pos1:
            assert pos1[planet]["lon"] == pos2[planet]["lon"]


class TestAyanamsha:
    def test_j2000_epoch_approximate(self):
        """Ayanamsha at J2000 should be ~23.85 degrees."""
        jd_j2000 = 2451545.0
        aya = get_ayanamsha(jd_j2000)
        assert 23.0 < aya < 25.0, f"Ayanamsha at J2000: {aya}"


class TestRetrograde:
    def test_sun_never_retrograde(self):
        """Sun should never be retrograde."""
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_retrograde("Sun", dt) is False

    def test_rahu_always_retrograde(self):
        """Rahu is always retrograde (mean motion)."""
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_retrograde("Rahu", dt) is True

    def test_ketu_always_retrograde(self):
        """Ketu is always retrograde (mean motion)."""
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_retrograde("Ketu", dt) is True
