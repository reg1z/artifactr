"""Tests for CLI create skill argument parsing and mode detection."""

import argparse

import pytest

from artifactr.cli import create_parser


class TestCreateSkillParsing:
    """Tests for create skill argument parsing."""

    def test_positional_name_required(self):
        """Verify skill name positional argument is required."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["create", "skill"])

    def test_positional_name_parsed(self):
        """Verify skill name is parsed from positional argument."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill"])
        assert args.skill_name == "my-skill"

    def test_description_flag_short(self):
        """Verify -d flag is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "-d", "A skill"])
        assert args.description == "A skill"

    def test_description_flag_long(self):
        """Verify --description flag is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "--description", "A skill"])
        assert args.description == "A skill"

    def test_name_override_flag(self):
        """Verify -n/--name override flag is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "-n", "Display Name"])
        assert args.display_name == "Display Name"

    def test_content_flag(self):
        """Verify -c/--content flag is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "-c", "Instructions"])
        assert args.content == "Instructions"

    def test_field_flag_single(self):
        """Verify -D flag is parsed for a single field."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "-D", "author=Jane"])
        assert args.field == ["author=Jane"]

    def test_field_flag_multiple(self):
        """Verify multiple -D flags are collected."""
        parser = create_parser()
        args = parser.parse_args([
            "create", "skill", "my-skill",
            "-D", "author=Jane",
            "-D", "version=1.0",
        ])
        assert args.field == ["author=Jane", "version=1.0"]

    def test_here_flag(self):
        """Verify -H/--here flag is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "-H"])
        assert args.here is True

    def test_here_flag_long(self):
        """Verify --here long form works."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "--here"])
        assert args.here is True

    def test_vault_flag(self):
        """Verify --vault flag is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "--vault", "favorites"])
        assert args.vaults == ["favorites"]

    def test_tools_flag(self):
        """Verify --tools flag is parsed."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "--tools", "claude-code,opencode"])
        assert args.tools == "claude-code,opencode"

    def test_defaults(self):
        """Verify default values for optional flags."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill"])
        assert args.display_name is None
        assert args.description is None
        assert args.content is None
        assert args.field == []
        assert args.here is False
        assert args.vaults is None
        assert args.tools is None

    def test_create_command_registered(self):
        """Verify create command is in the parser."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill"])
        assert args.command == "create"
        assert args.create_command == "skill"


class TestDescriptionRequired:
    """Tests for description requirement."""

    def test_no_description_is_default_none(self):
        """Verify description defaults to None without flag."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill"])
        assert args.description is None

    def test_description_provided(self):
        """Verify -d flag sets description."""
        parser = create_parser()
        args = parser.parse_args(["create", "skill", "my-skill", "-d", "A skill"])
        assert args.description == "A skill"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
