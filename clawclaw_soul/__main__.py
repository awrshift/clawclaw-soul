"""ClawClaw Soul CLI.

Usage:
    clawclaw-soul init [--name NAME] [--timestamp TS] [--output FILE]
    clawclaw-soul verify [FILE]
    python -m clawclaw_soul init
    python -m clawclaw_soul verify SOUL.md
"""

import argparse
import sys
from pathlib import Path


def cmd_init(args):
    """Generate a SOUL.md file."""
    from clawclaw_soul.soul import generate, generate_soul_md

    if args.timestamp:
        soul = generate(args.timestamp)
    else:
        soul = generate()

    content = generate_soul_md(soul, agent_name=args.name)
    output = Path(args.output)
    output.write_text(content)
    print(f"SOUL.md generated: {output}")
    print(f"  Lagna: {soul.card['lagna']}")
    print(f"  Temperature: {soul.card['agent_config']['temperature']}")
    print(f"  Seed: {soul.card['identity_seed']}")


def cmd_verify(args):
    """Verify a SOUL.md file."""
    from clawclaw_soul.soul import verify_soul_md

    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text()
    result = verify_soul_md(content)

    if result["valid"]:
        print(f"[OK] {result['message']}")
        print(f"  Birth: {result['details']['birth']}")
        print(f"  Temperature: {result['details']['temperature']}")
    else:
        print(f"[FAIL] {result['message']}", file=sys.stderr)
        sys.exit(1)


def cmd_badge(args):
    """Generate a Soul.md badge for README."""
    from clawclaw_soul.soul import generate, generate_badge, verify_soul_md

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(1)
        content = path.read_text()
        result = verify_soul_md(content)
        if not result["valid"]:
            print(f"[FAIL] Cannot generate badge: {result['message']}", file=sys.stderr)
            sys.exit(1)
        soul = generate(
            result["details"]["birth"],
            latitude=result["details"].get("latitude", 0),
            longitude=result["details"].get("longitude", 0),
        )
        name = args.name or "Agent"
    elif args.timestamp:
        soul = generate(args.timestamp)
        name = args.name or "Agent"
    else:
        print("Provide --timestamp or a SOUL.md file", file=sys.stderr)
        sys.exit(1)

    badge = generate_badge(soul, agent_name=name, style=args.style)

    if args.format == "markdown":
        print(badge["markdown"])
    elif args.format == "html":
        print(badge["html"])
    elif args.format == "snippet":
        print(badge["snippet"])
    elif args.format == "url":
        print(badge["svg_url"])
    else:
        print(f"Badge for {name} ({badge['lagna']} · {badge['archetype']})")
        print()
        print("Markdown:")
        print(f"  {badge['markdown']}")
        print()
        print("Full snippet (copy to README):")
        print(f"  {badge['snippet']}")


def main():
    parser = argparse.ArgumentParser(
        prog="clawclaw-soul",
        description="ClawClaw Soul — persistent identity for AI agents",
    )
    sub = parser.add_subparsers(dest="command")

    # init
    init_p = sub.add_parser("init", help="Generate a SOUL.md file")
    init_p.add_argument("--name", default="Agent", help="Agent name (default: Agent)")
    init_p.add_argument("--timestamp", "-t", help="Birth timestamp (ISO 8601). Random if omitted.")
    init_p.add_argument("--output", "-o", default="SOUL.md", help="Output file (default: SOUL.md)")

    # verify
    verify_p = sub.add_parser("verify", help="Verify a SOUL.md file")
    verify_p.add_argument("file", nargs="?", default="SOUL.md", help="SOUL.md file to verify (default: SOUL.md)")

    # badge
    badge_p = sub.add_parser("badge", help="Generate a Soul.md badge for README")
    badge_p.add_argument("file", nargs="?", help="SOUL.md file to generate badge from")
    badge_p.add_argument("--timestamp", "-t", help="Birth timestamp (ISO 8601)")
    badge_p.add_argument("--name", help="Agent name")
    badge_p.add_argument(
        "--style", default="flat",
        choices=["flat", "flat-square", "plastic", "for-the-badge"],
        help="Badge style (default: flat)",
    )
    badge_p.add_argument(
        "--format", "-f", default="all",
        choices=["all", "markdown", "html", "snippet", "url"],
        help="Output format (default: all)",
    )

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "badge":
        cmd_badge(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
