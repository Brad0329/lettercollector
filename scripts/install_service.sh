#!/bin/bash
# Install and start LetterCollector as a systemd background service
set -e

CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)

echo "Configuring service for user: $CURRENT_USER at $CURRENT_DIR"

sed -e "s|%USER%|$CURRENT_USER|g" -e "s|%WORKDIR%|$CURRENT_DIR|g" scripts/letter-collector.service > /tmp/letter-collector.service
sudo mv /tmp/letter-collector.service /etc/systemd/system/letter-collector.service

sudo systemctl daemon-reload
sudo systemctl enable letter-collector
sudo systemctl restart letter-collector

echo "=== LetterCollector service status ==="
sudo systemctl status letter-collector --no-pager
