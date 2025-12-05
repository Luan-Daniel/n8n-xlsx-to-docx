#!/usr/bin/env bash
set -euo pipefail

# Simple stopper for the n8n container created by start-n8n.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="n8n-custom"
IMAGE_NAME="n8n-custom:local"
ENV_FILE="$SCRIPT_DIR/.env"

err() { printf '%s\n' "$*" >&2; }

# If there's an env file, source it (safe read-only load)
if [ -f "$ENV_FILE" ]; then
	# shellcheck disable=SC1090
	source "$ENV_FILE"
fi

if docker ps -a --format '{{.Names}}' | grep -x "$CONTAINER_NAME" >/dev/null 2>&1; then
	if docker ps --format '{{.Names}}' | grep -x "$CONTAINER_NAME" >/dev/null 2>&1; then
		echo "[i] Stopping container '$CONTAINER_NAME'..."
		docker stop "$CONTAINER_NAME" >/dev/null || true
	else
		echo "[i] Container '$CONTAINER_NAME' exists but is not running."
	fi

	# echo "[i] Removing container '$CONTAINER_NAME'..."
	# docker rm -v "$CONTAINER_NAME" >/dev/null || true
	# echo "[i] Container '$CONTAINER_NAME' removed."
else
	echo "[i] No container named '$CONTAINER_NAME' found."
  exit 1
fi

echo "[i] stop-n8n.sh finished."
exit 0
