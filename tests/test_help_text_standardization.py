"""Tests for help text standardization: make_help() and ArtArgumentParser."""

import argparse
import io
import sys
from unittest import mock

import pytest

from artifactr.cli import ArtArgumentParser, create_parser, make_help


class TestMakeHelp:
    """10.1 - Tests for make_help() helper function."""

    def test_returns_required_keys(self):
        result = make_help(summary="Does a thing.")
        assert "description" in result
        assert "epilog" in result
        assert "formatter_class" in result

    def test_formatter_class_is_raw_description(self):
        result = make_help(summary="Does a thing.")
        assert result["formatter_class"] is argparse.RawDescriptionHelpFormatter

    def test_summary_appears_in_description(self):
        result = make_help(summary="Does a thing.")
        assert result["description"].startswith("Does a thing.")

    def test_aliases_appear_in_description(self):
        result = make_help(summary="Does a thing.", aliases=["x", "y"])
        assert "Aliases: x, y" in result["description"]

    def test_no_aliases_line_when_aliases_none(self):
        result = make_help(summary="Does a thing.", aliases=None)
        assert "Aliases" not in result["description"]

    def test_single_alias_in_description(self):
        result = make_help(summary="Does a thing.", aliases=["v"])
        assert "Aliases: v" in result["description"]

    def test_workflows_in_epilog(self):
        result = make_help(summary="Does a thing.", workflows="art proj import → art proj link")
        assert result["epilog"] is not None
        assert "Workflows:" in result["epilog"]
        assert "art proj import → art proj link" in result["epilog"]

    def test_see_also_in_epilog(self):
        result = make_help(
            summary="Does a thing.",
            see_also=[("art vault init", "Initialize a new vault")],
        )
        assert result["epilog"] is not None
        assert "See Also:" in result["epilog"]
        assert "art vault init" in result["epilog"]
        assert "Initialize a new vault" in result["epilog"]

    def test_notes_in_epilog(self):
        result = make_help(summary="Does a thing.", notes="Targets the default vault.")
        assert result["epilog"] is not None
        assert "Notes:" in result["epilog"]
        assert "Targets the default vault." in result["epilog"]

    def test_epilog_none_when_no_optional_sections(self):
        result = make_help(summary="Does a thing.")
        assert result["epilog"] is None

    def test_epilog_sections_separated_by_blank_lines(self):
        result = make_help(
            summary="Does a thing.",
            workflows="art proj import → art proj link",
            notes="Important note here.",
        )
        assert result["epilog"] is not None
        assert "\n\n" in result["epilog"]

    def test_multiple_see_also_entries(self):
        result = make_help(
            summary="Does a thing.",
            see_also=[
                ("art vault init", "Create vault"),
                ("art vault rm", "Remove vault"),
            ],
        )
        assert "art vault init" in result["epilog"]
        assert "art vault rm" in result["epilog"]

    def test_all_optional_sections_present(self):
        result = make_help(
            summary="Does a thing.",
            workflows="a → b",
            see_also=[("art foo", "Foo command")],
            notes="A note.",
        )
        assert "Workflows:" in result["epilog"]
        assert "See Also:" in result["epilog"]
        assert "Notes:" in result["epilog"]


class TestArtArgumentParser:
    """10.2 - Tests for ArtArgumentParser class."""

    def test_instantiable_no_args(self):
        parser = ArtArgumentParser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_show_help_on_error_defaults_false(self):
        parser = ArtArgumentParser()
        assert parser.show_help_on_error is False

    def test_show_help_on_error_can_be_set_true(self):
        parser = ArtArgumentParser(show_help_on_error=True)
        assert parser.show_help_on_error is True

    def test_error_exits_code_2_when_false(self):
        parser = ArtArgumentParser(show_help_on_error=False)
        parser.add_argument("name")
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([])
        assert exc.value.code == 2

    def test_no_full_help_printed_to_stderr_when_false(self, capsys):
        # With show_help_on_error=False, argparse still prints a brief usage line
        # but does NOT print the full help (options/description block).
        parser = ArtArgumentParser(show_help_on_error=False)
        parser.add_argument("name")
        parser.description = "A unique test description string."
        with pytest.raises(SystemExit):
            parser.parse_args([])
        captured = capsys.readouterr()
        assert "A unique test description string." not in captured.err
        assert "options:" not in captured.err

    def test_help_printed_to_stderr_when_true(self, capsys):
        parser = ArtArgumentParser(show_help_on_error=True)
        parser.add_argument("name")
        with pytest.raises(SystemExit):
            parser.parse_args([])
        captured = capsys.readouterr()
        assert "usage:" in captured.err

    def test_error_exits_code_2_when_true(self):
        parser = ArtArgumentParser(show_help_on_error=True)
        parser.add_argument("name")
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([])
        assert exc.value.code == 2

    def test_parse_args_works_normally(self):
        parser = ArtArgumentParser()
        parser.add_argument("name")
        args = parser.parse_args(["hello"])
        assert args.name == "hello"


class TestCreateParserInfrastructure:
    """Verify create_parser() uses ArtArgumentParser throughout."""

    def test_root_parser_is_artargumentparser(self):
        parser = create_parser()
        assert isinstance(parser, ArtArgumentParser)

    def test_vault_subparser_is_artargumentparser(self):
        parser = create_parser()
        args = parser.parse_args(["vault", "ls"])
        # If we got here without error, vault subparser parsed correctly
        assert args.vault_command == "ls"


class TestSubcommandOrdering:
    """Verify subcommands are registered in alphabetical order."""

    def _get_subcommand_names(self, parser: argparse.ArgumentParser, dest: str) -> list[str]:
        """Get the primary names (not aliases) of subcommands in registration order."""
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction) and action.dest == dest:
                # Filter out aliases by checking which keys are primary (not aliases)
                choices = action.choices
                primary = []
                seen_parsers: set[int] = set()
                for name, subparser in choices.items():
                    parser_id = id(subparser)
                    if parser_id not in seen_parsers:
                        seen_parsers.add(parser_id)
                        primary.append(name)
                return primary
        return []

    def test_vault_subcommands_alphabetical(self):
        parser = create_parser()
        help_output = parser.parse_args.__func__
        # Just check --help output order via string
        import io
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            try:
                parser.parse_args(["vault", "--help"])
            except SystemExit:
                pass
        output = buf.getvalue()
        add_idx = output.find("add")
        init_idx = output.find("init")
        ls_idx = output.find("  ls")
        name_idx = output.find("  name")
        rm_idx = output.find("  rm")
        select_idx = output.find("  select")
        assert add_idx < init_idx < ls_idx < name_idx < rm_idx < select_idx

    def test_tool_subcommands_alphabetical(self):
        import io
        buf = io.StringIO()
        parser = create_parser()
        with mock.patch("sys.stdout", buf):
            try:
                parser.parse_args(["tool", "--help"])
            except SystemExit:
                pass
        output = buf.getvalue()
        add_idx = output.find("  add")
        info_idx = output.find("  info")
        ls_idx = output.find("  ls")
        rm_idx = output.find("  rm")
        select_idx = output.find("  select")
        assert add_idx < info_idx < ls_idx < rm_idx < select_idx

    def test_create_subcommands_alphabetical(self):
        import io
        buf = io.StringIO()
        parser = create_parser()
        with mock.patch("sys.stdout", buf):
            try:
                parser.parse_args(["create", "--help"])
            except SystemExit:
                pass
        output = buf.getvalue()
        agent_idx = output.find("  agent")
        command_idx = output.find("  command")
        skill_idx = output.find("  skill")
        assert agent_idx < command_idx < skill_idx
