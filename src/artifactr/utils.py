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
        4. notepad.exe (Windows fallback)

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

    if platform.system() == "Windows" and shutil.which("notepad.exe"):
        return "notepad.exe"

    return None


def detect_shell() -> str:
    """Detect the user's current shell.

    Resolution order:
        1. $SHELL environment variable (Unix)
        2. PowerShell detection via $PSVersionTable presence
        3. Falls back to 'sh'

    Returns:
        Shell name: 'bash', 'zsh', 'fish', 'sh', or 'powershell'
    """
    shell_path = os.environ.get("SHELL", "")
    if shell_path:
        name = os.path.basename(shell_path)
        if name in ("bash", "zsh", "fish", "sh", "dash", "ksh"):
            return name
        return name  # Return whatever it is

    # PowerShell detection on Windows
    if os.environ.get("PSVersionTable") or os.environ.get("PSModulePath"):
        return "powershell"

    return "sh"


def get_shell_rc_file(shell: str) -> Path | None:
    """Return the rc file path for the given shell.

    Args:
        shell: Shell name (bash, zsh, fish, sh, powershell, etc.)

    Returns:
        Path to the rc file, or None if unknown/unhandled.
    """
    home = Path.home()
    if shell == "bash":
        return home / ".bashrc"
    elif shell == "zsh":
        return home / ".zshrc"
    elif shell == "fish":
        return home / ".config" / "fish" / "functions" / "art.fish"
    elif shell in ("sh", "dash"):
        return home / ".profile"
    elif shell == "powershell":
        profile = os.environ.get("PROFILE")
        if profile:
            return Path(profile)
        return home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    return None


def get_shell_wrapper_snippet(shell: str) -> str:
    """Return the shell wrapper snippet for the given shell.

    The wrapper intercepts 'art nav' calls and cd's to the printed path.

    Args:
        shell: Shell name.

    Returns:
        Shell function snippet string.
    """
    if shell in ("bash", "sh", "dash"):
        return (
            "# Artifactr shell integration\n"
            "art() {\n"
            "  if [ \"$1\" = \"nav\" ]; then\n"
            "    local _art_path\n"
            "    _art_path=$(command art nav --print \"${@:2}\" 2>/dev/null)\n"
            "    if [ -n \"$_art_path\" ]; then\n"
            "      cd \"$_art_path\" || return 1\n"
            "    else\n"
            "      command art nav \"${@:2}\"\n"
            "    fi\n"
            "  else\n"
            "    command art \"$@\"\n"
            "  fi\n"
            "}\n"
        )
    elif shell == "zsh":
        return (
            "# Artifactr shell integration\n"
            "art() {\n"
            "  if [[ \"$1\" == \"nav\" ]]; then\n"
            "    local _art_path\n"
            "    _art_path=$(command art nav --print \"${@:2}\" 2>/dev/null)\n"
            "    if [[ -n \"$_art_path\" ]]; then\n"
            "      cd \"$_art_path\" || return 1\n"
            "    else\n"
            "      command art nav \"${@:2}\"\n"
            "    fi\n"
            "  else\n"
            "    command art \"$@\"\n"
            "  fi\n"
            "}\n"
        )
    elif shell == "fish":
        return (
            "# Artifactr shell integration\n"
            "function art\n"
            "  if test \"$argv[1]\" = \"nav\"\n"
            "    set _art_path (command art nav --print $argv[2..] 2>/dev/null)\n"
            "    if test -n \"$_art_path\"\n"
            "      cd $_art_path\n"
            "    else\n"
            "      command art nav $argv[2..]\n"
            "    end\n"
            "  else\n"
            "    command art $argv\n"
            "  end\n"
            "end\n"
        )
    elif shell == "powershell":
        return (
            "# Artifactr shell integration\n"
            "function art {\n"
            "  if ($args[0] -eq 'nav') {\n"
            "    $path = & (Get-Command art -CommandType Application | Select-Object -First 1).Source nav --print @($args[1..($args.Length-1)]) 2>$null\n"
            "    if ($path) { Set-Location $path } else { & art nav @($args[1..($args.Length-1)]) }\n"
            "  } else {\n"
            "    & (Get-Command art -CommandType Application | Select-Object -First 1).Source @args\n"
            "  }\n"
            "}\n"
        )
    else:
        # Generic fallback (bash-style)
        return get_shell_wrapper_snippet("bash")


def is_git_repo(path: Path) -> bool:
    """Check if a directory is a git repository.

    Args:
        path: Directory path to check

    Returns:
        True if the path contains a .git directory, False otherwise
    """
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()
