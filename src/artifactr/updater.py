"""Update logic for the art update command."""

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .utils import detect_shell, get_data_dir, get_shell_rc_file


def detect_install_method() -> str:
    """Detect how artifactr was installed.

    Detection order:
        1. Editable install via PEP 610 direct_url.json
        2. pipx: "pipx/venvs/artifactr" substring in sys.executable path
        3. Managed venv: sys.executable is under get_data_dir() / ".venv"
        4. Unknown: anything else

    Returns:
        One of: "editable", "pipx", "venv", "unknown"
    """
    # 1. Editable install detection via PEP 610
    try:
        dist = importlib.metadata.distribution("artifactr")
        direct_url_text = dist.read_text("direct_url.json")
        if direct_url_text:
            data = json.loads(direct_url_text)
            dir_info = data.get("dir_info", {})
            if dir_info.get("editable", False):
                return "editable"
    except Exception:
        pass

    exe = Path(sys.executable)

    # 2. pipx detection
    if "pipx/venvs/artifactr" in str(exe):
        return "pipx"

    # 3. Managed venv detection
    try:
        data_venv = get_data_dir() / ".venv"
        if exe.is_relative_to(data_venv):
            return "venv"
    except Exception:
        pass

    return "unknown"


def get_current_version() -> str:
    """Return the currently installed version of artifactr.

    Returns:
        Version string (e.g. "0.3.2")
    """
    return importlib.metadata.version("artifactr")


def get_latest_pypi_version() -> str:
    """Query PyPI for the latest published version of artifactr.

    Raises:
        RuntimeError: On any network, timeout, or HTTP error.

    Returns:
        Version string (e.g. "0.3.3")
    """
    url = "https://pypi.org/pypi/artifactr/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"PyPI returned HTTP {response.status}")
            data = json.loads(response.read().decode())
            return data["info"]["version"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"PyPI HTTP error: {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"PyPI request failed: {e.reason}") from e
    except TimeoutError as e:
        raise RuntimeError("PyPI request timed out") from e
    except Exception as e:
        raise RuntimeError(f"Failed to query PyPI: {e}") from e


def run_upgrade(install_method: str) -> subprocess.CompletedProcess:
    """Run the upgrade command for the detected install method.

    Args:
        install_method: One of "pipx", "venv", "unknown"

    Returns:
        CompletedProcess result from subprocess.run
    """
    if install_method == "pipx":
        cmd = ["pipx", "upgrade", "--pip-args=--no-cache-dir", "artifactr"]
    else:
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--upgrade", "--no-cache-dir", "artifactr",
        ]
    return subprocess.run(cmd, capture_output=False)


def get_installed_version_from_pip() -> str | None:
    """Get the installed version of artifactr via pip show.

    Returns:
        Version string if found, None otherwise.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "artifactr"],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    return None


def check_and_repair_path(install_method: str, yes: bool = False) -> None:
    """Check if ~/.local/bin is in PATH and offer to repair if not.

    Skipped entirely on Windows and for pipx installs.

    Args:
        install_method: The detected install method.
        yes: If True, append to rc file without prompting.
    """
    if platform.system() == "Windows":
        return
    if install_method == "pipx":
        return

    local_bin = str(Path.home() / ".local" / "bin")
    path_dirs = os.environ.get("PATH", "").split(":")
    if local_bin in path_dirs:
        return

    # Determine rc file
    rc_file: Path | None = None

    # Try reading from state file first
    state_file = get_data_dir() / ".install-info"
    if state_file.exists():
        try:
            for line in state_file.read_text().splitlines():
                if line.startswith("rc_file="):
                    rc_path = line.split("=", 1)[1].strip()
                    if rc_path:
                        rc_file = Path(rc_path)
                    break
        except Exception:
            pass

    if rc_file is None:
        shell = detect_shell()
        rc_file = get_shell_rc_file(shell)

    if rc_file is None:
        print("Warning: Could not determine shell rc file for PATH repair.")
        return

    # Check if already in rc file
    export_line = 'export PATH="$HOME/.local/bin:$PATH"'
    if rc_file.exists():
        content = rc_file.read_text()
        if "/.local/bin" in content:
            return

    print(f"\nWarning: {local_bin} is not in your PATH.")
    print(f"  The 'art' command may not be found in new shells.")

    if yes:
        do_append = True
    else:
        answer = input(f"  Append '{export_line}' to {rc_file}? [y/N] ").strip()
        do_append = answer.lower() == "y"

    if do_append:
        try:
            with open(rc_file, "a") as f:
                f.write(f"\n# Added by art update\n{export_line}\n")
            print(f"  Appended to {rc_file}. Restart your shell or run: source {rc_file}")
        except Exception as e:
            print(f"  Failed to write to {rc_file}: {e}")
