# Stage 1: Build static frontend assets
FROM python:3.11-slim AS builder
WORKDIR /app

# Install Node.js (needed for reflex frontend compilation)
RUN apt-get update && apt-get install -y curl gnupg unzip \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Initialize and compile frontend to static files in .web/_static/
RUN reflex init --loglevel debug
RUN reflex export --frontend-only --no-zip 2>&1; echo "--- Export step done ---"

# Stage 2: Lean runtime (no Node.js needed - backend serves pre-compiled static files)
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything from builder (source + compiled .web/_static/)
COPY --from=builder /app /app

# Render uses $PORT (default 10000)
ENV PORT=10000
ENV PYTHONUNBUFFERED=1
EXPOSE 10000

# Reflex backend-only mode serves both the API and the pre-compiled static frontend
CMD ["sh", "-c", "reflex run --env prod --backend-only --backend-host 0.0.0.0 --backend-port ${PORT:-10000} --loglevel warning"]
