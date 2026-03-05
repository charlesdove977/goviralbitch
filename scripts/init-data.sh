#!/usr/bin/env bash
set -euo pipefail

# Viral Command — Data Initialization Script
# Creates all data files with clean defaults for a fresh repo clone.
# Safe to re-run: existing files are skipped unless --force is used.
#
# Usage:
#   bash scripts/init-data.sh          # Create missing files only
#   bash scripts/init-data.sh --force  # Overwrite all files to defaults

# ── Config ──────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

FORCE=false
CREATED=0
SKIPPED=0

if [[ "${1:-}" == "--force" ]]; then
  FORCE=true
  echo "⚠️  --force mode: all files will be overwritten to defaults."
  read -r -p "Are you sure? (y/N) " confirm
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 0
  fi
fi

# ── Helpers ─────────────────────────────────────────────────────────

create_file() {
  local filepath="$1"
  local content="$2"
  local relpath="${filepath#"$PROJECT_ROOT"/}"

  if [[ -f "$filepath" ]] && [[ "$FORCE" == false ]]; then
    echo "  SKIP: $relpath (already exists)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi

  mkdir -p "$(dirname "$filepath")"
  printf '%s' "$content" > "$filepath"
  echo "  CREATE: $relpath"
  CREATED=$((CREATED + 1))
}

create_empty_file() {
  local filepath="$1"
  local relpath="${filepath#"$PROJECT_ROOT"/}"

  if [[ -f "$filepath" ]] && [[ "$FORCE" == false ]]; then
    echo "  SKIP: $relpath (already exists)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi

  mkdir -p "$(dirname "$filepath")"
  : > "$filepath"
  echo "  CREATE: $relpath"
  CREATED=$((CREATED + 1))
}

create_gitkeep() {
  local dirpath="$1"
  local filepath="$dirpath/.gitkeep"
  local relpath="${filepath#"$PROJECT_ROOT"/}"

  mkdir -p "$dirpath"
  if [[ -f "$filepath" ]] && [[ "$FORCE" == false ]]; then
    echo "  SKIP: $relpath (already exists)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi

  : > "$filepath"
  echo "  CREATE: $relpath"
  CREATED=$((CREATED + 1))
}

# ── Directory Structure ─────────────────────────────────────────────

echo ""
echo "Viral Command — Initializing data files..."
echo "Project root: $PROJECT_ROOT"
echo ""

echo "Directories:"
for dir in \
  "$PROJECT_ROOT/data" \
  "$PROJECT_ROOT/data/hooks" \
  "$PROJECT_ROOT/data/topics" \
  "$PROJECT_ROOT/data/angles" \
  "$PROJECT_ROOT/data/scripts" \
  "$PROJECT_ROOT/data/analytics" \
  "$PROJECT_ROOT/data/insights" \
  "$PROJECT_ROOT/scripts" \
  "$PROJECT_ROOT/.claude/commands" \
  "$PROJECT_ROOT/skills/last30days"; do
  if [[ ! -d "$dir" ]]; then
    mkdir -p "$dir"
    echo "  CREATE: ${dir#"$PROJECT_ROOT"/}/"
  fi
done
echo ""

# ── Seed Agent Brain ────────────────────────────────────────────────

echo "Data files:"

SEED_BRAIN='{
  "identity": {
    "name": "",
    "brand": "",
    "niche": "",
    "tone": [],
    "differentiator": ""
  },
  "icp": {
    "segments": [],
    "pain_points": [],
    "goals": [],
    "platforms_they_use": [],
    "budget_range": ""
  },
  "pillars": [],
  "platforms": {
    "research": [],
    "posting": [],
    "api_keys_configured": []
  },
  "competitors": [],
  "cadence": {
    "weekly_schedule": {
      "shorts_per_day": 2,
      "shorts_days": ["mon", "tue", "wed", "thu", "fri", "sat"],
      "longform_per_week": 2,
      "longform_days": ["tue", "thu"]
    },
    "optimal_times": {}
  },
  "monetization": {
    "primary_funnel": "",
    "secondary_funnels": [],
    "cta_strategy": {
      "default_cta": "",
      "lead_magnet_url": "",
      "community_url": "",
      "newsletter_url": "",
      "website_url": ""
    },
    "client_capture": ""
  },
  "learning_weights": {
    "icp_relevance": 1.0,
    "timeliness": 1.0,
    "content_gap": 1.0,
    "proof_potential": 1.0
  },
  "hook_preferences": {
    "contradiction": 0,
    "specificity": 0,
    "timeframe_tension": 0,
    "pov_as_advice": 0,
    "vulnerable_confession": 0,
    "pattern_interrupt": 0
  },
  "performance_patterns": {
    "top_performing_topics": [],
    "top_performing_formats": [],
    "audience_growth_drivers": [],
    "avg_ctr": 0,
    "avg_retention_30s": 0,
    "total_content_analyzed": 0
  },
  "metadata": {
    "version": "0.1.0",
    "created_at": "",
    "updated_at": "",
    "last_onboard": "",
    "evolution_log": []
  }
}'

create_file "$PROJECT_ROOT/data/agent-brain.json" "$SEED_BRAIN"

# ── Empty Data Files ────────────────────────────────────────────────

SEED_INSIGHTS='{"last_updated":"","analysis_count":0}'

create_file "$PROJECT_ROOT/data/insights/insights.json" "$SEED_INSIGHTS"
create_empty_file "$PROJECT_ROOT/data/hooks/hook-repo.jsonl"
create_empty_file "$PROJECT_ROOT/data/idea-board.jsonl"

# ── Gitkeep Placeholders ───────────────────────────────────────────

create_gitkeep "$PROJECT_ROOT/data/topics"
create_gitkeep "$PROJECT_ROOT/data/angles"
create_gitkeep "$PROJECT_ROOT/data/scripts"
create_gitkeep "$PROJECT_ROOT/data/analytics"

echo ""
echo "════════════════════════════════════════"
echo "Done: $CREATED created, $SKIPPED skipped"
echo "════════════════════════════════════════"

if [[ "$CREATED" -gt 0 ]]; then
  echo ""
  echo "Next: Run /viral:onboard to populate your agent brain."
fi
