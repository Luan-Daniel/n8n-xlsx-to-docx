#!/usr/bin/env bash
set -euo pipefail

# Enhanced runner for n8n with automatic build, .env loading and persistent storage at "n8n-data:/home/node/.n8n"
# - Builds local Docker image from the Dockerfile in this directory if it's missing
# - Loads environment variables from ./ .env when present (passed to the container)
# - Uses a named volume from .env (N8N_VOLUME_NAME) or falls back to ./n8n-data host dir

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="n8n-custom"
IMAGE_NAME="n8n-custom:local"
ENV_FILE="$SCRIPT_DIR/.env"

set -a
source "$ENV_FILE"
set +a

# Helper: print to stderr
err() { printf '%s\n' "$*" >&2; }

# Determine data mount: prefer Docker named volume from N8N_VOLUME_NAME, else use host dir ./n8n-data
if [ -z "${N8N_VOLUME_NAME-unset}" ]; then
	DATA_MOUNT="${N8N_VOLUME_NAME}:/home/node/.n8n"
	DATA_IS_VOLUME=true
else
	HOST_DATA_DIR="$SCRIPT_DIR/n8n-data"
	mkdir -p "$HOST_DATA_DIR"
	DATA_MOUNT="$HOST_DATA_DIR:/home/node/.n8n"
	DATA_IS_VOLUME=false
fi

# Ensure application files directory exists regardless of volume mode
mkdir -p "$SCRIPT_DIR/../../n8n-files"
mkdir -p "$SCRIPT_DIR/../../n8n-files/sheets"
mkdir -p "$SCRIPT_DIR/../../n8n-files/images"
mkdir -p "$SCRIPT_DIR/../../n8n-files/documents"
mkdir -p "$SCRIPT_DIR/../../n8n-files/templates"
mkdir -p "$SCRIPT_DIR/../../n8n-files/downloads"

# Build image if missing, or rebuild if Dockerfile is newer than the image
DOCKERFILE="$SCRIPT_DIR/Dockerfile"
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
	echo "[i] Local image '$IMAGE_NAME' not found — building from Dockerfile in $SCRIPT_DIR"
	(cd "$SCRIPT_DIR" && docker build -t "$IMAGE_NAME" .)
else
	# If Dockerfile exists, compare its mtime (epoch) with the image Created timestamp
	if [ -f "$DOCKERFILE" ]; then
		# Get image created timestamp in a format `date` can parse
		image_created=$(docker image inspect -f '{{.Created}}' "$IMAGE_NAME" 2>/dev/null || true)
		if [ -n "$image_created" ]; then
			# Convert to epoch seconds; fall back to 0 on failure
			image_epoch=$(date -d "$image_created" +%s 2>/dev/null || echo 0)
			dockerfile_epoch=$(stat -c %Y "$DOCKERFILE" 2>/dev/null || echo 0)

			if [ "$image_epoch" -lt "$dockerfile_epoch" ]; then
				echo "[i] Image '$IMAGE_NAME' is older than '$DOCKERFILE' — rebuilding"
				(cd "$SCRIPT_DIR" && docker build -t "$IMAGE_NAME" .)
			else
				echo "[i] Using existing image '$IMAGE_NAME'"
			fi
			# removes first_run_done file to ensure setup-n8n.sh runs again after image rebuild
			if [ "$DATA_IS_VOLUME" = true ]; then
				if docker exec "$CONTAINER_NAME" sh -c 'test -f /home/node/.n8n/.first_run_done'; then
					docker exec "$CONTAINER_NAME" sh -c 'rm /home/node/.n8n/.first_run_done'
				fi
			else
				if [ -f "$HOST_DATA_DIR/.first_run_done" ]; then
					rm "$HOST_DATA_DIR/.first_run_done"
				fi
			fi
		else
			echo "[i] Couldn't determine creation time for image '$IMAGE_NAME' — using existing image"
		fi
	else
		echo "[i] Dockerfile not found in $SCRIPT_DIR — using existing image '$IMAGE_NAME'"
	fi
fi

# Stop and remove existing container if present
if docker ps -a --format '{{.Names}}' | grep -x "$CONTAINER_NAME" >/dev/null 2>&1; then
	echo "[i] Stopping and removing existing container '$CONTAINER_NAME'"
	docker rm -f "$CONTAINER_NAME" >/dev/null || true
fi

# Allow passing extra docker run args via CLI
EXTRA_ARGS=()
if [ "$#" -gt 0 ]; then
	EXTRA_ARGS=("$@")
fi

# Build docker run command
DOCKER_RUN=(docker run -d --name "$CONTAINER_NAME" -p ${HOST_PORT}:5678 -v "$DATA_MOUNT" -v "$SCRIPT_DIR/../../n8n-files:/files" --add-host=host.docker.internal:host-gateway)

# If there is an env file, pass it through
if [ -f "$ENV_FILE" ]; then
	DOCKER_RUN+=(--env-file "$ENV_FILE")
fi

# Add restart policy and any extra args
DOCKER_RUN+=(--restart unless-stopped)
DOCKER_RUN+=("${EXTRA_ARGS[@]}")

# Image and default command
DOCKER_RUN+=("$IMAGE_NAME")

echo "[i] Running container with: ${DOCKER_RUN[*]}"
"${DOCKER_RUN[@]}"

echo "[i] Container '$CONTAINER_NAME' started."

# Check for first run (by presence of .first_run_done file)
FIRST_RUN=false
if [ "$DATA_IS_VOLUME" = true ]; then
	if ! docker exec "$CONTAINER_NAME" sh -c 'test -f /home/node/.n8n/.first_run_done'; then
		FIRST_RUN=true
	fi
else
	if [ ! -f "$HOST_DATA_DIR/.first_run_done" ]; then
		FIRST_RUN=true
	fi
fi

# Run setup-n8n.sh only if it's the first run
if [ "$FIRST_RUN" = false ]; then
	echo "[i] Not first run; skipping setup-n8n.sh."
	exit 0
fi

echo "[i] Running setup-n8n.sh..."
"$SCRIPT_DIR/setup-n8n.sh"

# touch a file to indicate first run is done
if [ "$DATA_IS_VOLUME" = true ]; then
	docker exec "$CONTAINER_NAME" sh -c 'touch /home/node/.n8n/.first_run_done'
else
	touch "$HOST_DATA_DIR/.first_run_done"
fi
echo "[i] setup-n8n.sh finished."