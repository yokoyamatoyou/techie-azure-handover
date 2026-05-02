# ---------------------------------------------------
# コトメイク (notecode) — AI 記事生成サービス
# ---------------------------------------------------
FROM python:3.11-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for image processing (opencv-headless, pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
        fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY notecode/requirements.txt /app/notecode/requirements.txt
RUN pip install --no-cache-dir -r /app/notecode/requirements.txt \
    && pip install --no-cache-dir azure-storage-blob azure-identity

# Copy shared module (auth, billing, storage)
COPY shared/ /app/shared/
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

# Copy application code
COPY notecode/ /app/notecode/

RUN mkdir -p /app/notecode/logs /app/notecode/note/generated_images

WORKDIR /app/notecode

ENV HEADLESS=1 \
    PORT=8080 \
    PYTHONPATH=/app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

CMD ["python", "-m", "note.note_writer_app"]
