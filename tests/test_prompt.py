"""Tests for prompt translation — levels, dead zone, clamping."""

import pytest

from agent_soul.prompt import (
    CLAMP_THRESHOLD,
    DEAD_ZONE,
    MAX_ACTIVE_MODIFIERS,
    modifiers_to_prompt,
    value_to_level,
)


class TestValueToLevel:
    def test_dead_zone_zero(self):
        """Values in dead zone should map to 0."""
        assert value_to_level(0.0) == 0
        assert value_to_level(0.10) == 0
        assert value_to_level(-0.10) == 0
        assert value_to_level(DEAD_ZONE) == 0
        assert value_to_level(-DEAD_ZONE) == 0

    def test_positive_levels(self):
        """Positive values above dead zone should map to 1, 2, or 3."""
        assert value_to_level(0.20) == 1
        assert value_to_level(0.60) == 2
        assert value_to_level(0.90) == 3

    def test_negative_levels(self):
        """Negative values below dead zone should map to -1, -2, or -3."""
        assert value_to_level(-0.20) == -1
        assert value_to_level(-0.60) == -2
        assert value_to_level(-0.90) == -3

    def test_clamp_at_threshold(self):
        """Values at/beyond clamp threshold should be ±3."""
        assert value_to_level(CLAMP_THRESHOLD) == 3
        assert value_to_level(-CLAMP_THRESHOLD) == -3
        assert value_to_level(1.0) == 3
        assert value_to_level(-1.0) == -3


class TestModifiersToPrompt:
    def test_all_neutral_empty(self):
        """All neutral modifiers should produce empty string."""
        mods = {
            "verbosity": 0.0,
            "agreeableness": 0.05,
            "creativity": -0.10,
            "risk_tolerance": 0.15,
            "proactivity": -0.15,
        }
        assert modifiers_to_prompt(mods) == ""

    def test_single_active(self):
        """Single active modifier should appear in output."""
        mods = {
            "verbosity": 0.7,
            "agreeableness": 0.0,
            "creativity": 0.0,
            "risk_tolerance": 0.0,
            "proactivity": 0.0,
        }
        result = modifiers_to_prompt(mods)
        assert "## Personality" in result
        assert len(result) > 0

    def test_max_active_limit(self):
        """Output should have at most MAX_ACTIVE_MODIFIERS entries."""
        mods = {
            "verbosity": 0.9,
            "agreeableness": 0.8,
            "creativity": 0.7,
            "risk_tolerance": 0.6,
            "proactivity": 0.5,
        }
        result = modifiers_to_prompt(mods)
        # Count bullet points
        bullet_count = result.count("- ")
        assert bullet_count <= MAX_ACTIVE_MODIFIERS

    def test_strongest_modifiers_kept(self):
        """Strongest modifiers should be kept when exceeding max."""
        mods = {
            "verbosity": 0.95,      # strongest
            "agreeableness": 0.90,   # second
            "creativity": 0.85,     # third
            "risk_tolerance": 0.20, # weakest — should be dropped
            "proactivity": 0.18,    # weakest — should be dropped
        }
        result = modifiers_to_prompt(mods)
        # The top 3 should be present, bottom 2 dropped
        assert "exhaustive" in result.lower() or "detailed" in result.lower()

    def test_contains_personality_header(self):
        """Non-empty output should start with personality header."""
        mods = {"verbosity": 0.5, "agreeableness": 0.0, "creativity": 0.0,
                "risk_tolerance": 0.0, "proactivity": 0.0}
        result = modifiers_to_prompt(mods)
        assert result.startswith("## Personality")
