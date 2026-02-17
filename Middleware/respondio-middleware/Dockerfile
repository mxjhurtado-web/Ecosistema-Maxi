# Dockerfile for Render deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from the api subfolder
COPY api/requirements.txt ./api/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r api/requirements.txt

# Copy the rest of the application code
COPY api/ ./api/
COPY shared/ ./shared/

# Set Python path to ensure imports work correctly
ENV PYTHONPATH=/app

# Expose the port Render expects (default 10000, but we'll use ORBIT's 8000)
# Note: Render overrides this via the $PORT env var
EXPOSE 8000

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
