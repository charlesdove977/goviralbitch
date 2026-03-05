#!/usr/bin/env bash
# Viral Command — Install Cron Jobs (macOS launchd)
# Usage: ./scripts/install-crons.sh [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"
CRON_DIR="$PIPELINE_DIR/cron"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

echo "═══════════════════════════════════════"
echo "  VIRAL COMMAND — Install Cron Jobs"
echo "═══════════════════════════════════════"
echo ""
echo "Pipeline dir: $PIPELINE_DIR"
echo ""

if $DRY_RUN; then
    echo "[DRY RUN] No files will be copied or loaded."
    echo ""
fi

# Check we're on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "ERROR: This script is for macOS only."
    echo "For Linux, use crontab. For Windows, see docs/CRON-SETUP.md"
    exit 1
fi

# Ensure LaunchAgents directory exists
mkdir -p "$LAUNCH_AGENTS"

# Ensure log directory exists
mkdir -p "$PIPELINE_DIR/logs"

PLISTS=(
    "com.viralcommand.daily-discover.plist"
    "com.viralcommand.weekly-analyze.plist"
)

INSTALLED=0
FAILED=0

for plist in "${PLISTS[@]}"; do
    src="$CRON_DIR/$plist"
    dest="$LAUNCH_AGENTS/$plist"

    echo "────────────────────────────────────────"
    echo "Installing: $plist"

    if [[ ! -f "$src" ]]; then
        echo "  ✗ Source not found: $src"
        ((FAILED++))
        continue
    fi

    if $DRY_RUN; then
        echo "  [DRY RUN] Would copy $src → $dest"
        echo "  [DRY RUN] Would replace __PIPELINE_DIR__ with $PIPELINE_DIR"
        echo "  [DRY RUN] Would run: launchctl load $dest"
        ((INSTALLED++))
        continue
    fi

    # Unload existing if present (ignore errors)
    if [[ -f "$dest" ]]; then
        launchctl unload "$dest" 2>/dev/null || true
        echo "  ↻ Unloaded existing job"
    fi

    # Copy with path substitution
    sed "s|__PIPELINE_DIR__|$PIPELINE_DIR|g" "$src" > "$dest"
    echo "  ✓ Copied with paths resolved"

    # Load the job
    if launchctl load "$dest" 2>&1; then
        echo "  ✓ Loaded into launchd"
        ((INSTALLED++))
    else
        echo "  ✗ Failed to load"
        ((FAILED++))
    fi
done

echo ""
echo "═══════════════════════════════════════"
echo "  Installation Complete"
echo "═══════════════════════════════════════"
echo "  Installed: $INSTALLED"
echo "  Failed:    $FAILED"
echo ""

if [[ $INSTALLED -gt 0 ]]; then
    echo "  Schedules:"
    echo "    Daily discovery:  Every day at 6:00 AM UTC"
    echo "    Weekly analysis:  Friday at 6:00 AM UTC (1:00 AM EST)"
    echo ""
    echo "  Verify: launchctl list | grep viralcommand"
    echo "  Logs:   tail -f $PIPELINE_DIR/logs/daily-discover.log"
    echo ""
    echo "  Uninstall: ./scripts/uninstall-crons.sh"
fi

if $DRY_RUN; then
    echo "  Mode: DRY RUN (nothing installed)"
fi
echo "═══════════════════════════════════════"
