<!--List of System requirements:
- linux: any recent distro should work
- macos: recent version should work (untested)
- windows: wsl2 is installed and set as default
- we need docker, python3, pip3, python3-tk installed on the unix-like environment (wsl2 or linux).
- also curl, sqlite3, and jq are used in setup scripts.
- other dependencies are installed automatically during the first execution and need internet access.
-->

<!-- Guide for installing each of the system dependencies-->

# System Setup Guide

This guide explains how to install all required dependencies on **Linux**, and **Windows (WSL2)**.  
Once inside a Unix-like environment (Linux or WSL2), the installation steps are unified.

---

## System Requirements
- **Linux**: Any recent distribution (Ubuntu, Debian, Fedora, Arch, etc.)
- **macOS**: Recent version should work (untested)
- **Windows**: Requires **WSL2** installed and set as default
- **Dependencies**:
  - Docker
  - Python3
  - pip3
  - python3-tk
  - curl
  - sqlite3
  - jq
- Other dependencies are installed automatically during first execution (requires internet access).

---

## Windows Setup (WSL2)

### 1. Enable WSL
Open **PowerShell as Administrator** and run:
```powershell
wsl --install
```

This installs WSL with the default Linux distribution (usually Ubuntu).  
If you already have WSL installed, upgrade to WSL2:

```powershell
wsl --set-default-version 2
```

### 2. Launch WSL2
Open Ubuntu (or your chosen distro) from the Start Menu, or run:
```powershell
wsl
```

You are now inside a Linux shell. Continue with the **Linux setup steps** below.

---

## Linux & WSL2 Setup

Run the following commands inside your Linux terminal (Ubuntu/Debian-based examples):

### 1. Update Package Manager
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Python3, pip3, and python3-tk
```bash
sudo apt install -y python3 python3-pip python3-tk
```

### 3. Install Docker
```bash
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
```

Add your user to the Docker group to avoid using `sudo`:
```bash
sudo usermod -aG docker $USER
```

Log out and back in for changes to take effect.
```bash
# in wsl, you can do 'exit' or close the terminal window
exit
# then reopen wsl from the comandline
wsl
```

### 4. Install curl, sqlite3, and jq
```bash
sudo apt install -y curl sqlite3 jq
```