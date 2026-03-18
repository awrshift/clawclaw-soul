"""Integration test: README quickstart must work verbatim."""

import json


def test_generate_with_timestamp():
    from clawclaw_soul import generate

    soul = generate("2024-03-15T09:30:00Z")
    card = soul.card

    assert isinstance(card, dict)
    assert "agent_config" in card
    assert "persona" in card
    assert "system_prompt_modifier" in card
    assert "identity_seed" in card
    assert "soul_card" in card

    cfg = card["agent_config"]
    assert "temperature" in cfg
    assert "max_tokens" in cfg
    assert 0.3 <= cfg["temperature"] <= 1.3


def test_determinism():
    from clawclaw_soul import generate

    a = generate("2024-03-15T09:30:00Z").card
    b = generate("2024-03-15T09:30:00Z").card
    assert a == b


def test_generate_random():
    from clawclaw_soul import generate

    soul = generate()
    assert soul.card is not None
    assert "agent_config" in soul.card


def test_generate_with_coords():
    from clawclaw_soul import generate

    soul_default = generate("2024-03-15T09:30:00Z")
    soul_london = generate("2024-03-15T09:30:00Z", latitude=51.5074, longitude=-0.1278)
    assert soul_default.card["agent_config"]["temperature"] != soul_london.card["agent_config"]["temperature"]


def test_card_json_serializable():
    from clawclaw_soul import generate

    soul = generate("2024-03-15T09:30:00Z")
    serialized = json.dumps(soul.card)
    assert len(serialized) > 100
