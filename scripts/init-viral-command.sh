#!/usr/bin/env bash
# Viral Command — Repository Bootstrap Script
# Usage: ./scripts/init-viral-command.sh [--force]
# Idempotent: safe to run multiple times (won't overwrite existing files)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"

FORCE=false
if [[ "${1:-}" == "--force" ]]; then
    FORCE=true
fi

echo "═══════════════════════════════════════"
echo "  VIRAL COMMAND — Initializing..."
echo "  $(date +%Y-%m-%d\ %H:%M:%S)"
echo "═══════════════════════════════════════"
echo ""

# Verify we're in the right repo
if [[ ! -d "$PIPELINE_DIR/.claude/commands" ]]; then
    echo "ERROR: Not running from the Viral Command repo root."
    echo "Expected .claude/commands/ directory at: $PIPELINE_DIR/.claude/commands/"
    echo ""
    echo "Usage: cd /path/to/content-pipeline && ./scripts/init-viral-command.sh"
    exit 1
fi
echo "✓ Running from: $PIPELINE_DIR"
echo ""

# ──────────────────────────────────────
# Step 1: Create directory structure
# ──────────────────────────────────────
echo "Step 1: Creating directory structure..."

DIRS=(
    "data"
    "data/analytics"
    "data/analytics/raw"
    "data/insights"
    "data/hooks"
    "data/topics"
    "data/scripts"
    "data/recon"
    "data/recon/competitors"
    "data/recon/reports"
    "data/angles"
    "logs"
)

CREATED=0
for dir in "${DIRS[@]}"; do
    target="$PIPELINE_DIR/$dir"
    if [[ ! -d "$target" ]]; then
        mkdir -p "$target"
        ((CREATED++))
    fi
done
echo "  ✓ Directories ready ($CREATED created, $((${#DIRS[@]} - CREATED)) already existed)"
echo ""

# ──────────────────────────────────────
# Step 2: Initialize empty data files
# ──────────────────────────────────────
echo "Step 2: Initializing data files..."

DATA_FILES=(
    "data/idea-board.jsonl"
    "data/hooks.jsonl"
    "data/scripts.jsonl"
    "data/angles.jsonl"
    "data/calendar.jsonl"
    "data/analytics/analytics.jsonl"
)

INITIALIZED=0
SKIPPED=0
for file in "${DATA_FILES[@]}"; do
    target="$PIPELINE_DIR/$file"
    if [[ ! -f "$target" ]]; then
        touch "$target"
        ((INITIALIZED++))
    else
        ((SKIPPED++))
    fi
done
echo "  ✓ Data files ready ($INITIALIZED created, $SKIPPED already existed)"
echo ""

# ──────────────────────────────────────
# Step 3: Install Python dependencies
# ──────────────────────────────────────
echo "Step 3: Installing Python dependencies..."

DEPS_STATUS="OK"
if [[ -f "$PIPELINE_DIR/requirements.txt" ]]; then
    if command -v pip3 &>/dev/null; then
        if pip3 install -r "$PIPELINE_DIR/requirements.txt" --quiet 2>/dev/null; then
            echo "  ✓ Python packages installed"
        else
            echo "  ⚠ Some packages failed to install (run manually: pip3 install -r requirements.txt)"
            DEPS_STATUS="ISSUES"
        fi
    elif command -v pip &>/dev/null; then
        if pip install -r "$PIPELINE_DIR/requirements.txt" --quiet 2>/dev/null; then
            echo "  ✓ Python packages installed"
        else
            echo "  ⚠ Some packages failed to install (run manually: pip install -r requirements.txt)"
            DEPS_STATUS="ISSUES"
        fi
    else
        echo "  ⚠ pip not found — install Python packages manually: pip3 install -r requirements.txt"
        DEPS_STATUS="ISSUES"
    fi
else
    echo "  ⚠ requirements.txt not found"
    DEPS_STATUS="ISSUES"
fi
echo ""

# ──────────────────────────────────────
# Step 4: Check CLI tools
# ──────────────────────────────────────
echo "Step 4: Checking CLI tools..."

CLI_STATUS="OK"

# Python version
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [[ "$PY_MAJOR" -ge 3 ]] && [[ "$PY_MINOR" -ge 8 ]]; then
        echo "  ✓ Python $PY_VERSION (3.8+ required)"
    else
        echo "  ⚠ Python $PY_VERSION found but 3.8+ required"
        CLI_STATUS="ISSUES"
    fi
else
    echo "  ✗ Python 3 not found — install: https://python.org/downloads/"
    CLI_STATUS="ISSUES"
fi

# yt-dlp
if command -v yt-dlp &>/dev/null; then
    YT_VERSION=$(yt-dlp --version 2>&1)
    echo "  ✓ yt-dlp $YT_VERSION"
else
    echo "  ⚠ yt-dlp not found — install: pip3 install yt-dlp"
    CLI_STATUS="ISSUES"
fi

# Instaloader
if command -v instaloader &>/dev/null; then
    INSTA_VERSION=$(instaloader --version 2>&1 | head -1)
    echo "  ✓ Instaloader $INSTA_VERSION"
else
    echo "  ⚠ Instaloader not found — install: pip3 install instaloader"
    CLI_STATUS="ISSUES"
fi

echo ""

# ──────────────────────────────────────
# Step 5: Check .env file
# ──────────────────────────────────────
echo "Step 5: Checking API key configuration..."

ENV_STATUS="configured"
ENV_FILE="$PIPELINE_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
    echo "  ✓ .env file found"
    # Check for actual keys (not just comments)
    if grep -q "^YOUTUBE" "$ENV_FILE" 2>/dev/null || grep -q "^OPENAI" "$ENV_FILE" 2>/dev/null; then
        echo "  ✓ API keys detected"
    else
        echo "  ⚠ .env exists but no API keys set — edit .env to add your keys"
        ENV_STATUS=".env needs keys"
    fi
else
    cat > "$ENV_FILE" << 'ENVEOF'
# Viral Command API Keys
# Uncomment and set your keys below

# YouTube Data API v3 (required for /viral:discover + /viral:analyze)
# Get one at: https://console.cloud.google.com → APIs → YouTube Data API v3
# YOUTUBE_DATA_API_KEY=your_key_here

# OpenAI API (required for Whisper transcription in competitor recon)
# Get one at: https://platform.openai.com/api-keys
# OPENAI_API_KEY=your_key_here
ENVEOF
    echo "  ✓ Created .env template — add your API keys"
    ENV_STATUS=".env template created"
fi
echo ""

# ──────────────────────────────────────
# Step 6: Summary
# ──────────────────────────────────────
echo "═══════════════════════════════════════"
echo "  Viral Command — Setup Complete"
echo "═══════════════════════════════════════"
echo "  Directories:  OK"
echo "  Data files:   OK"
echo "  Dependencies: $DEPS_STATUS"
echo "  CLI tools:    $CLI_STATUS"
echo "  API keys:     $ENV_STATUS"
echo ""
echo "  Next: Run /viral:setup in Claude Code for guided API configuration"
echo "  Or:   Run /viral:onboard to set up your creator profile"
echo "═══════════════════════════════════════"
