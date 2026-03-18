"""ClawClaw Soul MCP Server.

Exposes identity tools via FastMCP (stdio transport).
Based on Jyotish MCP architecture (~/.../jyotish/app/mcp_server.py).

Usage:
    python -m clawclaw_soul.mcp_server

Add to Claude Desktop config (~/.claude/mcp.json):
    {
        "mcpServers": {
            "clawclaw-soul": {
                "command": "python",
                "args": ["-m", "clawclaw_soul.mcp_server"]
            }
        }
    }
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from clawclaw_soul.soul import generate, generate_soul_md, verify_soul_md

mcp = FastMCP(
    "ClawClaw Soul",
    instructions="Persistent identity protocol for AI agents. "
    "Generate deterministic personality from celestial mechanics.",
)


@mcp.tool()
def generate_soul(
    timestamp: str,
    latitude: float = 0.0,
    longitude: float = 0.0,
    agent_name: str = "Agent",
) -> str:
    """Generate a Soul Card from a birth timestamp.

    Returns JSON with agent_config (temperature, max_tokens, top_p),
    persona (assertiveness, empathy, creativity, etc.),
    system_prompt_modifier, and identity_seed.

    Args:
        timestamp: ISO 8601 birth datetime (e.g. "2024-03-15T09:30:00Z").
        latitude: Birth latitude (-90 to 90). Default 0.0.
        longitude: Birth longitude (-180 to 180). Default 0.0.
        agent_name: Name for the agent identity.
    """
    soul = generate(timestamp, latitude=latitude, longitude=longitude)
    card = soul.card
    card["agent_name"] = agent_name
    return json.dumps(card, indent=2, default=str)


@mcp.tool()
def init_soul_md(
    timestamp: str | None = None,
    latitude: float = 0.0,
    longitude: float = 0.0,
    agent_name: str = "Agent",
    output_path: str = "SOUL.md",
) -> str:
    """Generate a SOUL.md identity file for an AI agent.

    Creates a persistent, deterministically verifiable identity file.
    Same birth parameters = same identity. Always.

    Args:
        timestamp: ISO 8601 birth datetime. Random if omitted.
        latitude: Birth latitude. Default 0.0.
        longitude: Birth longitude. Default 0.0.
        agent_name: Name for the agent.
        output_path: Where to write the file. Default "SOUL.md".
    """
    soul = generate(timestamp, latitude=latitude, longitude=longitude)
    content = generate_soul_md(soul, agent_name=agent_name)

    path = Path(output_path)
    path.write_text(content)

    return json.dumps({
        "status": "created",
        "path": str(path.resolve()),
        "lagna": soul.card["lagna"],
        "temperature": soul.card["agent_config"]["temperature"],
        "identity_seed": soul.card["identity_seed"],
    })


@mcp.tool()
def verify_identity(file_path: str = "SOUL.md") -> str:
    """Verify a SOUL.md file by re-computing from its birth parameters.

    Deterministic verification: re-runs the celestial mechanics math
    and checks if the result matches. No server needed.

    Args:
        file_path: Path to SOUL.md file. Default "SOUL.md".
    """
    path = Path(file_path)
    if not path.exists():
        return json.dumps({"valid": False, "message": f"File not found: {file_path}"})

    content = path.read_text()
    result = verify_soul_md(content)
    return json.dumps(result)


@mcp.tool()
def get_daily_drift(
    timestamp: str,
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> str:
    """Get today's transit-adjusted dimensions for an agent.

    Computes how planetary transits shift the agent's personality today.
    Use the original birth timestamp from the agent's SOUL.md.

    Args:
        timestamp: Original birth timestamp from SOUL.md (ISO 8601).
        latitude: Birth latitude.
        longitude: Birth longitude.
    """
    from clawclaw_soul.engine import compute_modifiers_v2

    soul = generate(timestamp, latitude=latitude, longitude=longitude)
    drift = compute_modifiers_v2(soul)
    return json.dumps(drift, indent=2, default=str)


if __name__ == "__main__":
    mcp.run(transport="stdio")
