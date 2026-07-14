# Stage 1: Build static frontend assets
FROM python:3.11-slim AS builder

WORKDIR /app

# Install Node.js & npm (required to compile the React/Next.js frontend)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Initialize reflex (runs npm install for packages)
RUN reflex init

# Set build-time API_URL so the compiled frontend points to the correct domain.
# Render exposes both front and back on the same host.
ARG API_URL=https://orbit-dashboard-ewov.onrender.com
ENV API_URL=$API_URL

# Export frontend static assets into .web/_static/
RUN reflex export --frontend-only --no-zip

# Stage 2: Final runner container
FROM python:3.11-slim

WORKDIR /app

# Copy Caddy from the official Caddy image
COPY --from=caddy:2.7 /usr/bin/caddy /usr/bin/caddy

# Install python dependencies in final image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the compiled python backend and the static frontend folder
COPY --from=builder /app /app

# Create entrypoint shell script to run both backend and Caddy
RUN echo '#!/bin/sh\n\
reflex run --env prod --backend-only &\n\
caddy run --config Caddyfile --adapter caddyfile\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose Render port (Render defaults to 10000 or $PORT env var)
EXPOSE 10000
ENV PORT=10000

ENTRYPOINT ["/app/entrypoint.sh"]
