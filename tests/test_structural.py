"""Tests for structural prompts and proxy metrics (CVB v3 / Brainstorm 004)."""

from __future__ import annotations

import pytest

from agent_soul.prompt import (
    dimensions_to_structural_prompt,
    STRUCTURAL_CONSTRAINTS,
)
from benchmark.proxy_metrics import compute_proxies, compute_batch


# ──────────────────────────────────────────────
# Structural Prompt Tests
# ──────────────────────────────────────────────

class TestDimensionsToStructuralPrompt:
    """Test continuous structural prompt generation."""

    def test_returns_string(self):
        dims = {"empathy": 0.0, "execution": 0.0, "authority": 0.0}
        result = dimensions_to_structural_prompt(dims)
        assert isinstance(result, str)
        assert "## Response Format" in result

    def test_always_includes_three_constraints(self):
        """Should always produce word count, bullet, and sentence instructions."""
        dims = {"empathy": 0.0, "execution": 0.0, "authority": 0.0}
        result = dimensions_to_structural_prompt(dims)
        assert "words" in result
        assert "sentences" in result
        # Either "bullet" or "prose" should be present
        assert "bullet" in result or "prose" in result

    def test_high_empathy_high_word_count(self):
        """High empathy → more words."""
        low = dimensions_to_structural_prompt({"empathy": -0.8})
        high = dimensions_to_structural_prompt({"empathy": 0.8})
        # Extract word counts
        import re
        low_wc = int(re.search(r"approximately (\d+) words", low).group(1))
        high_wc = int(re.search(r"approximately (\d+) words", high).group(1))
        assert high_wc > low_wc

    def test_extreme_empathy_word_limits(self):
        """Extreme values should hit the bounds."""
        import re
        low = dimensions_to_structural_prompt({"empathy": -1.0})
        high = dimensions_to_structural_prompt({"empathy": 1.0})
        low_wc = int(re.search(r"approximately (\d+) words", low).group(1))
        high_wc = int(re.search(r"approximately (\d+) words", high).group(1))
        assert low_wc == 30
        assert high_wc == 250

    def test_high_execution_more_bullets(self):
        """High execution → more bullet points."""
        import re
        low = dimensions_to_structural_prompt({"execution": -0.8})
        high = dimensions_to_structural_prompt({"execution": 0.8})
        low_match = re.search(r"exactly (\d+) bullet", low)
        high_match = re.search(r"exactly (\d+) bullet", high)
        if low_match and high_match:
            assert int(high_match.group(1)) > int(low_match.group(1))
        elif not low_match:
            # Low execution = prose (0 bullets)
            assert "prose" in low
            assert high_match is not None

    def test_zero_bullets_gives_prose(self):
        """Very low execution → prose format instead of bullets."""
        result = dimensions_to_structural_prompt({"execution": -1.0})
        assert "prose" in result.lower()
        assert "bullet" not in result.lower()

    def test_high_authority_more_sentences(self):
        """High authority → more sentences."""
        import re
        low = dimensions_to_structural_prompt({"authority": -0.8})
        high = dimensions_to_structural_prompt({"authority": 0.8})
        low_sc = int(re.search(r"exactly (\d+) sentences", low).group(1))
        high_sc = int(re.search(r"exactly (\d+) sentences", high).group(1))
        assert high_sc > low_sc

    def test_gain_amplifies(self):
        """Gain factor should amplify dimension values."""
        import re
        normal = dimensions_to_structural_prompt({"empathy": 0.2})
        amplified = dimensions_to_structural_prompt({"empathy": 0.2}, gain=3.0)
        normal_wc = int(re.search(r"approximately (\d+) words", normal).group(1))
        amplified_wc = int(re.search(r"approximately (\d+) words", amplified).group(1))
        assert amplified_wc > normal_wc

    def test_gain_clamps_at_bounds(self):
        """Gain should not produce values outside [30, 250] for word count."""
        import re
        result = dimensions_to_structural_prompt({"empathy": 0.5}, gain=10.0)
        wc = int(re.search(r"approximately (\d+) words", result).group(1))
        assert 30 <= wc <= 250

    def test_missing_dimensions_default_to_zero(self):
        """Missing dimensions should default to 0."""
        result = dimensions_to_structural_prompt({})
        assert "## Response Format" in result

    def test_different_dimensions_different_prompts(self):
        """Different dimension values should produce different prompts."""
        p1 = dimensions_to_structural_prompt({"empathy": -0.5, "execution": 0.3})
        p2 = dimensions_to_structural_prompt({"empathy": 0.5, "execution": -0.3})
        assert p1 != p2


# ──────────────────────────────────────────────
# Proxy Metrics Tests
# ──────────────────────────────────────────────

class TestComputeProxies:
    """Test proxy metric computation."""

    def test_returns_all_metrics(self):
        result = compute_proxies("Hello world this is a test.")
        expected_keys = {"word_count", "hedge_density", "pronoun_ratio",
                         "distinct_2", "bullet_count", "sentence_count"}
        assert set(result.keys()) == expected_keys

    def test_word_count(self):
        result = compute_proxies("one two three four five")
        assert result["word_count"] == 5.0

    def test_hedge_density(self):
        text = "Perhaps we might consider this. Maybe it could work."
        result = compute_proxies(text)
        assert result["hedge_density"] > 0.2  # several hedge words

    def test_no_hedges(self):
        text = "Do this now. Execute the plan. Start immediately."
        result = compute_proxies(text)
        assert result["hedge_density"] == 0.0

    def test_pronoun_ratio_first_person(self):
        text = "I think we should do our best to help my team."
        result = compute_proxies(text)
        assert result["pronoun_ratio"] > 1.0  # more first-person

    def test_pronoun_ratio_second_person(self):
        text = "You should check your work and improve your process."
        result = compute_proxies(text)
        assert result["pronoun_ratio"] < 1.0  # more second-person

    def test_distinct_2_repetitive(self):
        text = "the cat the cat the cat the cat"
        result = compute_proxies(text)
        assert result["distinct_2"] < 0.5  # very repetitive

    def test_distinct_2_diverse(self):
        text = "alpha beta gamma delta epsilon zeta eta theta"
        result = compute_proxies(text)
        assert result["distinct_2"] > 0.8  # very diverse

    def test_bullet_detection(self):
        text = "- Point one\n- Point two\n- Point three"
        result = compute_proxies(text)
        assert result["bullet_count"] == 3.0

    def test_numbered_list_detection(self):
        text = "1. First step\n2. Second step\n3. Third step"
        result = compute_proxies(text)
        assert result["bullet_count"] == 3.0

    def test_sentence_count(self):
        text = "First sentence. Second sentence. Third sentence."
        result = compute_proxies(text)
        assert result["sentence_count"] == 3.0

    def test_empty_text(self):
        result = compute_proxies("")
        assert result["word_count"] == 0.0
        assert result["hedge_density"] == 0.0

    def test_compute_batch(self):
        texts = ["Hello world.", "This is a test.", "One more text."]
        results = compute_batch(texts)
        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)


# ──────────────────────────────────────────────
# Structural Constraints Table Tests
# ──────────────────────────────────────────────

class TestStructuralConstraintsTable:
    """Test the discrete STRUCTURAL_CONSTRAINTS table is well-formed."""

    def test_three_dimensions(self):
        assert set(STRUCTURAL_CONSTRAINTS.keys()) == {"compression", "analysis", "authority"}

    def test_seven_levels_each(self):
        for dim, levels in STRUCTURAL_CONSTRAINTS.items():
            assert set(levels.keys()) == {-3, -2, -1, 0, 1, 2, 3}, f"{dim} missing levels"

    def test_neutral_is_empty(self):
        for dim, levels in STRUCTURAL_CONSTRAINTS.items():
            assert levels[0] == "", f"{dim} level 0 should be empty"

    def test_non_neutral_non_empty(self):
        for dim, levels in STRUCTURAL_CONSTRAINTS.items():
            for level, text in levels.items():
                if level != 0:
                    assert text, f"{dim} level {level} should not be empty"
