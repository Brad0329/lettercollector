#!/bin/bash
# LetterCollector VM Setup Script (Ubuntu/Debian)
set -e

echo "=== 1. System packages & CJK fonts installation ==="
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip fonts-noto-cjk fonts-wqy-zenhei curl

echo "=== 2. Setting up Python virtual environment ==="
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -e .

echo "=== 3. Creating storage directory ==="
mkdir -p storage

echo "=== Setup complete! ==="
echo "To test run manually:"
echo "  PORT=8080 MCP_TRANSPORT=sse .venv/bin/python -m src.server"
