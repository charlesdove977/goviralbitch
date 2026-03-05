#!/usr/bin/env bash
# Weekly Analysis Pipeline — Performance analytics + feedback loop
# Usage: ./scripts/weekly-analyze.sh [--dry-run]
# Cron:  0 6 * * 5 cd /path/to/content-pipeline && ./scripts/weekly-analyze.sh >> logs/weekly-analyze.log 2>&1
#        (Friday 06:00 UTC = Friday 1:00 AM EST)
#
# ─────────────────────────────────────────────────────────
# launchd plist (save as ~/Library/LaunchAgents/com.viralcommand.weekly-analyze.plist):
#
# <?xml version="1.0" encoding="UTF-8"?>
# <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
# <plist version="1.0">
# <dict>
#     <key>Label</key>
#     <string>com.viralcommand.weekly-analyze</string>
#     <key>Program</key>
#     <string>/path/to/content-pipeline/scripts/weekly-analyze.sh</string>
#     <key>StartCalendarInterval</key>
#     <dict>
#         <key>Weekday</key>
#         <integer>5</integer>
#         <key>Hour</key>
#         <integer>1</integer>
#         <key>Minute</key>
#         <integer>0</integer>
#     </dict>
#     <key>StandardOutPath</key>
#     <string>/path/to/content-pipeline/logs/weekly-analyze.log</string>
#     <key>StandardErrorPath</key>
#     <string>/path/to/content-pipeline/logs/weekly-analyze.log</string>
#     <key>WorkingDirectory</key>
#     <string>/path/to/content-pipeline</string>
# </dict>
# </plist>
#
# Install:
#   cp com.viralcommand.weekly-analyze.plist ~/Library/LaunchAgents/
#   launchctl load ~/Library/LaunchAgents/com.viralcommand.weekly-analyze.plist
#
# Uninstall:
#   launchctl unload ~/Library/LaunchAgents/com.viralcommand.weekly-analyze.plist
#   rm ~/Library/LaunchAgents/com.viralcommand.weekly-analyze.plist
# ─────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"

LOG_DIR="$PIPELINE_DIR/logs"
mkdir -p "$LOG_DIR"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

TODAY=$(date +%Y-%m-%d)
START_TIME=$(date +%s)

echo "═══════════════════════════════════════"
echo "  VIRAL COMMAND — Weekly Analysis"
echo "  $TODAY $(date +%H:%M:%S)"
echo "═══════════════════════════════════════"
echo ""

if $DRY_RUN; then
    echo "[DRY RUN] No analysis will be executed."
    echo ""
fi

# ──────────────────────────────────────
# Step 1: Pre-flight checks
# ──────────────────────────────────────
echo "Step 1: Pre-flight checks..."

BRAIN_FILE="$PIPELINE_DIR/data/agent-brain.json"
SCRIPTS_FILE="$PIPELINE_DIR/data/scripts.jsonl"
ANALYTICS_DIR="$PIPELINE_DIR/data/analytics"

if [[ ! -f "$BRAIN_FILE" ]]; then
    echo "  ERROR: agent-brain.json not found at $BRAIN_FILE"
    echo "  Run /viral:onboard first to initialize the agent brain."
    exit 1
fi
echo "  ✓ agent-brain.json found"

if [[ ! -f "$SCRIPTS_FILE" ]]; then
    echo "  WARNING: scripts.jsonl not found — no published scripts to analyze."
    echo "  Exiting (nothing to do)."
    exit 0
fi
echo "  ✓ scripts.jsonl found"

mkdir -p "$ANALYTICS_DIR"
echo "  ✓ analytics directory ready"
echo ""

# ──────────────────────────────────────
# Step 2: Count published content
# ──────────────────────────────────────
echo "Step 2: Counting published content..."

SCRIPT_COUNT=$(wc -l < "$SCRIPTS_FILE" | tr -d ' ')
echo "  Total scripts: $SCRIPT_COUNT"

ANALYTICS_FILE="$ANALYTICS_DIR/analytics.jsonl"
if [[ -f "$ANALYTICS_FILE" ]]; then
    ANALYTICS_COUNT=$(wc -l < "$ANALYTICS_FILE" | tr -d ' ')
    echo "  Existing analytics entries: $ANALYTICS_COUNT"
else
    ANALYTICS_COUNT=0
    echo "  Existing analytics entries: 0 (first run)"
fi
echo ""

# ──────────────────────────────────────
# Step 3: Run analysis
# ──────────────────────────────────────
echo "Step 3: Running /viral:analyze --manual --all..."

if $DRY_RUN; then
    echo "  [DRY RUN] Would execute:"
    echo "    cd $PIPELINE_DIR && claude -p '/viral:analyze --manual --all'"
    echo ""
else
    echo "  Invoking Claude Code CLI..."
    cd "$PIPELINE_DIR"
    claude -p "/viral:analyze --manual --all" 2>&1 | tee -a "$LOG_DIR/weekly-analyze-${TODAY}.log"
    ANALYZE_EXIT=$?

    if [[ $ANALYZE_EXIT -ne 0 ]]; then
        echo "  WARNING: /viral:analyze exited with code $ANALYZE_EXIT"
    else
        echo "  ✓ Analysis complete"
    fi
    echo ""
fi

# ──────────────────────────────────────
# Step 4: Summary
# ──────────────────────────────────────
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "═══════════════════════════════════════"
echo "  Weekly Analysis Complete"
echo "═══════════════════════════════════════"
echo "  Date:             $TODAY"
echo "  Duration:         ${DURATION}s"
echo "  Scripts in repo:  $SCRIPT_COUNT"
echo "  Prior analytics:  $ANALYTICS_COUNT"
if $DRY_RUN; then
    echo "  Mode:             DRY RUN (nothing executed)"
fi
echo "  Log:              $LOG_DIR/weekly-analyze-${TODAY}.log"
echo "═══════════════════════════════════════"
