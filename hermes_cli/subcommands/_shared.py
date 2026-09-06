"""Shared argparse helpers for the ``hermes_cli/subcommands/*`` builders.

Import-cycle-free (no ``main`` import); ``main.py`` re-exports for compatibility.
"""

from __future__ import annotations

import argparse


def add_accept_hooks_flag(parser: argparse.ArgumentParser) -> None:
    """Attach ``--accept-hooks`` (shared by every agent subparser so it works in any position)."""
    parser.add_argument(
        "--accept-hooks", action="store_true", default=argparse.SUPPRESS,
        help="Auto-approve unseen shell hooks without a TTY prompt "
            "(equivalent to HERMES_ACCEPT_HOOKS=1 / hooks_auto_accept: true).")


def add_yes_flag(parser: argparse.ArgumentParser, help: str = "Skip confirmation prompt") -> None:
    """Attach ``--yes/-y`` (store_true) with the given help text."""
    parser.add_argument("--yes", "-y", action="store_true", help=help)


def add_json_flag(parser: argparse.ArgumentParser, help: str) -> None:
    """Attach ``--json`` (store_true) with the given help text."""
    parser.add_argument("--json", action="store_true", help=help)


VALID_OUTPUT_FORMATS: tuple[str, ...] = ("text", "json", "toon")


def add_format_flag(
    parser: argparse.ArgumentParser,
    default: str | None = None,
    choices: tuple[str, ...] = VALID_OUTPUT_FORMATS,
    help: str = "Output format (text, json, toon)",
) -> None:
    """Attach ``--format`` (choices: text, json, toon) with the given help text."""
    parser.add_argument(
        "--format",
        choices=choices,
        default=default,
        help=help,
    )


def resolve_output_format(args: Any = None, explicit_format: str | None = None) -> str:
    """Resolve active output format (explicit > args.format > args.json > config.yaml > 'text')."""
    if explicit_format:
        fmt = str(explicit_format).lower().strip()
        if fmt in VALID_OUTPUT_FORMATS:
            return fmt
    if args is not None:
        raw_fmt = getattr(args, "format", None)
        if raw_fmt:
            fmt = str(raw_fmt).lower().strip()
            if fmt in VALID_OUTPUT_FORMATS:
                return fmt
        if getattr(args, "json", False):
            return "json"
    try:
        from tools.tool_output_limits import get_output_format
        return get_output_format()
    except Exception:
        return "text"


def _format_toon_primitive(val: Any) -> str:
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val)
    if not s:
        return '""'
    if any(c in s for c in (",", ":", "\n", '"', "{", "}", "[", "]")) or s.strip() != s:
        import json
        return json.dumps(s)
    if s.lower() in ("true", "false", "null"):
        import json
        return json.dumps(s)
    return s


def to_toon(data: Any, indent: int = 0) -> str:
    """Serialize data into Token-Optimized Object Notation (TOON)."""
    prefix = " " * indent
    if data is None or isinstance(data, (bool, int, float, str)):
        return prefix + _format_toon_primitive(data)
    if isinstance(data, list):
        if not data:
            return prefix + "[0]:"
        if all(isinstance(x, dict) for x in data):
            cols: list[str] = []
            for d in data:
                for k in d.keys():
                    if k not in cols:
                        cols.append(k)
            lines = [f"{prefix}[{len(data)}]{{{','.join(cols)}}}:"]
            for d in data:
                row = ",".join(_format_toon_primitive(d.get(c)) for c in cols)
                lines.append(f"{prefix}{row}")
            return "\n".join(lines)
        lines = [f"{prefix}[{len(data)}]:"]
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(to_toon(item, indent=indent + 2))
            else:
                lines.append(f"{prefix}- {_format_toon_primitive(item)}")
        return "\n".join(lines)
    if isinstance(data, dict):
        if not data:
            return prefix + "{}"
        lines = []
        for k, v in data.items():
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                cols = []
                for d in v:
                    for col in d.keys():
                        if col not in cols:
                            cols.append(col)
                lines.append(f"{prefix}{k}[{len(v)}]{{{','.join(cols)}}}:")
                for d in v:
                    row = ",".join(_format_toon_primitive(d.get(c)) for c in cols)
                    lines.append(f"{prefix}  {row}")
            elif isinstance(v, list):
                if not v:
                    lines.append(f"{prefix}{k}[0]:")
                else:
                    lines.append(f"{prefix}{k}[{len(v)}]:")
                    for item in v:
                        if isinstance(item, (dict, list)):
                            lines.append(to_toon(item, indent=indent + 2))
                        else:
                            lines.append(f"{prefix}  - {_format_toon_primitive(item)}")
            elif isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                lines.append(to_toon(v, indent=indent + 2))
            else:
                lines.append(f"{prefix}{k}: {_format_toon_primitive(v)}")
        return "\n".join(lines)
    return prefix + str(data)


def emit_formatted_output(
    data: Any,
    format: str,
    default_text_fn: Any | None = None,
) -> None:
    """Emit formatted output for CLI subcommands based on format (text, json, toon)."""
    import json
    if format == "json":
        print(json.dumps(data, indent=2))
    elif format == "toon":
        print(to_toon(data))
    elif default_text_fn is not None:
        default_text_fn()
    else:
        print(data)
