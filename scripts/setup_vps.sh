#!/bin/bash
set -e

echo "=== [1/4] Installing system dependencies & Chromium ==="
sudo apt-get update -qq
sudo apt-get install -y -qq \
    chromium-browser \
    chromium-chromedriver \
    python3 \
    python3-pip \
    python3-venv \
    fonts-liberation \
    xdg-utils \
    --no-install-recommends

echo "=== [2/4] Creating virtual environment ==="
python3 -m venv venv
source venv/bin/activate

echo "=== [3/4] Installing Python requirements ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [4/4] Done! ==="
echo "1. Put cookies into data/cookies.json"
echo "2. Copy data/config.example.json -> data/config.json"
echo "3. Run: source venv/bin/activate && python main.py"
