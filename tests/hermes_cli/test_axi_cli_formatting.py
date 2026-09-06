"""Tests for AXI Phase 2 CLI formatting, TOON serialization, and content-first defaults."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hermes_cli.subcommands._shared import (
    VALID_OUTPUT_FORMATS,
    add_format_flag,
    emit_formatted_output,
    resolve_output_format,
    to_toon,
)
from tools.tool_output_limits import (
    DEFAULT_OUTPUT_FORMAT,
    _reset_tool_output_limits_cache,
    get_output_format,
    get_tool_output_limits,
)


def test_to_toon_primitives() -> None:
    assert to_toon(None) == "null"
    assert to_toon(True) == "true"
    assert to_toon(False) == "false"
    assert to_toon(42) == "42"
    assert to_toon(3.14) == "3.14"
    assert to_toon("simple") == "simple"
    assert to_toon("with,comma") == '"with,comma"'
    assert to_toon("with:colon") == '"with:colon"'
    assert to_toon("with\nnewline") == '"with\\nnewline"'
    assert to_toon("true") == '"true"'
    assert to_toon("null") == '"null"'


def test_to_toon_empty_containers() -> None:
    assert to_toon([]) == "[0]:"
    assert to_toon({}) == "{}"


def test_to_toon_uniform_list_of_dicts() -> None:
    items = [
        {"name": "web-search", "category": "research", "status": "enabled"},
        {"name": "code-exec", "category": "tools", "status": "disabled"},
    ]
    expected = (
        "[2]{name,category,status}:\n"
        "web-search,research,enabled\n"
        "code-exec,tools,disabled"
    )
    assert to_toon(items) == expected


def test_to_toon_list_of_scalars() -> None:
    items = ["apple", "banana", "cherry"]
    expected = (
        "[3]:\n"
        "- apple\n"
        "- banana\n"
        "- cherry"
    )
    assert to_toon(items) == expected


def test_to_toon_nested_dict() -> None:
    data = {
        "count": 2,
        "items": [
            {"id": 1, "label": "first"},
            {"id": 2, "label": "second"},
        ],
    }
    expected = (
        "count: 2\n"
        "items[2]{id,label}:\n"
        "  1,first\n"
        "  2,second"
    )
    assert to_toon(data) == expected


def test_add_format_flag() -> None:
    parser = argparse.ArgumentParser()
    add_format_flag(parser)
    args = parser.parse_args(["--format", "toon"])
    assert args.format == "toon"

    with pytest.raises(SystemExit):
        parser.parse_args(["--format", "invalid_format"])


def test_resolve_output_format_precedence() -> None:
    # 1. Explicit override wins
    assert resolve_output_format(args=argparse.Namespace(format="text", json=True), explicit_format="toon") == "toon"

    # 2. args.format wins over args.json
    assert resolve_output_format(args=argparse.Namespace(format="toon", json=True)) == "toon"

    # 3. args.json gives "json"
    assert resolve_output_format(args=argparse.Namespace(format=None, json=True)) == "json"

    # 4. Fallback to default
    assert resolve_output_format(args=argparse.Namespace(format=None, json=False)) in VALID_OUTPUT_FORMATS


def test_tool_output_format_config(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_tool_output_limits_cache()
    limits = get_tool_output_limits()
    assert limits["format"] == DEFAULT_OUTPUT_FORMAT
    assert get_output_format() == DEFAULT_OUTPUT_FORMAT

    # Mock config with format: "toon"
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"tool_output": {"format": "toon"}},
    )
    _reset_tool_output_limits_cache()
    try:
        assert get_output_format() == "toon"
    finally:
        _reset_tool_output_limits_cache()


def test_emit_formatted_output(capsys: pytest.CaptureFixture[str]) -> None:
    data = [{"a": 1, "b": "ok"}]

    emit_formatted_output(data, format="json")
    captured = capsys.readouterr()
    assert json.loads(captured.out) == data

    emit_formatted_output(data, format="toon")
    captured = capsys.readouterr()
    assert "[1]{a,b}:" in captured.out
    assert "1,ok" in captured.out

    called = []
    emit_formatted_output(data, format="text", default_text_fn=lambda: called.append(True))
    assert called == [True]


def test_skills_command_defaults_to_list() -> None:
    from hermes_cli.skills_hub import skills_command

    args = argparse.Namespace(skills_action=None, source="all", enabled_only=False, format="toon")
    with patch("hermes_cli.skills_hub.do_list") as mock_do_list:
        skills_command(args)
        assert mock_do_list.called
        assert args.skills_action == "list"


def test_sessions_command_defaults_to_list(capsys: pytest.CaptureFixture[str]) -> None:
    from hermes_cli.sessions_cmd import cmd_sessions

    args = argparse.Namespace(sessions_action=None, source=None, limit=10, workspace=None, format="toon")
    with patch("hermes_state.SessionDB") as mock_db_cls:
        mock_db = MagicMock()
        mock_db.list_sessions_rich.return_value = [
            {"id": "sess_1", "title": "Test Session", "preview": "hello", "source": "cli"}
        ]
        mock_db_cls.return_value = mock_db
        cmd_sessions(args)
        out, _err = capsys.readouterr()
        assert "[1]{id,title,preview,workspace,last_active,source}:" in out
        assert "sess_1,Test Session,hello" in out


def test_plugins_toggle_non_interactive_defaults_to_list(monkeypatch: pytest.MonkeyPatch) -> None:
    from hermes_cli.plugins_cmd import cmd_toggle

    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    with patch("hermes_cli.plugins_cmd.cmd_list") as mock_cmd_list:
        cmd_toggle()
        assert mock_cmd_list.called
