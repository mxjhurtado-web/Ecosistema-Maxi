# Stage 1: Build static frontend assets and download Caddy
FROM python:3.11-slim AS builder
WORKDIR /app

# Install Node.js (needed for reflex frontend compilation) and curl/tar
RUN apt-get update && apt-get install -y curl gnupg unzip tar \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Download clean Caddy binary from GitHub releases (statically compiled Go binary without setcap net_bind_service metadata)
RUN curl -L "https://github.com/caddyserver/caddy/releases/download/v2.7.6/caddy_2.7.6_linux_amd64.tar.gz" -o caddy.tar.gz \
    && tar -zxvf caddy.tar.gz caddy

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Initialize and compile frontend to static files in .web/_static/
RUN reflex init --loglevel debug
RUN reflex export --frontend-only --no-zip 2>&1; echo "--- Export step done ---"

# Stage 2: Lean runtime
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy clean Caddy binary from builder stage
COPY --from=builder /app/caddy /usr/bin/caddy

# Copy everything from builder (source + compiled .web/_static/)
COPY --from=builder /app /app

# Render uses $PORT (default 10000)
ENV PORT=10000
ENV PYTHONUNBUFFERED=1
EXPOSE 10000

# Run Reflex backend on localhost:8000 and Caddy on $PORT (10000)
CMD ["sh", "-c", "python /app/setup_env.py && reflex run --env prod --backend-only --backend-host 127.0.0.1 --backend-port 8000 --loglevel warning & caddy run --config /app/Caddyfile --adapter caddyfile"]
