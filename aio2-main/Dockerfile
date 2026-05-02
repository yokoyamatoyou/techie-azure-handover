# ---------------------------------------------------
# コトミガキ (aio2-main) — SEO/AIO 分析サービス
# Base: Playwright image for Chromium + WeasyPrint deps
# ---------------------------------------------------
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# The Playwright base image already includes the browser/runtime packages we
# need for the current NiceGUI analysis flow. Keeping an extra apt layer here
# made ACR builds brittle on Ubuntu Noble mirrors, so we rely on the base image
# and Python wheels instead.

WORKDIR /app

# Install Python deps first (better layer caching)
COPY aio2-main/requirements.txt /app/aio2-main/requirements.txt
RUN pip install --no-cache-dir -r /app/aio2-main/requirements.txt \
    && pip install --no-cache-dir psycopg2-binary azure-storage-blob azure-identity

# Install Playwright browsers (Chromium only)
RUN playwright install --with-deps chromium

# Copy shared module (auth, billing, storage)
COPY shared/ /app/shared/
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

# Copy application code
COPY aio2-main/ /app/aio2-main/

# Create writable dirs
RUN mkdir -p /app/aio2-main/data/poc_outputs/reports /app/aio2-main/logs /app/aio2-main/static

WORKDIR /app/aio2-main

ENV HEADLESS=1 \
    PORT=8081 \
    CONTAINER_ENV=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/')" || exit 1

CMD ["python", "run_app.py"]
