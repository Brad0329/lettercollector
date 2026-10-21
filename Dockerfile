# Dockerfile for LetterCollector on Google Cloud Run or GCP VM
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PORT=8080 \
    HOST=0.0.0.0 \
    MCP_TRANSPORT=http \
    LETTER_STORAGE_DIR=/app/storage

WORKDIR /app

# CJK font for calligrapher names in grid.png (visualizer.py looks for wqy-zenhei on Linux).
# fonts-noto-cjk was dropped: visualizer never loads it, and it bloated the image by hundreds of MB.
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-wqy-zenhei \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast python dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project definition and install dependencies
COPY pyproject.toml README.md /app/
RUN uv pip install --system --no-cache -e .

# Copy application source code
COPY src/ /app/src/

# Storage directory. On Cloud Run this is in-memory and emptied on every cold start —
# characters are simply re-fetched from sf.zdic.net on next use (accepted for low traffic).
RUN mkdir -p /app/storage

EXPOSE 8080

# Run LetterCollector HTTP/SSE server
CMD ["python", "-m", "src.server"]
