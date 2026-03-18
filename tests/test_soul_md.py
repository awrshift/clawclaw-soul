"""Tests for SOUL.md generation and verification."""

from clawclaw_soul import generate, generate_soul_md, verify_soul_md


def test_generate_soul_md_contains_identity():
    soul = generate("2024-03-15T09:30:00Z")
    md = generate_soul_md(soul, agent_name="TestBot")
    assert "# SOUL.md" in md
    assert "**Name:** TestBot" in md
    assert "**Birth:** 2024-03-15" in md
    assert "**Lagna:** Aries" in md
    assert "**Temperature:**" in md


def test_generate_soul_md_contains_dimensions():
    soul = generate("2024-03-15T09:30:00Z")
    md = generate_soul_md(soul)
    assert "authority" in md
    assert "empathy" in md
    assert "execution" in md
    assert "| Dimension | Value |" in md


def test_generate_soul_md_contains_system_prompt():
    soul = generate("2024-03-15T09:30:00Z")
    md = generate_soul_md(soul)
    assert "## System Prompt" in md
    assert "```" in md


def test_verify_soul_md_valid():
    soul = generate("2024-03-15T09:30:00Z")
    md = generate_soul_md(soul)
    result = verify_soul_md(md)
    assert result["valid"] is True
    assert "verified" in result["message"].lower()


def test_verify_soul_md_tampered():
    soul = generate("2024-03-15T09:30:00Z")
    md = generate_soul_md(soul)
    tampered = md.replace("**Temperature:** 0.68", "**Temperature:** 0.99")
    result = verify_soul_md(tampered)
    assert result["valid"] is False
    assert "Mismatch" in result["message"]


def test_verify_soul_md_missing_fields():
    result = verify_soul_md("# Just a random file\n\nNo soul data here.")
    assert result["valid"] is False
    assert "Missing" in result["message"]


def test_soul_md_deterministic():
    soul1 = generate("2024-03-15T09:30:00Z")
    soul2 = generate("2024-03-15T09:30:00Z")
    md1 = generate_soul_md(soul1, agent_name="Bot")
    md2 = generate_soul_md(soul2, agent_name="Bot")
    assert md1 == md2
