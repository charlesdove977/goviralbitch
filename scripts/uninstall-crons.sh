#!/usr/bin/env bash
# Viral Command — Uninstall Cron Jobs (macOS launchd)
# Usage: ./scripts/uninstall-crons.sh [--dry-run]

set -euo pipefail

LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

echo "═══════════════════════════════════════"
echo "  VIRAL COMMAND — Uninstall Cron Jobs"
echo "═══════════════════════════════════════"
echo ""

if $DRY_RUN; then
    echo "[DRY RUN] No files will be removed."
    echo ""
fi

PLISTS=(
    "com.viralcommand.daily-discover.plist"
    "com.viralcommand.weekly-analyze.plist"
)

REMOVED=0
NOT_FOUND=0

for plist in "${PLISTS[@]}"; do
    dest="$LAUNCH_AGENTS/$plist"

    if [[ ! -f "$dest" ]]; then
        echo "  ○ $plist — not installed (skip)"
        ((NOT_FOUND++))
        continue
    fi

    if $DRY_RUN; then
        echo "  [DRY RUN] Would unload and remove: $dest"
        ((REMOVED++))
        continue
    fi

    # Unload
    launchctl unload "$dest" 2>/dev/null || true
    echo "  ✓ Unloaded: $plist"

    # Remove
    rm -f "$dest"
    echo "  ✓ Removed: $dest"
    ((REMOVED++))
done

echo ""
echo "═══════════════════════════════════════"
echo "  Uninstall Complete"
echo "═══════════════════════════════════════"
echo "  Removed:   $REMOVED"
echo "  Not found: $NOT_FOUND"
if $DRY_RUN; then
    echo "  Mode:      DRY RUN (nothing removed)"
fi
echo "═══════════════════════════════════════"
