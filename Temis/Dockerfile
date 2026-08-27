# Production Dockerfile for TEMIS Web Flow (Reflex + FastAPI)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required by Reflex for Next.js compilation)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir reflex

# Copy application source code
COPY . .

# Initialize Reflex app
RUN python -m reflex init

# Expose web port
EXPOSE 3000
EXPOSE 8000

# Start Reflex in production mode
CMD ["python", "-m", "reflex", "run", "--env", "prod", "--frontend-port", "3000"]
