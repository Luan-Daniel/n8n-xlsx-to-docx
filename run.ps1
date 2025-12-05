param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

function Write-Err([string]$msg) {
  Write-Error $msg
  exit 1
}

# If running inside WSL, there will commonly be an env var `WSL_DISTRO_NAME`.
if ($env:WSL_DISTRO_NAME) {
  # Require WSL2 kernel inside WSL
  $osrel = ""
  try { $osrel = Get-Content "/proc/sys/kernel/osrelease" -ErrorAction SilentlyContinue } catch {}
  if (-not $osrel -or ($osrel -notmatch 'WSL2')) {
    Write-Err "WSL 1 detected. Please upgrade this distro to WSL 2. See: https://learn.microsoft.com/windows/wsl/install"
  }

  if (Get-Command python3 -ErrorAction SilentlyContinue) { $pyCmd = 'python3' }
  elseif (Get-Command python -ErrorAction SilentlyContinue) { $pyCmd = 'python' }
  else { Write-Err "Python not found inside WSL. Please install Python inside WSL." }

  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Err "Docker not found inside WSL. Please install/enable Docker inside WSL." }

  # Ensure tkinter available in the Linux environment
  $tkOut = & $pyCmd -c "import tkinter; print('ok')" 2>$null
  if ($LASTEXITCODE -ne 0 -or ($tkOut.Trim() -ne 'ok')) {
    Write-Err "Missing tkinter inside WSL. Install it and re-run: `n  Debian/Ubuntu:   sudo apt-get update && sudo apt-get install -y python3-tk `n  Fedora:          sudo dnf install -y python3-tkinter `n  Arch:            sudo pacman -S tk"
  }

  & $pyCmd "./src/entrypoint.py" @Args
  exit $LASTEXITCODE
}

# Not in WSL: ensure wsl is available
if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
  Write-Err "WSL not found. On Windows install/enable WSL and retry." }

# Ensure default WSL distro is running WSL 2
$wslList = $null
try { $wslList = wsl -l -v 2>$null } catch {}
if ($LASTEXITCODE -eq 0 -and $wslList) {
  $defaultLine = $wslList | Select-String '^[\*]'
  if ($defaultLine) {
    $line = $defaultLine.Line
    if ($line -match '(\d+)\s*$') {
      $ver = [int]$Matches[1]
      if ($ver -ne 2) {
        Write-Err "Default WSL distro is not WSL 2. Upgrade it: wsl --set-version <Distro> 2 (and set default version: wsl --set-default-version 2)."
      }
    }
  } else {
    $status = wsl --status 2>$null
    if (-not ($status -and ($status -match 'Default Version:\s*2'))) {
      Write-Err "Unable to confirm WSL 2. Ensure default version is 2: wsl --set-default-version 2, and upgrade your distro: wsl --set-version <Distro> 2."
    }
  }
} else {
  $status = wsl --status 2>$null
  if (-not ($status -and ($status -match 'Default Version:\s*2'))) {
    Write-Err "WSL 2 required. Set default version to 2 and upgrade your distro. See: https://learn.microsoft.com/windows/wsl/install"
  }
}

# Find python inside WSL (prefer python3)
$pythonInWsl = wsl bash -lc 'if command -v python3 >/dev/null 2>&1; then echo python3; elif command -v python >/dev/null 2>&1; then echo python; fi'
$pythonInWsl = $pythonInWsl.Trim()
if (-not $pythonInWsl) { Write-Err "Python not found inside WSL. Please install Python in your WSL distro." }

# Check docker inside WSL
$dockerCheck = wsl bash -lc 'command -v docker >/dev/null 2>&1 && echo ok || true'
if (-not ($dockerCheck.Trim() -eq 'ok')) { Write-Err "Docker not found inside WSL. Install Docker (or enable Docker inside WSL)." }

# Ensure tkinter inside WSL (uses selected python)
$tkCheck = wsl bash -lc "$pythonInWsl -c 'import tkinter; print(\"ok\")' 2>/dev/null || true"
$tkCheck = $tkCheck.Trim()
if ($tkCheck -ne 'ok') {
  Write-Err "Missing tkinter inside WSL. Install it and re-run: `n  Debian/Ubuntu:   sudo apt-get update && sudo apt-get install -y python3-tk `n  Fedora:          sudo dnf install -y python3-tkinter `n  Arch:            sudo pacman -S tk"
}

# Convert current Windows working directory to WSL path
$winPwd = (Get-Location).Path
$wslPath = (wsl wslpath -a -u "$winPwd") -replace "\r",""

function Escape-ArgForBash([string]$s) {
  return $s -replace "'","'""'""'"  # transform single quote -> '\'' for bash
}

$escapedArgs = ''
if ($Args.Count -gt 0) {
  $parts = @()
  foreach ($a in $Args) { $parts += "'" + (Escape-ArgForBash $a) + "'" }
  $escapedArgs = $parts -join ' '
}

$cmd = "cd '$wslPath' && $pythonInWsl ./src/entrypoint.py $escapedArgs"
wsl bash -lc $cmd
$exit = $LASTEXITCODE
exit $exit
