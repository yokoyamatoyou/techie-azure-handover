# ---------------------------------------------------
# コトメガネ (kotomegane) - LLM visibility / batch analysis service
# ---------------------------------------------------
FROM python:3.11-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY kotomegane/requirements.txt /app/kotomegane/requirements.txt
RUN pip install --no-cache-dir -r /app/kotomegane/requirements.txt \
    && pip install --no-cache-dir uvicorn azure-storage-blob azure-identity

COPY shared/ /app/shared/
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

COPY kotomegane/ /app/kotomegane/

RUN mkdir -p /app/kotomegane/data /app/kotomegane/exports /app/kotomegane/logs

WORKDIR /app/kotomegane

ENV HOST=0.0.0.0 \
    PORT=8083 \
    PYTHONPATH=/app

EXPOSE 8083

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8083/')" || exit 1

CMD ["python", "kotomegane_app.py"]
