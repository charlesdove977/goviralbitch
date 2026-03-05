#!/usr/bin/env bash
# Daily Discovery Pipeline — Competitor scrape + score + save
# Usage: ./scripts/daily-discover.sh [--dry-run]
# Cron:  0 6 * * * cd /path/to/content-pipeline && ./scripts/daily-discover.sh >> logs/daily.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"
export PYTHONPATH="$PIPELINE_DIR"

LOG_DIR="$PIPELINE_DIR/logs"
mkdir -p "$LOG_DIR"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

TODAY=$(date +%Y-%m-%d)
START_TIME=$(date +%s)

echo "═══════════════════════════════════════"
echo "  VIRAL COMMAND — Daily Discovery"
echo "  $TODAY $(date +%H:%M:%S)"
echo "═══════════════════════════════════════"
echo ""

if $DRY_RUN; then
    echo "[DRY RUN] No scraping or saving will occur."
    echo ""
fi

# Ensure data directories exist
mkdir -p "$PIPELINE_DIR/data/recon/competitors"
mkdir -p "$PIPELINE_DIR/data/recon/reports"
mkdir -p "$PIPELINE_DIR/data/topics"

# ──────────────────────────────────────
# Step 1: Check stale competitors
# ──────────────────────────────────────
echo "Step 1: Checking competitor freshness..."

STALE=$(python3 -c "
from recon.tracker import get_stale_competitors
stale = get_stale_competitors()
print('\n'.join(stale) if stale else '')
")

if [[ -z "$STALE" ]]; then
    echo "  All competitors fresh (scraped within 24h)."
    echo ""
    STALE_COUNT=0
else
    STALE_COUNT=$(echo "$STALE" | wc -l | tr -d ' ')
    echo "  $STALE_COUNT competitor(s) need scraping:"
    echo "$STALE" | while read -r handle; do
        echo "    - @$handle"
    done
    echo ""
fi

# ──────────────────────────────────────
# Step 2: Scrape stale competitors
# ──────────────────────────────────────
NEW_CONTENT_COUNT=0

if [[ $STALE_COUNT -gt 0 ]]; then
    echo "Step 2: Scraping stale competitors..."

    if $DRY_RUN; then
        echo "  [DRY RUN] Would scrape: $STALE"
        echo ""
    else
        # Run scraping + tracking + bridge in a single Python script
        # to avoid multiple process spawns and keep state consistent
        NEW_CONTENT_COUNT=$(python3 << 'PYTHON_EOF'
import json
import sys
from datetime import datetime
from pathlib import Path

from recon.config import load_competitors, load_config
from recon.tracker import load_state, save_state, filter_new_content, get_stale_competitors

stale_handles = get_stale_competitors()
if not stale_handles:
    print(0)
    sys.exit(0)

config = load_config()
competitors = load_competitors()
state = load_state()
total_new = 0

for comp in competitors:
    handle = comp.handle.lstrip("@").lower()
    if handle not in stale_handles:
        continue

    platform = comp.platform.lower()
    content_items = []

    try:
        if platform == "youtube":
            from recon.scraper.youtube import scrape_channel
            content_items = scrape_channel(comp.handle, max_results=10)
        elif platform == "instagram":
            from recon.scraper.instagram import scrape_profile
            content_items = scrape_profile(
                handle,
                ig_username=config.ig_username,
                ig_password=config.ig_password,
                max_posts=10,
            )
    except Exception as e:
        print(f"  Warning: Failed to scrape @{handle}: {e}", file=sys.stderr)
        continue

    if not content_items:
        continue

    # Filter to new-only via tracker
    new_items = filter_new_content(handle, content_items, state)
    total_new += len(new_items)

    if new_items:
        print(f"  @{handle}: {len(new_items)} new items", file=sys.stderr)

# Save tracker state
save_state(state)
print(total_new)
PYTHON_EOF
        )
        echo "  Found $NEW_CONTENT_COUNT new content item(s)."
        echo ""
    fi
else
    echo "Step 2: Skipped (no stale competitors)."
    echo ""
fi

# ──────────────────────────────────────
# Step 3: Process new content through bridge
# ──────────────────────────────────────
TOPIC_COUNT=0

if [[ $NEW_CONTENT_COUNT -gt 0 ]] && ! $DRY_RUN; then
    echo "Step 3: Processing new content through bridge..."

    TOPIC_COUNT=$(python3 << 'PYTHON_EOF'
import sys
from recon.bridge import load_latest_skeletons, generate_topics_from_skeletons, save_topics_jsonl

skeletons = load_latest_skeletons()
if not skeletons:
    print(0)
    sys.exit(0)

topics = generate_topics_from_skeletons(skeletons)
if topics:
    output = save_topics_jsonl(topics)
    print(len(topics))
else:
    print(0)
PYTHON_EOF
    )
    echo "  Generated $TOPIC_COUNT topic(s)."
    echo ""
else
    echo "Step 3: Skipped (no new content to process)."
    echo ""
fi

# ──────────────────────────────────────
# Step 4: Summary
# ──────────────────────────────────────
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "═══════════════════════════════════════"
echo "  Daily Discovery Complete"
echo "═══════════════════════════════════════"
echo "  Date:        $TODAY"
echo "  Duration:    ${DURATION}s"
echo "  Stale:       $STALE_COUNT competitor(s)"
echo "  New content: $NEW_CONTENT_COUNT item(s)"
echo "  New topics:  $TOPIC_COUNT"
if [[ $TOPIC_COUNT -gt 0 ]]; then
    echo "  File:        data/topics/${TODAY}-topics.jsonl"
fi
if $DRY_RUN; then
    echo "  Mode:        DRY RUN (nothing saved)"
fi
echo "═══════════════════════════════════════"
