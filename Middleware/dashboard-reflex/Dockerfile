# Stage 0: Caddy binary
FROM caddy:2.7-alpine AS caddy

# Stage 1: Build static frontend assets
FROM python:3.11-slim AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl gnupg unzip \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Initialize reflex and compile frontend
RUN reflex init --loglevel debug
RUN reflex export --frontend-only --no-zip 2>&1; echo "Export step finished"

# Stage 2: Slim runtime
FROM python:3.11-slim
WORKDIR /app

# Caddy binary for serving static frontend
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy compiled app from builder
COPY --from=builder /app /app

EXPOSE 10000
ENV PORT=10000

# Run backend + Caddy via CMD (shell form avoids exec permission issues)
CMD sh -c 'reflex run --env prod --backend-only --loglevel warning & caddy run --config /app/Caddyfile --adapter caddyfile'
