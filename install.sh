#!/usr/bin/env bash
set -euo pipefail

# ── Globals ────────────────────────────────────────────────────────────────────
AUTO_YES=0
UNINSTALL=0
INSTALL_METHOD=""
RC_FILE=""
DATA_DIR=""
SHELL_RC=""

# ── Argument parsing ───────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
  --yes | -y)
    AUTO_YES=1
    ;;
  --uninstall)
    UNINSTALL=1
    ;;
  *)
    echo "Unknown flag: $arg"
    echo "Usage: install.sh [--yes|-y] [--uninstall]"
    exit 1
    ;;
  esac
done

# ── Helpers ────────────────────────────────────────────────────────────────────
confirm() {
  local message="$1"
  if [[ "$AUTO_YES" -eq 1 ]]; then
    echo "$message [y/N] y (auto)"
    return 0
  fi
  printf "%s [y/N] " "$message"
  read -r response || true
  case "$response" in
  [yY])
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

read_state_file() {
  local state_file="$DATA_DIR/.install-info"
  if [[ ! -f "$state_file" ]]; then
    return 0
  fi
  while IFS='=' read -r key value; do
    case "$key" in
    method) INSTALL_METHOD="$value" ;;
    rc_file) RC_FILE="$value" ;;
    esac
  done <"$state_file"
}

write_state_file() {
  mkdir -p "$DATA_DIR"
  local state_file="$DATA_DIR/.install-info"
  printf "method=%s\n" "$INSTALL_METHOD" >"$state_file"
  if [[ -n "$RC_FILE" ]]; then
    printf "rc_file=%s\n" "$RC_FILE" >>"$state_file"
  fi
}

# ── Platform detection ─────────────────────────────────────────────────────────
OS="$(uname -s 2>/dev/null || echo "Unknown")"
case "$OS" in
MINGW* | CYGWIN* | MSYS*)
  echo "Windows detected. A PowerShell installer (install.ps1) is planned."
  echo "See the README for manual install instructions."
  exit 1
  ;;
Linux)
  DATA_DIR="$HOME/.local/share/artifactr"
  ;;
Darwin)
  DATA_DIR="$HOME/Library/Application Support/artifactr"
  ;;
*)
  echo "Unsupported OS: $OS"
  exit 1
  ;;
esac

# ── Shell rc file detection ────────────────────────────────────────────────────
shell_name="$(basename "${SHELL:-}")"
case "$shell_name" in
bash) SHELL_RC="$HOME/.bashrc" ;;
zsh) SHELL_RC="$HOME/.zshrc" ;;
fish) SHELL_RC="$HOME/.config/fish/config.fish" ;;
sh | dash) SHELL_RC="$HOME/.profile" ;;
*) SHELL_RC="$HOME/.profile" ;;
esac

# ── Python version check ───────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "python3 not found. Install Python 3.10+ from https://www.python.org/downloads/"
  exit 1
fi

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
  PYTHON_VERSION="$(python3 -c "import sys; print('.'.join(str(x) for x in sys.version_info[:3]))")"
  echo "Found Python $PYTHON_VERSION. Python 3.10+ required."
  exit 1
fi

# ── Uninstall flow ─────────────────────────────────────────────────────────────
if [[ "$UNINSTALL" -eq 1 ]]; then

  # 7.1 Detect if installed
  if ! command -v art &>/dev/null && [[ ! -f "$DATA_DIR/.install-info" ]]; then
    echo "artifactr does not appear to be installed."
    exit 0
  fi

  # Read state file
  read_state_file

  # 7.2 Show uninstall summary and confirm
  echo ""
  echo "Uninstall artifactr"
  echo "  Method: ${INSTALL_METHOD:-unknown}"
  echo "  Data directory: $DATA_DIR"
  if [[ -n "$RC_FILE" ]]; then
    echo "  RC file: $RC_FILE"
  fi
  echo ""
  if ! confirm "Proceed with uninstall?"; then
    echo "Uninstall cancelled."
    exit 0
  fi

  # 7.3 pipx uninstall
  if [[ "$INSTALL_METHOD" == "pipx" ]]; then
    pipx uninstall artifactr
    rm -rf "$DATA_DIR"

  # 7.4 venv uninstall
  elif [[ "$INSTALL_METHOD" == "venv" ]]; then
    rm -rf "$DATA_DIR"
    rm -f "$HOME/.local/bin/art"

  else
    echo "Unknown install method in state file. Attempting manual cleanup..."
    rm -rf "$DATA_DIR"
    rm -f "$HOME/.local/bin/art"
  fi

  # 7.5 Remove PATH export from rc file
  if [[ -n "$RC_FILE" && -f "$RC_FILE" ]]; then
    path_line='export PATH="$HOME/.local/bin:$PATH"'
    if grep -qF "$path_line" "$RC_FILE" 2>/dev/null; then
      echo ""
      echo "The following line was added to $RC_FILE by the installer:"
      echo "  $path_line"
      echo ""
      if confirm "Remove this line from $RC_FILE?"; then
        tmp_file="$(mktemp)"
        grep -vF "$path_line" "$RC_FILE" >"$tmp_file"
        mv "$tmp_file" "$RC_FILE"
        echo "Removed PATH export from $RC_FILE."
      fi
    fi
  fi

  # 7.6 Print success
  echo ""
  echo "artifactr uninstalled successfully."
  exit 0
fi

# ── Install / Upgrade ──────────────────────────────────────────────────────────

# 5.1 Detect existing install → upgrade flow
if command -v art &>/dev/null; then

  # 6.1 Read state file; warn if unmanaged install
  read_state_file
  if [[ -z "$INSTALL_METHOD" ]]; then
    echo "Warning: artifactr is installed but was not managed by this script."
    echo "Please uninstall it manually before re-running this installer."
    exit 1
  fi

  echo ""
  echo "Upgrading artifactr (method: $INSTALL_METHOD)..."

  # 6.2 pipx upgrade
  if [[ "$INSTALL_METHOD" == "pipx" ]]; then
    upgrade_output="$(pipx upgrade artifactr 2>&1)"
    if echo "$upgrade_output" | grep -q "already installed"; then
      echo "artifactr is already up to date."
    else
      echo "$upgrade_output"
      echo "artifactr upgraded successfully."
    fi

  # 6.3 venv upgrade
  elif [[ "$INSTALL_METHOD" == "venv" ]]; then
    upgrade_output="$("$DATA_DIR/.venv/bin/pip" install --upgrade artifactr 2>&1)"
    if echo "$upgrade_output" | grep -q "already satisfied"; then
      echo "artifactr is already up to date."
    else
      echo "$upgrade_output"
      echo "artifactr upgraded successfully."
    fi
  fi

  exit 0
fi

# ── Fresh install ──────────────────────────────────────────────────────────────

# Determine install method
if command -v pipx &>/dev/null; then
  INSTALL_METHOD="pipx"
else
  INSTALL_METHOD="venv"
fi

# 5.2 Show install summary and confirm
echo ""
echo "Install artifactr"
echo "  Method: $INSTALL_METHOD"
if [[ "$INSTALL_METHOD" == "venv" ]]; then
  echo "  Venv location: $DATA_DIR/.venv"
  echo "  Symlink: $HOME/.local/bin/art"
fi
echo ""
if ! confirm "Proceed with installation?"; then
  echo "Installation cancelled."
  exit 0
fi

# 5.3 pipx install
if [[ "$INSTALL_METHOD" == "pipx" ]]; then
  pipx install artifactr
  write_state_file

# 5.4 venv install
elif [[ "$INSTALL_METHOD" == "venv" ]]; then
  mkdir -p "$DATA_DIR"
  python3 -m venv "$DATA_DIR/.venv"
  "$DATA_DIR/.venv/bin/pip" install artifactr
  mkdir -p "$HOME/.local/bin"
  ln -sf "$DATA_DIR/.venv/bin/art" "$HOME/.local/bin/art"
  write_state_file

  # 5.5 PATH check (venv installs only)
  if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    path_line='export PATH="$HOME/.local/bin:$PATH"'
    # Idempotency guard: skip if rc file already references .local/bin
    if ! grep -q "/.local/bin" "$SHELL_RC" 2>/dev/null; then
      echo ""
      echo "~/.local/bin is not in your PATH."
      echo "The following line will be added to $SHELL_RC:"
      echo "  $path_line"
      echo ""
      if confirm "Add to $SHELL_RC?"; then
        printf '\n%s\n' "$path_line" >>"$SHELL_RC"
        RC_FILE="$SHELL_RC"
        write_state_file
        echo "Added to $SHELL_RC."
      fi
    fi
  fi
fi

# 5.6 Print success message with installed version
echo ""
if [[ "$INSTALL_METHOD" == "venv" ]]; then
  installed_version="$("$DATA_DIR/.venv/bin/pip" show artifactr 2>/dev/null | awk '/^Version:/{print $2}')"
else
  installed_version="$(pipx list --short 2>/dev/null | awk '/^artifactr /{print $2}')"
fi
installed_version="${installed_version:-unknown}"
echo "artifactr ${installed_version} installed successfully."
if [[ -n "$RC_FILE" ]]; then
  echo "Run 'source $RC_FILE' or start a new shell to update your PATH."
fi
