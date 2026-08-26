FROM python:3.11-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# Instalación de dependencias del sistema para WeasyPrint/Pango/Cairo
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80retries && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
        fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia del código fuente (incluyendo la carpeta tools/) y requirements
COPY . /app

# Instalación de las librerías de Python requeridas
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Creación de carpetas de salida
RUN mkdir -p /mnt/disco2/cjhirashi-data/mcp-outputs/cvs /mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters

EXPOSE 8000

CMD ["python", "server.py"]