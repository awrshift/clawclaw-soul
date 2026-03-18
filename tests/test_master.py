"""Tests for Master Agent script."""

import json
from unittest.mock import patch, MagicMock

import pytest

from app.master import (
    call_api,
    generate_soul,
    print_comparison_table,
    print_soul_summary,
    CHILD_AGENTS,
    DEFAULT_API_URL,
)


# Sample API response for mocking
SAMPLE_SOUL = {
    "agent_config": {
        "temperature": 0.96,
        "max_tokens": 943,
        "top_p": 0.94,
        "frequency_penalty": -0.17,
    },
    "persona": {
        "assertiveness": 0.614,
        "empathy": 0.641,
        "risk_tolerance": 0.75,
        "analytical_depth": 0.335,
        "creativity": 0.654,
        "decision_speed": "impulsive",
    },
    "system_prompt_modifier": "Deliberate, thorough. Values concrete evidence over speculation.",
    "tool_preferences": {"identity": "preferred", "memory": "restricted"},
    "identity_seed": "632399400/52.5200/13.4050",
    "lagna": "Taurus",
    "dominant_dimensions": {"execution": 0.68, "empathy": 0.49, "restriction": -0.46},
    "yogas": [{"name": "Kemadruma", "effect": "raw_output"}],
    "retrograde": ["Mercury", "Jupiter", "Venus"],
}


class TestChildAgents:
    """Verify child agent definitions."""

    def test_three_child_agents_defined(self):
        assert len(CHILD_AGENTS) == 3

    def test_each_agent_has_required_fields(self):
        for agent in CHILD_AGENTS:
            assert "name" in agent
            assert "label" in agent
            assert "timestamp" in agent
            assert "latitude" in agent
            assert "longitude" in agent

    def test_all_timestamps_different(self):
        timestamps = [a["timestamp"] for a in CHILD_AGENTS]
        assert len(set(timestamps)) == 3

    def test_all_coordinates_different(self):
        coords = [(a["latitude"], a["longitude"]) for a in CHILD_AGENTS]
        assert len(set(coords)) == 3


class TestGenerateSoul:
    """Test API call to generate soul (mocked)."""

    @patch("app.master.urllib.request.urlopen")
    def test_generate_soul_calls_api(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(SAMPLE_SOUL).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = generate_soul(DEFAULT_API_URL, CHILD_AGENTS[0])

        assert result["lagna"] == "Taurus"
        assert result["agent_config"]["temperature"] == 0.96
        assert mock_urlopen.called

    @patch("app.master.urllib.request.urlopen")
    def test_generate_soul_sends_correct_payload(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(SAMPLE_SOUL).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        generate_soul(DEFAULT_API_URL, CHILD_AGENTS[0])

        call_args = mock_urlopen.call_args[0][0]
        payload = json.loads(call_args.data.decode())
        assert payload["timestamp"] == CHILD_AGENTS[0]["timestamp"]
        assert payload["latitude"] == CHILD_AGENTS[0]["latitude"]
        assert payload["longitude"] == CHILD_AGENTS[0]["longitude"]


class TestDisplay:
    """Test display functions don't crash."""

    def test_print_soul_summary(self, capsys):
        print_soul_summary("Saturn", "Berlin 1990", SAMPLE_SOUL)
        captured = capsys.readouterr()
        assert "Saturn Agent" in captured.out
        assert "Taurus" in captured.out
        assert "Kemadruma" in captured.out

    def test_print_comparison_table(self, capsys):
        results = [
            {"name": "A", "label": "Test A", "soul": SAMPLE_SOUL, "response": None},
            {"name": "B", "label": "Test B", "soul": SAMPLE_SOUL, "response": None},
        ]
        print_comparison_table(results)
        captured = capsys.readouterr()
        assert "VARIANCE COMPARISON" in captured.out
        assert "Taurus" in captured.out

    def test_print_comparison_with_responses(self, capsys):
        results = [
            {"name": "A", "label": "Test A", "soul": SAMPLE_SOUL,
             "response": "I would carefully consider the situation."},
            {"name": "B", "label": "Test B", "soul": SAMPLE_SOUL,
             "response": "Override immediately. Lives are at stake."},
        ]
        print_comparison_table(results)
        captured = capsys.readouterr()
        assert "RESPONSES" in captured.out


def _api_available() -> bool:
    """Check if Soul Oracle API is reachable."""
    try:
        import urllib.request
        with urllib.request.urlopen(f"{DEFAULT_API_URL}/health", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


class TestDryRunIntegration:
    """Integration test: dry-run calls real API (if available)."""

    @pytest.mark.skipif(
        not _api_available(),
        reason="Soul Oracle API not reachable",
    )
    def test_dry_run_produces_three_unique_souls(self):
        souls = []
        for agent_def in CHILD_AGENTS:
            soul = generate_soul(DEFAULT_API_URL, agent_def)
            souls.append(soul)

        # All temperatures should be different
        temps = [s["agent_config"]["temperature"] for s in souls]
        assert len(set(temps)) == 3

        # All lagnas might differ (not guaranteed but likely)
        lagnas = [s["lagna"] for s in souls]
        assert len(set(lagnas)) >= 2  # at least 2 different
