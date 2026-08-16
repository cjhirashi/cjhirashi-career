# Imagen base Python 3.11 slim
FROM python:3.11-slim

# Metadatos
LABEL maintainer="Carlos <cjhirashi@gmail.com>"
LABEL description="MCP Tools API REST con FastAPI y PostgreSQL"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copiar archivo de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear usuario no-root
RUN useradd -m -u 1000 apiuser && \
    chown -R apiuser:apiuser /app

# Cambiar a usuario no-root
USER apiuser

# Exponer puerto
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

# Comando de inicio
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
