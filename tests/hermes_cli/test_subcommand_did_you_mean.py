"""Tests for Did-You-Mean subcommand and flag typo suggestions in top-level parser."""

from __future__ import annotations

import pytest

from hermes_cli._parser import build_top_level_parser


def test_subcommand_typo_suggests_close_matches(capsys: pytest.CaptureFixture[str]) -> None:
    parser, subparsers, _chat = build_top_level_parser()
    subparsers.add_parser("status")
    subparsers.add_parser("skills")

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["statsu"])
    assert excinfo.value.code == 2

    captured = capsys.readouterr()
    # Concise error
    assert "unknown command 'statsu'" in captured.err
    assert "Did you mean:" in captured.err
    assert "status" in captured.err
    # Must NOT dump the 70+ choices blob
    assert "choose from" not in captured.err


def test_subcommand_typo_unmatched_clean_error(capsys: pytest.CaptureFixture[str]) -> None:
    parser, _subparsers, _chat = build_top_level_parser()

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["completely_bogus_command_xyz"])
    assert excinfo.value.code == 2

    captured = capsys.readouterr()
    assert "unknown command 'completely_bogus_command_xyz'" in captured.err
    assert "Run 'hermes --help' for available commands." in captured.err
    assert "choose from" not in captured.err


def test_flag_typo_suggests_option(capsys: pytest.CaptureFixture[str]) -> None:
    parser, _subparsers, _chat = build_top_level_parser()

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--yoloo"])
    assert excinfo.value.code == 2

    captured = capsys.readouterr()
    assert "unrecognized arguments: --yoloo" in captured.err
    assert "did you mean: --yoloo -> --yolo" in captured.err
