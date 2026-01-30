"""Tests for utils module (Task 2.1)."""

import os
import platform
from pathlib import Path
from unittest import mock

import pytest

from artifactr.utils import get_config_dir, is_git_repo


class TestGetConfigDir:
    """Tests for get_config_dir function."""

    def test_returns_path_object(self):
        """Verify function returns a Path instance."""
        result = get_config_dir()
        assert isinstance(result, Path)

    def test_path_ends_with_artifactr(self):
        """Verify path always ends with 'artifactr' directory."""
        result = get_config_dir()
        assert result.name == "artifactr"

    @mock.patch("artifactr.utils.platform.system")
    def test_linux_default_path(self, mock_system):
        """Verify Linux uses ~/.config/artifactr by default."""
        mock_system.return_value = "Linux"
        with mock.patch.dict(os.environ, {}, clear=True):
            # Remove XDG_CONFIG_HOME if set
            os.environ.pop("XDG_CONFIG_HOME", None)
            result = get_config_dir()
            expected = Path.home() / ".config" / "artifactr"
            assert result == expected

    @mock.patch("artifactr.utils.platform.system")
    def test_linux_respects_xdg_config_home(self, mock_system):
        """Verify Linux respects XDG_CONFIG_HOME environment variable."""
        mock_system.return_value = "Linux"
        custom_config = "/custom/config/path"
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": custom_config}):
            result = get_config_dir()
            expected = Path(custom_config) / "artifactr"
            assert result == expected

    @mock.patch("artifactr.utils.platform.system")
    def test_macos_path(self, mock_system):
        """Verify macOS uses ~/Library/Application Support/artifactr."""
        mock_system.return_value = "Darwin"
        result = get_config_dir()
        expected = Path.home() / "Library" / "Application Support" / "artifactr"
        assert result == expected

    @mock.patch("artifactr.utils.platform.system")
    def test_windows_with_appdata(self, mock_system):
        """Verify Windows uses %APPDATA%/artifactr when APPDATA is set."""
        mock_system.return_value = "Windows"
        appdata_path = "/Users/TestUser/AppData/Roaming"
        with mock.patch.dict(os.environ, {"APPDATA": appdata_path}):
            result = get_config_dir()
            expected = Path(appdata_path) / "artifactr"
            assert result == expected

    @mock.patch("artifactr.utils.platform.system")
    def test_windows_fallback_without_appdata(self, mock_system):
        """Verify Windows falls back to home/AppData/Roaming when APPDATA unset."""
        mock_system.return_value = "Windows"
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("APPDATA", None)
            result = get_config_dir()
            expected = Path.home() / "AppData" / "Roaming" / "artifactr"
            assert result == expected

    @mock.patch("artifactr.utils.platform.system")
    def test_unknown_platform_uses_linux_default(self, mock_system):
        """Verify unknown platforms fall back to Linux-style path."""
        mock_system.return_value = "FreeBSD"
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("XDG_CONFIG_HOME", None)
            result = get_config_dir()
            expected = Path.home() / ".config" / "artifactr"
            assert result == expected


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_detects_git_directory(self, tmp_path):
        """Verify function returns True when .git directory exists."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        assert is_git_repo(tmp_path) is True

    def test_returns_false_for_non_git_directory(self, tmp_path):
        """Verify function returns False when no .git directory."""
        assert is_git_repo(tmp_path) is False

    def test_returns_false_when_git_is_file(self, tmp_path):
        """Verify function returns False when .git is a file, not directory."""
        git_file = tmp_path / ".git"
        git_file.write_text("gitdir: /some/path")  # Git worktree format
        assert is_git_repo(tmp_path) is False

    def test_returns_false_for_nonexistent_path(self, tmp_path):
        """Verify function returns False for paths that don't exist."""
        nonexistent = tmp_path / "does_not_exist"
        assert is_git_repo(nonexistent) is False

    def test_nested_git_directory(self, tmp_path):
        """Verify function only checks immediate .git directory."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        nested_git = subdir / ".git"
        nested_git.mkdir()

        # Parent should not be detected as git repo
        assert is_git_repo(tmp_path) is False
        # Subdir should be detected
        assert is_git_repo(subdir) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
