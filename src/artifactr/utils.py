"""Cross-platform utility functions for Artifactr."""

import os
import platform
import shutil
from pathlib import Path


def get_config_dir() -> Path:
    """Return the platform-appropriate configuration directory for Artifactr.

    Returns:
        Path: Configuration directory path
            - Linux: ~/.config/artifactr/ (or $XDG_CONFIG_HOME/artifactr/)
            - macOS: ~/Library/Application Support/artifactr/
            - Windows: %APPDATA%/artifactr/
    """
    system = platform.system()

    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "artifactr"
        return Path.home() / "AppData" / "Roaming" / "artifactr"

    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "artifactr"

    else:  # Linux and others
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "artifactr"
        return Path.home() / ".config" / "artifactr"


def get_editor() -> str | None:
    """Return the user's preferred editor.

    Resolution order:
        1. $VISUAL environment variable
        2. $EDITOR environment variable
        3. First found from: nano, nvim, vim, vi

    Returns:
        The editor command string, or None if no editor is found.
    """
    for var in ("VISUAL", "EDITOR"):
        value = os.environ.get(var)
        if value:
            return value

    for editor in ("nano", "nvim", "vim", "vi"):
        if shutil.which(editor):
            return editor

    return None


def is_git_repo(path: Path) -> bool:
    """Check if a directory is a git repository.

    Args:
        path: Directory path to check

    Returns:
        True if the path contains a .git directory, False otherwise
    """
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()
