# Dockerfile for LetterCollector on Google Cloud Run or GCP VM
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PORT=8080 \
    HOST=0.0.0.0 \
    MCP_TRANSPORT=sse \
    LETTER_STORAGE_DIR=/app/storage

WORKDIR /app

# Install system dependencies and CJK fonts to prevent tofu on Chinese/Korean characters in Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
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

# Create persistent storage directory
RUN mkdir -p /app/storage

EXPOSE 8080

# Run LetterCollector HTTP/SSE server
CMD ["python", "-m", "src.server"]
