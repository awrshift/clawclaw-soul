"""Tests for core engine — determinism, range bounds, completeness."""

from datetime import datetime, timezone

import pytest

from agent_soul.engine import (
    MODIFIER_NAMES,
    agent_id_to_birth,
    compute_modifiers,
    compute_natal_modifiers,
)


class TestAgentIdToBirth:
    def test_deterministic(self):
        """Same agent_id always produces same birth datetime."""
        dt1 = agent_id_to_birth("test-agent-42")
        dt2 = agent_id_to_birth("test-agent-42")
        assert dt1 == dt2

    def test_different_agents_different_births(self):
        """Different agent_ids produce different birth datetimes."""
        dt1 = agent_id_to_birth("agent-alpha")
        dt2 = agent_id_to_birth("agent-beta")
        assert dt1 != dt2

    def test_birth_in_range(self):
        """Birth datetime falls within 1970-2020."""
        for i in range(100):
            dt = agent_id_to_birth(f"agent-{i}")
            assert dt.year >= 1970
            assert dt.year < 2020


class TestComputeModifiers:
    FIXED_TS = datetime(2026, 3, 13, 12, 0, 0, tzinfo=timezone.utc)

    def test_determinism_100_runs(self):
        """Same inputs → identical output across 100 runs."""
        first = compute_modifiers("test-agent", self.FIXED_TS)
        for _ in range(99):
            result = compute_modifiers("test-agent", self.FIXED_TS)
            assert result == first

    def test_all_modifiers_present(self):
        """Output contains all 5 modifier keys."""
        result = compute_modifiers("test-agent", self.FIXED_TS)
        for name in MODIFIER_NAMES:
            assert name in result["modifiers"]

    def test_modifier_range(self):
        """All modifiers are in [-1, +1]."""
        for i in range(100):
            result = compute_modifiers(f"agent-{i}", self.FIXED_TS)
            for name, value in result["modifiers"].items():
                assert -1.0 <= value <= 1.0, f"{name}={value} out of range for agent-{i}"

    def test_strict_mode_range(self):
        """Strict mode clamps to [-0.6, +0.6]."""
        for i in range(50):
            result = compute_modifiers(f"agent-{i}", self.FIXED_TS, strict_mode=True)
            assert result["strict_mode"] is True
            for name, value in result["modifiers"].items():
                assert -0.6 <= value <= 0.6, f"strict: {name}={value} out of range"

    def test_output_structure(self):
        """Output has all required keys."""
        result = compute_modifiers("test-agent", self.FIXED_TS)
        assert "agent_id" in result
        assert "genesis_timestamp" in result
        assert "computed_at" in result
        assert "modifiers" in result
        assert "phase" in result
        assert "volatility" in result
        assert "strict_mode" in result
        assert "next_refresh" in result

    def test_phase_format(self):
        """Phase is 'MD-AD' format."""
        result = compute_modifiers("test-agent", self.FIXED_TS)
        phase = result["phase"]
        assert "-" in phase
        parts = phase.split("-")
        assert len(parts) == 2

    def test_volatility_range(self):
        """Volatility is in [0, 1]."""
        for i in range(50):
            result = compute_modifiers(f"agent-{i}", self.FIXED_TS)
            assert 0.0 <= result["volatility"] <= 1.0

    def test_different_timestamps_different_transits(self):
        """Different timestamps produce different transit-based modifiers."""
        ts1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ts2 = datetime(2026, 7, 1, tzinfo=timezone.utc)
        r1 = compute_modifiers("test-agent", ts1)
        r2 = compute_modifiers("test-agent", ts2)
        # At least one modifier should differ due to transit changes
        diffs = [abs(r1["modifiers"][m] - r2["modifiers"][m]) for m in MODIFIER_NAMES]
        assert max(diffs) > 0.001

    def test_naive_timestamp_treated_as_utc(self):
        """Naive datetime gets UTC timezone attached."""
        naive = datetime(2026, 3, 13, 12, 0, 0)
        result = compute_modifiers("test-agent", naive)
        assert "+00:00" in result["computed_at"] or "Z" in result["computed_at"]

    def test_next_refresh_4h_ahead(self):
        """next_refresh is ~4 hours after computed_at."""
        result = compute_modifiers("test-agent", self.FIXED_TS)
        computed = datetime.fromisoformat(result["computed_at"])
        refresh = datetime.fromisoformat(result["next_refresh"])
        diff_hours = (refresh - computed).total_seconds() / 3600
        assert abs(diff_hours - 4.0) < 0.01
