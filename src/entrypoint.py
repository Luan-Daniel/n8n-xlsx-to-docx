#!/usr/bin/env python3
"""
Project entrypoint.

Responsibilities:
- Check basic system requirements (OS, Docker)
- Create and populate a virtualenv at `./.venv` if missing
- Install `requirements.txt` into the venv
- Launch the main application `src/service-manager/main.py` using the venv python

Designed to be safe for interactive runs for end users.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "src" / "requirements.txt"
REQUIREMENTS_HASH_FILE = VENV_DIR / ".requirements_hash"
MAIN_SCRIPT = ROOT / "src" / "service-manager" / "main.py"


def is_wsl() -> bool:
  # WSL environment detection
  if platform.system() != "Linux":
    return False
  try:
    with open("/proc/version", "r") as f:
      return "microsoft" in f.read().lower()
  except Exception:
    return False


def is_msys_like() -> bool:
  """Detect Git Bash / MSYS / MINGW / Cygwin shells via env or uname.

  This returns True for environments that emulate a Unix shell on top of
  Windows (Git Bash, MSYS, MINGW, Cygwin). These are supported by users
  but may be incompatible with expected Linux/WSL behaviour; we warn when
  detected so users can choose WSL instead.
  """
  if os.environ.get("MSYSTEM"):
    return True
  try:
    uname = os.uname().sysname.lower()
    if any(x in uname for x in ("mingw", "msys", "cygwin")):
      return True
  except Exception:
    pass
  return False


def is_windows_python_executable() -> bool:
  """Heuristic to detect a Windows-installed python executable.

  We check for Windows-style paths in sys.executable or a Windows
  platform string. If this returns True and we're not inside WSL,
  it's likely the user is running a Windows Python (not a Linux one).
  """
  exe = str(sys.executable or "")
  # Typical Windows python executables contain backslashes or a drive letter
  if "\\" in exe or (len(exe) > 1 and exe[1] == ":"):
    return True
  if platform.system().lower().startswith("win"):
    return True
  return False


def prompt_yes_no(message: str, default: bool = True) -> bool:
  yes = "Y/n" if default else "y/N"
  try:
    resp = input(f"{message} [{yes}]: ").strip().lower()
  except EOFError:
    return default
  if not resp:
    return default
  return resp[0] == "y"


def compute_requirements_hash() -> str:
  """Compute SHA256 hash of the requirements.txt file."""
  if not REQUIREMENTS.exists():
    return ""
  
  sha256 = hashlib.sha256()
  with open(REQUIREMENTS, "rb") as f:
    sha256.update(f.read())
  return sha256.hexdigest()


def get_saved_requirements_hash() -> str:
  """Read the saved requirements hash from the hash file."""
  if not REQUIREMENTS_HASH_FILE.exists():
    return ""
  
  try:
    return REQUIREMENTS_HASH_FILE.read_text().strip()
  except Exception:
    return ""


def save_requirements_hash(hash_value: str) -> None:
  """Save the requirements hash to the hash file."""
  try:
    REQUIREMENTS_HASH_FILE.write_text(hash_value)
  except Exception as exc:
    print(f"Warning: Failed to save requirements hash: {exc}")


def should_install_requirements(force: bool = False) -> bool:
  """Check if requirements need to be installed based on hash comparison."""
  if force:
    print("Forced requirements installation requested.")
    return True
  
  if not REQUIREMENTS.exists():
    return False
  
  current_hash = compute_requirements_hash()
  saved_hash = get_saved_requirements_hash()
  
  if not saved_hash:
    print("No previous requirements installation detected.")
    return True
  
  if current_hash != saved_hash:
    print("Requirements file has changed since last installation.")
    return True
  
  print("Requirements file unchanged, skipping installation.")
  return False


def ensure_venv() -> Path:
  """Create a venv at `VENV_DIR` if missing and return the python executable path."""
  if not VENV_DIR.exists():
    print(f"Creating virtual environment at {VENV_DIR}...")
    try:
      subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    except subprocess.CalledProcessError:
      print("Failed to create virtual environment. Please create one manually and re-run.")
      raise

  if platform.system() == "Windows":
    py = VENV_DIR / "Scripts" / "python.exe"
  else:
    py = VENV_DIR / "bin" / "python"

  if not py.exists():
    raise FileNotFoundError(f"Python executable not found in venv at {py}")
  return py


def install_requirements(venv_python: Path, force: bool = False) -> None:
  if not should_install_requirements(force):
    return

  if not REQUIREMENTS.exists():
    print(f"No requirements file found at {REQUIREMENTS}; skipping install.")
    return

  print("Installing Python dependencies into virtualenv...")
  cmd = [str(venv_python), "-m", "pip", "install", "-U", "pip"]
  subprocess.run(cmd, check=True)
  cmd = [str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS)]
  subprocess.run(cmd, check=True)
  
  # Save the hash after successful installation
  current_hash = compute_requirements_hash()
  save_requirements_hash(current_hash)
  print("Requirements installation complete.")


def run_main_with_venv(venv_python: Path) -> int:
  if not MAIN_SCRIPT.exists():
    print(f"Main script not found at {MAIN_SCRIPT}")
    return 2
  cmd = [str(venv_python), str(MAIN_SCRIPT)]
  print("Launching main application...")
  return subprocess.call(cmd)


def main() -> int:
  parser = argparse.ArgumentParser(description="Project entrypoint")
  parser.add_argument(
    "--force-requirements-download",
    action="store_true",
    help="Force reinstallation of requirements even if unchanged"
  )
  args = parser.parse_args()

  print(f"Project root: {ROOT}")

  # Basic system checks
  system = platform.system()
  print(f"Detected OS: {system}{' (WSL)' if is_wsl() else ''}")
  
  if (is_msys_like() or (is_windows_python_executable() and not is_wsl())):
    print("Warning: It looks like you're running Python from a Windows installation or from a Win32-emulating shell (Git Bash/MSYS/Cygwin).")
    print("This project expects a full Unix-like environment (Linux or WSL/macOS). Consider using WSL on Windows to avoid issues.")
    print()
  
  if system not in ("Linux", "Darwin", "Windows"):
    print("Warning: OS not explicitly supported, continuing anyway.")

  try:
    venv_python = ensure_venv()
  except Exception as exc:
    print(f"Error ensuring virtualenv: {exc}")
    return 4

  try:
    install_requirements(venv_python, force=args.force_requirements_download)
  except subprocess.CalledProcessError as exc:
    print("Failed installing requirements. You can inspect the error above and try again.")
    return 5

  try:
    return run_main_with_venv(venv_python)
  except Exception as exc:
    print(f"Error running main script: {exc}.")
    return 6

if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except KeyboardInterrupt:
    print("Interrupted by user")
    raise
