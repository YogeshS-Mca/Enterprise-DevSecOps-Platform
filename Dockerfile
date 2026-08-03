FROM python:3.14-slim

LABEL org.opencontainers.image.title="Enterprise DevSecOps Platform"
LABEL org.opencontainers.image.description="Containerized Flask application with Prometheus metrics"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Yogesh Heddure"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup app ./app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1

CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "app.app:app"]