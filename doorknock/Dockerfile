# ---------------------------------------------------
# コトムスビ (doorknock) — 代理店向け PDF 生成 API
# Shares aio2-main engine via PYTHONPATH
# ---------------------------------------------------
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# WeasyPrint + PDF deps (shared with aio2-main engine)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 libffi-dev libcairo2 \
        fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install aio2-main deps first (doorknock depends on its engine)
COPY aio2-main/requirements.txt /app/aio2-main/requirements.txt
RUN pip install --no-cache-dir -r /app/aio2-main/requirements.txt \
    && pip install --no-cache-dir psycopg2-binary azure-storage-blob azure-identity

# Install doorknock-specific deps
COPY doorknock/requirements.txt /app/doorknock/requirements.txt
RUN pip install --no-cache-dir -r /app/doorknock/requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy shared module (auth, billing, storage)
COPY shared/ /app/shared/
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

# Copy aio2-main engine (doorknock imports from it)
COPY aio2-main/ /app/aio2-main/

# Copy doorknock app
COPY doorknock/ /app/doorknock/

RUN mkdir -p /app/doorknock/output /app/doorknock/outputs

ENV HEADLESS=1 \
    PORT=8082 \
    PYTHONPATH=/app:/app/aio2-main \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app/doorknock

EXPOSE 8082

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8082/health')" || exit 1

CMD ["uvicorn", "doorknock_server:app", "--host", "0.0.0.0", "--port", "8082"]
