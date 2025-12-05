#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for unix-like systems.
# Checks for Python and Docker, then runs src/entrypoint.py.

# If running inside WSL, `WSL_DISTRO_NAME` is usually set. Allow WSL.
if [ -n "${WSL_DISTRO_NAME-}" ]; then
  IN_WSL=1
else
  IN_WSL=0
fi

# If in WSL, require WSL2 (not WSL1)
if [ "$IN_WSL" -eq 1 ]; then
  if ! grep -qi 'WSL2' /proc/sys/kernel/osrelease 2>/dev/null; then
    cat >&2 <<'EOF'
WSL 1 detected. This project requires WSL 2 for full compatibility.
Please upgrade your distro to WSL 2:
  wsl --set-version <YourDistroName> 2
  wsl --set-default-version 2
See: https://learn.microsoft.com/windows/wsl/install
EOF
    exit 2
  fi
fi

# Detect common Windows-emulator shells (Git Bash / MSYS / MINGW / Cygwin).
# These environments are known to have differences from a full Linux/WSL setup
# and can cause runtime failures; recommend using WSL instead.
if [ "$IN_WSL" -eq 0 ]; then
  uname_s=$(uname -s 2>/dev/null || true)
  # Check uname and MSYSTEM env var
  if printf '%s' "$uname_s" | grep -Ei 'mingw|msys|cygwin' >/dev/null 2>&1 || [ -n "${MSYSTEM-}" ]; then
    cat >&2 <<'EOF'
Incompatible shell detected (Git Bash / MSYS / Cygwin).
This project expects a full Unix-like environment. Please run it inside WSL (Windows Subsystem for Linux) or a real Linux/macOS shell.
Recommended: install and use WSL on Windows and run this script from a WSL shell.
EOF
    exit 2
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python not found. Please install Python (python3)." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Please install Docker." >&2
  exit 1
fi

# On Linux (including WSL), ensure tkinter is available
if [ "$(uname -s)" = "Linux" ]; then
  if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    cat >&2 <<'EOF'
Missing tkinter for Python (package 'python3-tk' or equivalent).
Install it on your distro and re-run:
  Debian/Ubuntu:   sudo apt-get update && sudo apt-get install -y python3-tk
  Fedora:          sudo dnf install -y python3-tkinter
  Arch:            sudo pacman -S --noconfirm tk
EOF
    exit 1
  fi
fi

# Resolve project root (script lives at project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$PY" "$SCRIPT_DIR/src/entrypoint.py" "$@"

