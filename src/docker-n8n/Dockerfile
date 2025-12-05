FROM n8nio/n8n:1.121.3

# Instalar dependências necessárias para gráficos
USER root

# Support both Alpine (apk) and Debian/Ubuntu (apt-get) based images.
RUN set -eux; \
    if command -v apk >/dev/null 2>&1; then \
        apk add --no-cache \
            build-base \
            cairo-dev \
            pango-dev \
            libjpeg-turbo-dev \
            giflib-dev \
            librsvg; \
    elif command -v apt-get >/dev/null 2>&1; then \
        apt-get update && apt-get install -y --no-install-recommends \
            build-essential \
            libcairo2-dev \
            libpango1.0-dev \
            libjpeg-dev \
            libgif-dev \
            librsvg2-dev && \
        rm -rf /var/lib/apt/lists/*; \
    else \
        echo "No known package manager found (apk or apt-get)." >&2; exit 1; \
    fi

# Enable community nodes (needed for docxtemplater)
ENV N8N_COMMUNITY_PACKAGES_ENABLED=true

USER node

# Enable community nodes ?
ENV N8N_COMMUNITY_NODES_ENABLED=true

# For now, additional packages are being installed in the setup script. For some reason, installing them here doesn't work. npm just doesn't save the packages.