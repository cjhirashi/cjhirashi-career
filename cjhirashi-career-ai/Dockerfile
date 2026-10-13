# Harness de agentes de cjhirashi-career (spec 009). Mismo patrón que cjhirashi-career-api.
FROM python:3.11-slim

LABEL maintainer="Carlos <cjhirashi@gmail.com>"
LABEL description="Harness de agentes (FastAPI) - cjhirashi-career-ai"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml .
RUN pip install --upgrade pip && pip install .

COPY . .

RUN useradd -m -u 1000 aiuser && chown -R aiuser:aiuser /app
USER aiuser

# Puerto interno del harness (plan §5): Caddy /ai/ -> cjhirashi-career-ai:8010
EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8010/health')" || exit 1

CMD ["uvicorn", "app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8010", "--workers", "1"]
