FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY hades_api/requirements.txt /app/hades_api/
COPY hades_core/requirements.txt /app/hades_core/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r hades_api/requirements.txt
RUN pip install --no-cache-dir -r hades_core/requirements.txt

# Copiar código
COPY hades_api /app/hades_api
COPY hades_core /app/hades_core

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["uvicorn", "hades_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
