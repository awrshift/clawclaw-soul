"""Tests for yogas.py — full yoga detection engine."""

from __future__ import annotations

from clawclaw_soul.soul import create_soul
from clawclaw_soul.yogas import YOGA_META, compute_yoga_dimensions, detect_yogas_full


class TestYogaStructure:
    def test_all_yogas_have_required_keys(self):
        """All detected yogas must have name, planets, effect, description."""
        for seed in range(100):
            soul = create_soul(seed=seed)
            for yoga in soul.yogas:
                assert "name" in yoga, f"Missing 'name' in yoga (seed {seed})"
                assert "planets" in yoga, f"Missing 'planets' in yoga (seed {seed})"
                assert "effect" in yoga, f"Missing 'effect' in yoga (seed {seed})"
                assert "description" in yoga, f"Missing 'description' in yoga (seed {seed})"
                assert "type" in yoga, f"Missing 'type' in yoga (seed {seed})"
                assert "category" in yoga, f"Missing 'category' in yoga (seed {seed})"

    def test_effect_is_nonempty_string(self):
        for seed in range(50):
            soul = create_soul(seed=seed)
            for yoga in soul.yogas:
                assert isinstance(yoga["effect"], str)
                assert len(yoga["effect"]) > 0

    def test_type_values(self):
        """Type must be 'auspicious' or 'challenging'."""
        for seed in range(50):
            soul = create_soul(seed=seed)
            for yoga in soul.yogas:
                assert yoga["type"] in ("auspicious", "challenging"), (
                    f"Bad type '{yoga['type']}' for {yoga['name']} (seed {seed})"
                )


class TestYogaMetaCoverage:
    def test_meta_has_required_keys(self):
        for name, meta in YOGA_META.items():
            assert "dims" in meta, f"Missing 'dims' in YOGA_META['{name}']"
            assert "polarity" in meta, f"Missing 'polarity' in YOGA_META['{name}']"
            assert "lord" in meta, f"Missing 'lord' in YOGA_META['{name}']"
            assert meta["polarity"] in (+1, -1), f"Bad polarity for '{name}'"
            assert len(meta["dims"]) >= 1, f"Empty dims for '{name}'"
            assert len(meta["dims"]) <= 2, f"Too many dims for '{name}'"

    def test_dims_are_valid(self):
        valid_dims = {
            "authority", "empathy", "execution", "analysis",
            "wisdom", "aesthetics", "restriction", "innovation", "compression",
        }
        for name, meta in YOGA_META.items():
            for dim in meta["dims"]:
                assert dim in valid_dims, f"Invalid dim '{dim}' in YOGA_META['{name}']"


class TestYogaDimensions:
    def test_dimension_range(self):
        """Net yoga dimension values should be capped at ±0.3."""
        for seed in range(50):
            soul = create_soul(seed=seed)
            yd = soul.yoga_dimensions
            if yd.get("net"):
                for dim, val in yd["net"].items():
                    assert -0.3 <= val <= 0.3, f"{dim}={val} out of range (seed {seed})"

    def test_volatility_non_negative(self):
        for seed in range(50):
            soul = create_soul(seed=seed)
            yd = soul.yoga_dimensions
            if yd.get("volatility"):
                for dim, val in yd["volatility"].items():
                    assert val >= 0.0, f"Negative volatility {dim}={val} (seed {seed})"

    def test_conflicts_are_strings(self):
        for seed in range(50):
            soul = create_soul(seed=seed)
            yd = soul.yoga_dimensions
            if yd.get("conflicts"):
                for c in yd["conflicts"]:
                    assert isinstance(c, str)

    def test_compute_yoga_dimensions_empty(self):
        result = compute_yoga_dimensions([])
        assert result["net"] == {}
        assert result["conflicts"] == []


class TestYogaVolume:
    def test_more_yogas_than_v02(self):
        """v0.3 should detect significantly more yogas than the old 6-detector system."""
        total_yogas = sum(len(create_soul(seed=i).yogas) for i in range(100))
        # Old system: ~30-50 yogas across 100 agents
        # New system: should be much more with 55 detectors
        assert total_yogas > 100, f"Only {total_yogas} yogas in 100 agents — expected more"

    def test_diverse_yoga_names(self):
        """Should detect many different yoga types."""
        names = set()
        for seed in range(100):
            soul = create_soul(seed=seed)
            for yoga in soul.yogas:
                names.add(yoga["name"])
        assert len(names) > 10, f"Only {len(names)} unique yoga types in 100 agents"


class TestDetectYogasFull:
    def test_returns_list(self):
        soul = create_soul(seed=0)
        result = detect_yogas_full(soul.positions, soul.houses, soul.combustion)
        assert isinstance(result, list)

    def test_sorted_auspicious_first(self):
        """Auspicious yogas should come before challenging ones."""
        soul = create_soul(seed=0)
        yogas = soul.yogas
        if len(yogas) > 1:
            saw_challenging = False
            for y in yogas:
                if y["type"] == "challenging":
                    saw_challenging = True
                elif y["type"] == "auspicious" and saw_challenging:
                    assert False, "Auspicious yoga found after challenging ones"
