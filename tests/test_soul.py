"""Tests for Digital Soul (soul.py) — natal chart creation and scoring."""

from __future__ import annotations

from datetime import datetime, timezone

from clawclaw_soul.soul import (
    AgentSoul,
    DIMENSION_NAMES,
    GRAHA_TO_DIMENSION,
    HOUSE_DOMAINS,
    check_combustion,
    compute_all_dimensions,
    compute_aspects,
    compute_houses,
    compute_lagna,
    compute_planet_positions,
    create_soul,
    detect_yogas,
    generate_birth_data,
)


class TestGenerateBirthData:
    def test_reproducibility(self):
        b1 = generate_birth_data(seed=42)
        b2 = generate_birth_data(seed=42)
        assert b1["latitude"] == b2["latitude"]
        assert b1["longitude"] == b2["longitude"]
        assert b1["birth_dt"] == b2["birth_dt"]

    def test_different_seeds_differ(self):
        b1 = generate_birth_data(seed=0)
        b2 = generate_birth_data(seed=1)
        assert b1["latitude"] != b2["latitude"]

    def test_latitude_range(self):
        for seed in range(50):
            b = generate_birth_data(seed=seed)
            assert -60.0 <= b["latitude"] <= 60.0

    def test_longitude_range(self):
        for seed in range(50):
            b = generate_birth_data(seed=seed)
            assert -180.0 <= b["longitude"] <= 180.0

    def test_birth_dt_range(self):
        for seed in range(50):
            b = generate_birth_data(seed=seed)
            assert b["birth_dt"].year >= 1970
            assert b["birth_dt"].year <= 2024


class TestComputeLagna:
    def test_lagna_range(self):
        """Lagna should be 0-360 sidereal degrees."""
        for seed in range(20):
            b = generate_birth_data(seed=seed)
            import swisseph as swe
            jd = swe.julday(
                b["birth_dt"].year, b["birth_dt"].month,
                b["birth_dt"].day,
                b["birth_dt"].hour + b["birth_dt"].minute / 60.0,
            )
            lagna = compute_lagna(jd, b["latitude"], b["longitude"])
            assert 0 <= lagna < 360, f"Lagna {lagna} out of range for seed {seed}"

    def test_different_locations_differ(self):
        """Different locations at same time should give different Lagnas."""
        import swisseph as swe
        jd = swe.julday(2000, 1, 1, 12.0)
        l1 = compute_lagna(jd, 0.0, 0.0)
        l2 = compute_lagna(jd, 50.0, 100.0)
        assert l1 != l2


class TestComputePlanetPositions:
    def test_all_nine_planets(self):
        import swisseph as swe
        jd = swe.julday(2000, 1, 1, 12.0)
        pos = compute_planet_positions(jd)
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        assert set(pos.keys()) == expected

    def test_position_structure(self):
        import swisseph as swe
        jd = swe.julday(2000, 1, 1, 12.0)
        pos = compute_planet_positions(jd)
        for planet, data in pos.items():
            assert "lon" in data
            assert "sign" in data
            assert "degree" in data
            assert "nakshatra" in data
            assert "pada" in data
            assert "retrograde" in data
            assert 0 <= data["lon"] < 360
            assert 0 <= data["degree"] < 30

    def test_rahu_ketu_opposite(self):
        import swisseph as swe
        jd = swe.julday(2000, 1, 1, 12.0)
        pos = compute_planet_positions(jd)
        diff = abs(pos["Rahu"]["lon"] - pos["Ketu"]["lon"])
        assert abs(diff - 180.0) < 1.0


class TestComputeHouses:
    def test_twelve_houses(self):
        soul = create_soul(seed=0)
        assert len(soul.houses) == 12

    def test_house_numbers(self):
        soul = create_soul(seed=0)
        numbers = [h["number"] for h in soul.houses]
        assert numbers == list(range(1, 13))

    def test_all_planets_placed(self):
        soul = create_soul(seed=0)
        placed = set()
        for h in soul.houses:
            placed.update(h["planets"])
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        assert placed == expected

    def test_consecutive_signs(self):
        """Houses should have consecutive zodiac signs (Whole Sign)."""
        from clawclaw_soul.tables import SIGNS, SIGN_INDEX
        soul = create_soul(seed=0)
        first_sign_idx = SIGN_INDEX[soul.houses[0]["sign"]]
        for i, h in enumerate(soul.houses):
            expected_idx = (first_sign_idx + i) % 12
            assert SIGN_INDEX[h["sign"]] == expected_idx


class TestAspects:
    def test_aspects_keys(self):
        soul = create_soul(seed=0)
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        assert set(soul.aspects.keys()) == expected

    def test_no_self_aspect(self):
        """A planet should never aspect itself."""
        for seed in range(20):
            soul = create_soul(seed=seed)
            for planet, aspectors in soul.aspects.items():
                assert planet not in aspectors, f"{planet} aspects itself in seed {seed}"


class TestCombustion:
    def test_sun_not_combust(self):
        """Sun is never combust (it causes combustion)."""
        for seed in range(20):
            soul = create_soul(seed=seed)
            assert "Sun" not in soul.combustion

    def test_rahu_ketu_not_combust(self):
        """Rahu/Ketu are not subject to combustion."""
        for seed in range(20):
            soul = create_soul(seed=seed)
            assert "Rahu" not in soul.combustion
            assert "Ketu" not in soul.combustion


class TestDimensions:
    def test_all_nine_dimensions(self):
        soul = create_soul(seed=0)
        assert set(soul.dimensions.keys()) == set(GRAHA_TO_DIMENSION.values())

    def test_dimension_range(self):
        for seed in range(100):
            soul = create_soul(seed=seed)
            for dim, val in soul.dimensions.items():
                assert -1.0 <= val <= 1.0, f"{dim}={val} out of range (seed {seed})"

    def test_dimensions_vary_across_seeds(self):
        """Dimensions should vary — not all the same."""
        vals = set()
        for seed in range(20):
            soul = create_soul(seed=seed)
            vals.add(round(soul.dimensions["authority"], 2))
        assert len(vals) > 3, "Authority dimension too uniform across 20 agents"


class TestCapabilities:
    def test_all_twelve_capabilities(self):
        soul = create_soul(seed=0)
        assert set(soul.capabilities.keys()) == set(HOUSE_DOMAINS.values())

    def test_capability_range(self):
        for seed in range(50):
            soul = create_soul(seed=seed)
            for cap, val in soul.capabilities.items():
                assert -1.0 <= val <= 1.0, f"{cap}={val} out of range (seed {seed})"


class TestYogas:
    def test_yoga_structure(self):
        """All detected yogas should have required keys."""
        for seed in range(100):
            soul = create_soul(seed=seed)
            for yoga in soul.yogas:
                assert "name" in yoga
                assert "planets" in yoga
                assert "effect" in yoga
                assert "description" in yoga

    def test_some_yogas_detected(self):
        """At least some agents should have yogas."""
        total_yogas = sum(len(create_soul(seed=i).yogas) for i in range(100))
        assert total_yogas > 10, f"Only {total_yogas} yogas in 100 agents"


class TestLagnaDiversity:
    def test_all_12_lagnas_in_100(self):
        lagnas = set()
        for seed in range(100):
            lagnas.add(create_soul(seed=seed).lagna_sign)
        assert len(lagnas) == 12


class TestCreateSoul:
    def test_reproducibility(self):
        s1 = create_soul(seed=7)
        s2 = create_soul(seed=7)
        assert s1.dimensions == s2.dimensions
        assert s1.lagna_sign == s2.lagna_sign
        assert s1.moon_nakshatra == s2.moon_nakshatra

    def test_to_dict(self):
        soul = create_soul(seed=0)
        d = soul.to_dict()
        assert "birth_dt" in d
        assert "lagna_sign" in d
        assert "dimensions" in d
        assert "capabilities" in d
        assert "yogas" in d
        assert "seed" in d

    def test_summary_not_empty(self):
        soul = create_soul(seed=0)
        s = soul.summary()
        assert "Agent Soul" in s
        assert soul.lagna_sign in s
