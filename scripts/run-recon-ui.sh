#!/bin/bash
# Viral Command — Launch Recon Intelligence UI
# Usage: ./scripts/run-recon-ui.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"

echo "═══════════════════════════════════════"
echo "  VIRAL COMMAND — Recon Intelligence"
echo "═══════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Install Python 3.9+."
    exit 1
fi

# Install deps if needed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r "$PIPELINE_DIR/requirements.txt"
    echo ""
fi

# Create data directories
mkdir -p "$PIPELINE_DIR/data/recon/competitors"
mkdir -p "$PIPELINE_DIR/data/recon/reports"
mkdir -p "$PIPELINE_DIR/data/recon/cache"
mkdir -p "$PIPELINE_DIR/data/recon/logs"

# Launch Flask
echo "Starting Recon UI on http://localhost:5001"
echo ""

cd "$PIPELINE_DIR"
PYTHONPATH="$PIPELINE_DIR" python3 -m recon.web.app
