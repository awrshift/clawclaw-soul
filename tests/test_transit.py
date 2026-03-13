"""Tests for Gochar (transit) scoring."""

import pytest

from agent_soul.transit import check_vedha, compute_transit_scores, score_transit


class TestScoreTransit:
    def test_favorable_strong_house(self):
        """Favorable planet in strong house should score high."""
        score = score_transit("Sun", 10, is_favorable=True, vedha_cancelled=False)
        assert score > 0.5

    def test_favorable_vedha_cancelled(self):
        """Vedha cancellation should zero out favorable score."""
        score = score_transit("Sun", 10, is_favorable=True, vedha_cancelled=True)
        assert score == 0.0

    def test_unfavorable_dusthana(self):
        """Unfavorable planet in dusthana should score negative."""
        score = score_transit("Mars", 8, is_favorable=False, vedha_cancelled=False)
        assert score < 0

    def test_score_range(self):
        """All scores should be in [-1, +1]."""
        for house in range(1, 13):
            for fav in [True, False]:
                for vedha in [True, False]:
                    s = score_transit("Sun", house, fav, vedha)
                    assert -1.0 <= s <= 1.0


class TestCheckVedha:
    def test_no_vedha_when_empty(self):
        """No vedha when no other planets present."""
        result = check_vedha("Sun", 3, {"Sun": 3})
        assert result is False

    def test_vedha_triggered(self):
        """Vedha should trigger when obstruction house is occupied."""
        # Sun in house 3, vedha pair is 3:9
        all_houses = {"Sun": 3, "Mars": 9}
        result = check_vedha("Sun", 3, all_houses)
        assert result is True

    def test_vedha_not_triggered_wrong_house(self):
        """Vedha should not trigger when wrong house occupied."""
        all_houses = {"Sun": 3, "Mars": 7}
        result = check_vedha("Sun", 3, all_houses)
        assert result is False


class TestComputeTransitScores:
    def test_returns_all_planets(self):
        """Should return scores for all planets in positions."""
        positions = {
            "Sun": {"sign": "Aries", "lon": 15.0},
            "Moon": {"sign": "Cancer", "lon": 105.0},
            "Mars": {"sign": "Leo", "lon": 130.0},
            "Mercury": {"sign": "Taurus", "lon": 45.0},
            "Jupiter": {"sign": "Gemini", "lon": 75.0},
            "Venus": {"sign": "Pisces", "lon": 345.0},
            "Saturn": {"sign": "Aquarius", "lon": 315.0},
            "Rahu": {"sign": "Virgo", "lon": 165.0},
            "Ketu": {"sign": "Pisces", "lon": 345.0},
        }
        scores = compute_transit_scores(positions, "Aries")
        assert len(scores) == 9
        for planet, score in scores.items():
            assert -1.0 <= score <= 1.0, f"{planet} score {score} out of range"

    def test_score_range_various_moons(self):
        """Scores should be in range for various natal Moon signs."""
        positions = {
            "Sun": {"sign": "Leo", "lon": 130.0},
            "Moon": {"sign": "Taurus", "lon": 45.0},
            "Mars": {"sign": "Aries", "lon": 10.0},
            "Mercury": {"sign": "Virgo", "lon": 165.0},
            "Jupiter": {"sign": "Sagittarius", "lon": 255.0},
            "Venus": {"sign": "Libra", "lon": 195.0},
            "Saturn": {"sign": "Capricorn", "lon": 280.0},
            "Rahu": {"sign": "Gemini", "lon": 75.0},
            "Ketu": {"sign": "Sagittarius", "lon": 255.0},
        }
        for moon_sign in ["Aries", "Cancer", "Libra", "Capricorn"]:
            scores = compute_transit_scores(positions, moon_sign)
            for planet, score in scores.items():
                assert -1.0 <= score <= 1.0
