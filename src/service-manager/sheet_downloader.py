import threading
import time
from typing import Callable, Optional
import requests
import re
import shlex
import webbrowser
from pathlib import Path
import os
import subprocess

# n8n app/downloads path
def get_app_downloads_folder() -> Path:
  # for now hardcode the path based on project structure (not ideal, change later)
  try:
    # Determine project root from this file location: .../src/service-manager/sheet_downloader.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]  # .../ubiq2
    downloads_dir = project_root / 'n8n-files' / 'downloads'
    downloads_dir.mkdir(parents=True, exist_ok=True)
    return downloads_dir
  except Exception:
    # Fallback to relative path if resolution fails
    fallback = Path('./n8n-files/downloads').resolve()
    try:
      fallback.mkdir(parents=True, exist_ok=True)
    except Exception:
      pass
    return fallback

def is_wsl() -> bool:
  # Detect WSL by checking /proc/version for 'microsoft'
  if os.name != 'posix':
    return False
  try:
    with open('/proc/version', 'r') as f:
      return 'microsoft' in f.read().lower()
  except Exception:
    return False

def get_windows_env_var(var: str) -> Optional[str]:
  # Get Windows env var from WSL using wslpath and powershell
  try:
    # Use powershell.exe to echo the env var
    result = subprocess.run([
      'powershell.exe', '-NoProfile', '-Command', f'echo $Env:{var}'
    ], capture_output=True, text=True)
    val = result.stdout.strip()
    return val if val else None
  except Exception:
    return None

def get_downloads_folder() -> Path:
  if os.name == 'nt':  # Windows
    return Path(os.path.join(os.environ['USERPROFILE'], 'Downloads'))
  elif is_wsl():
    # Get Windows Downloads folder from WSL and convert to WSL path
    userprofile = get_windows_env_var('USERPROFILE')
    if userprofile:
      # Convert Windows path (C:\Users\...) to WSL path (/mnt/c/Users/...)
      win_path = Path(userprofile) / 'Downloads'
      result = subprocess.run(['wslpath', str(win_path)], capture_output=True, text=True)
      if result.returncode == 0:
        return Path(result.stdout.strip())
    # fallback to home
    return Path.home() / 'Downloads'
  else:  # macOS/Linux
    return Path.home() / 'Downloads'

def get_google_sheet_download_link(url: str) -> str:
  match = re.search(r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
  if not match:
    raise ValueError("Invalid Google Sheets URL or unable to extract file ID.")

  file_id = match.group(1)
  return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"


def get_latest_xlsx(folder: Path) -> Optional[Path]:
  """
  Returns the most recently modified .xlsx file in the given folder,
  or None if no .xlsx files exist.
  """
  xlsx_files = list(folder.glob("*.xlsx"))
  if not xlsx_files:
    return None
  return max(xlsx_files, key=lambda f: f.stat().st_mtime)


def _watch_for_download(
  callback: Callable[[Optional[Path]], None],
  baseline_file: Optional[Path],
  timeout: int = 300 # 300 seconds = 5 minutes
)-> None:
  """
  Watches the downloads folder for a new .xlsx file that differs from the baseline.
  Detects when the latest xlsx file has changed (either a new file appeared or an existing one was modified).
  """
  start_time = time.time()
  downloads = get_downloads_folder()

  try:
    while (time.time() - start_time) < timeout:
      current_latest = get_latest_xlsx(downloads)
      
      # Check if we have a new latest file
      if current_latest != baseline_file:
        # Either a new file appeared, or None became a file
        if current_latest is not None:
          print(f"  [i] New file detected: {current_latest}")
          callback(current_latest)
          return
      
      time.sleep(3)
    # Timeout reached
    print(f"  [!] Watcher timed out after {timeout} seconds.")
    # callback(None)
  except Exception as e:
    print(f"  [!] Error while monitoring downloads: {e}")
    # callback(None)

def is_valid_url(url: str) -> bool:
    """
    Validate that the URL starts with http:// or https://
    and contains no spaces.
    """
    pattern = re.compile(r'^(https?://\S+)$')
    return bool(pattern.match(url))

def sanitize_url(url: str) -> str:
    """
    Escape the URL string safely for passing to subprocess.
    Uses shlex.quote to prevent command injection.
    """
    return shlex.quote(url)

def open_browser(url: str) -> bool:
    """Open browser, using explorer.exe in WSL, else webbrowser.open"""
    if not is_valid_url(url):
        print(f"  [!] Invalid URL: {url}")
        return False
    safe_url = sanitize_url(url)

    if is_wsl():
        try:
            # explorer.exe can open URLs in Windows default browser from WSL
            subprocess.run(["cmd.exe", "/c", "start", '""', url], check=True)
            return True
        except Exception as e:
            print(f"  [!] Failed to open browser via explorer.exe: {e}")
            return False
    else:
        return webbrowser.open(url, 2, autoraise=True)

def download_sheet(url: str, callback: Callable[[Optional[Path]], None]) -> list[int, Optional[threading.Thread]]:
    download_url: str = ""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        download_url = get_google_sheet_download_link(url)
    except ValueError as e:
        print(f"  [!] Error: {e}")
        return -1, None

    try:
        # Attempting direct download
        response = requests.get(download_url, headers=headers, timeout=3)
        content_type = response.headers.get("Content-Type", "")

        is_unexpected_content = "text/html" in content_type or "application/json" in content_type
        if response.status_code == 401 or is_unexpected_content: # Unauthorized. Fallback to manual authentication.
            print("  [i] Authentication required. Opening browser for authentication...")
            # Get the latest xlsx file before opening browser as baseline
            baseline_file = get_latest_xlsx(get_downloads_folder())
            thread = threading.Thread(target=_watch_for_download, args=(callback, baseline_file), daemon=True)
            res = open_browser(download_url)
            if not res:
                print(f"  [!] Failed to open web browser for authentication. Please download the file manually: {download_url}")
                # Don't join thread - return immediately to avoid blocking GUI
                return -2, None
            thread.start()
            print("  [i] Returning to caller; waiting for download in the background...")
            return 1, thread # Indicate that manual download is in progress

        if response.status_code == 200: # OK
            print("  [i] Writing file...")
            output_path = get_app_downloads_folder() / f"sheet_{time.time()}.xlsx"
            with open(output_path, "wb") as f:
                f.write(response.content)
            callback(output_path)
            return 0, None # Success

        else:
            print(f"  [!] Failed to download file. HTTP Status Code: {response.status_code}")
            return -3, None
    except requests.RequestException as e:
        print(f"  [!] Network error occurred: {e}")
        return -4, None
    except requests.Timeout as e:
        print(f"  [!] The request timed out: {e}")
        return -5, None
    except Exception as e:
        print(f"  [!] An unexpected error occurred: {e}")
        return -6, None