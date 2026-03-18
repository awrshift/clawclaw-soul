"""Tests for engine v2 — 9-dimension Digital Soul pipeline."""

from __future__ import annotations

from datetime import datetime, timezone

from clawclaw_soul.engine import DIMENSION_NAMES, compute_modifiers_v2
from clawclaw_soul.prompt import dimensions_to_prompt
from clawclaw_soul.soul import create_soul


class TestComputeModifiersV2:
    def test_all_dimensions_present(self):
        soul = create_soul(seed=0)
        result = compute_modifiers_v2(soul)
        assert set(result["dimensions"].keys()) == set(DIMENSION_NAMES)

    def test_dimension_range(self):
        for seed in range(20):
            soul = create_soul(seed=seed)
            result = compute_modifiers_v2(soul)
            for dim, val in result["dimensions"].items():
                assert -1.0 <= val <= 1.0, f"{dim}={val} out of range (seed {seed})"

    def test_output_structure(self):
        soul = create_soul(seed=0)
        result = compute_modifiers_v2(soul)
        assert "agent_id" in result
        assert "genesis_timestamp" in result
        assert "computed_at" in result
        assert "lagna" in result
        assert "dimensions" in result
        assert "yogas" in result
        assert "capabilities" in result
        assert "phase" in result
        assert "volatility" in result
        assert "next_refresh" in result

    def test_determinism(self):
        soul = create_soul(seed=42)
        ts = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        r1 = compute_modifiers_v2(soul, timestamp=ts)
        r2 = compute_modifiers_v2(soul, timestamp=ts)
        assert r1["dimensions"] == r2["dimensions"]

    def test_different_timestamps_vary(self):
        soul = create_soul(seed=0)
        ts1 = datetime(2020, 1, 1, tzinfo=timezone.utc)
        ts2 = datetime(2025, 6, 15, tzinfo=timezone.utc)
        r1 = compute_modifiers_v2(soul, timestamp=ts1)
        r2 = compute_modifiers_v2(soul, timestamp=ts2)
        # At least some dimensions should differ due to transits
        diffs = sum(1 for d in DIMENSION_NAMES if r1["dimensions"][d] != r2["dimensions"][d])
        assert diffs > 0, "Same dimensions for different timestamps"

    def test_custom_weights(self):
        soul = create_soul(seed=0)
        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        r_default = compute_modifiers_v2(soul, timestamp=ts)
        r_transit_heavy = compute_modifiers_v2(soul, timestamp=ts, weights=(0.20, 0.25, 0.55))
        # Results should differ with different weights
        assert r_default["dimensions"] != r_transit_heavy["dimensions"]

    def test_volatility_range(self):
        soul = create_soul(seed=0)
        result = compute_modifiers_v2(soul)
        assert 0 <= result["volatility"] <= 1.0

    def test_yogas_passed_through(self):
        soul = create_soul(seed=0)
        result = compute_modifiers_v2(soul)
        assert result["yogas"] == soul.yogas


class TestDimensionsToPrompt:
    def test_all_neutral_empty(self):
        dims = {d: 0.0 for d in DIMENSION_NAMES}
        assert dimensions_to_prompt(dims) == ""

    def test_single_active(self):
        dims = {d: 0.0 for d in DIMENSION_NAMES}
        dims["authority"] = 0.7
        prompt = dimensions_to_prompt(dims)
        assert "Personality" in prompt
        assert len(prompt) > 0

    def test_yoga_included(self):
        dims = {d: 0.0 for d in DIMENSION_NAMES}
        dims["empathy"] = 0.5
        yogas = [
            {"name": "Gaja Kesari", "effect": "empathetic_sage", "planets": ["Moon", "Jupiter"], "description": ""},
        ]
        prompt = dimensions_to_prompt(dims, yogas)
        assert "Behavioral Patterns" in prompt
        assert "empathy" in prompt.lower() or "wisdom" in prompt.lower()

    def test_max_dimensions_limit(self):
        # Set all dimensions high
        dims = {d: 0.9 for d in DIMENSION_NAMES}
        prompt = dimensions_to_prompt(dims)
        # Should have at most MAX_ACTIVE_DIMENSIONS bullet points in Personality
        personality_lines = [line for line in prompt.split("\n") if line.startswith("- ")]
        assert len(personality_lines) <= 5  # 4 dims + possible yoga

    def test_unknown_yoga_effect_ignored(self):
        dims = {d: 0.0 for d in DIMENSION_NAMES}
        dims["authority"] = 0.5
        yogas = [{"name": "Unknown", "effect": "nonexistent_effect", "planets": [], "description": ""}]
        prompt = dimensions_to_prompt(dims, yogas)
        # Should still have personality but no behavioral patterns for unknown effect
        assert "Personality" in prompt


class TestEndToEnd:
    def test_full_pipeline(self):
        """Create soul → compute modifiers → generate prompt."""
        soul = create_soul(seed=7)
        result = compute_modifiers_v2(soul)
        prompt = dimensions_to_prompt(result["dimensions"], result["yogas"])
        # Should produce some non-empty prompt (most agents have active dimensions)
        assert isinstance(prompt, str)

    def test_100_agents_all_valid(self):
        """All 100 agents should produce valid pipeline output."""
        for seed in range(100):
            soul = create_soul(seed=seed)
            result = compute_modifiers_v2(
                soul,
                timestamp=datetime(2025, 6, 1, tzinfo=timezone.utc),
            )
            prompt = dimensions_to_prompt(result["dimensions"], result["yogas"])
            assert isinstance(prompt, str)
            for dim, val in result["dimensions"].items():
                assert -1.0 <= val <= 1.0
