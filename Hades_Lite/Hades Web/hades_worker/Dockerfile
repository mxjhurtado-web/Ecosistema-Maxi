FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY hades_worker/requirements.txt /app/hades_worker/
COPY hades_core/requirements.txt /app/hades_core/
COPY hades_api/requirements.txt /app/hades_api/
COPY hades_api/requirements_drive.txt /app/hades_api/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r hades_worker/requirements.txt
RUN pip install --no-cache-dir -r hades_core/requirements.txt
RUN pip install --no-cache-dir -r hades_api/requirements.txt
RUN pip install --no-cache-dir -r hades_api/requirements_drive.txt

# Copiar código
COPY hades_worker /app/hades_worker
COPY hades_core /app/hades_core
COPY hades_api /app/hades_api

# Comando por defecto (worker)
CMD ["celery", "-A", "hades_worker.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
