#!/bin/bash
# Viral Command — Launch Recon Intelligence UI
# Usage: ./scripts/run-recon-ui.sh [--docker]
# Runs natively by default. With --docker (or when python3 is missing but
# Docker is available) the UI runs in the goviralbro container instead.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"

echo "═══════════════════════════════════════"
echo "  VIRAL COMMAND — Recon Intelligence"
echo "═══════════════════════════════════════"
echo ""

# Inside the goviralbro container the UI usually already runs as the `recon`
# service — don't start a second copy.
if [ -n "${GOVIRALBRO_DOCKER:-}" ]; then
    if command -v curl &> /dev/null && curl -fsS -m 2 -o /dev/null "http://recon:5001/" 2>/dev/null; then
        echo "Recon UI is already running — open http://localhost:5001 in your browser."
        exit 0
    fi
    echo "Note: you are inside the goviralbro container. If your browser can't"
    echo "reach the UI, run this script from a host terminal instead."
    echo ""
fi

# Docker mode: --docker flag, or python3 missing on the host
USE_DOCKER=0
if [ "${1:-}" = "--docker" ]; then
    USE_DOCKER=1
elif [ -z "${GOVIRALBRO_DOCKER:-}" ] && ! command -v python3 &> /dev/null; then
    if docker compose version &> /dev/null; then
        echo "python3 not found — starting the UI in Docker instead."
        USE_DOCKER=1
    fi
fi

if [ "$USE_DOCKER" = "1" ]; then
    echo "Starting Recon UI on http://localhost:5001 (Ctrl+C to stop)"
    echo ""
    cd "$PIPELINE_DIR"
    exec docker compose up recon
fi

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
