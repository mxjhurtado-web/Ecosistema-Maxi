# Stage 0: Caddy binary source
FROM caddy:2.7-alpine AS caddy

# Stage 1: Build static frontend assets
FROM python:3.11-slim AS builder

WORKDIR /app

# Install Node.js 18 (required to compile the React/Next.js frontend)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unzip \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Initialize reflex (non-interactive mode)
RUN reflex init --loglevel debug

# Set build-time API_URL so the compiled frontend points to the correct domain
ARG API_URL=https://orbit-dashboard.onrender.com
ENV API_URL=$API_URL

# Export frontend static assets into .web/_static/
RUN reflex export --frontend-only --no-zip 2>&1 || echo "Export done"

# Stage 2: Final runtime container
FROM python:3.11-slim

WORKDIR /app

# Copy Caddy binary from Stage 0
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy compiled backend + static frontend from builder stage
COPY --from=builder /app /app

# Write entrypoint script
RUN printf '#!/bin/sh\nreflex run --env prod --backend-only --loglevel warning &\ncaddy run --config /app/Caddyfile --adapter caddyfile\n' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Render uses $PORT env var (default 10000)
EXPOSE 10000
ENV PORT=10000

ENTRYPOINT ["/app/entrypoint.sh"]
