# /viral:discover — Multi-Platform Topic Discovery

You are running the Viral Command discovery engine. Your job is to find trending topics across multiple platforms, score them against the creator's ICP, and save the best ones for content development.

**Arguments:** $ARGUMENTS

---

## Phase A: Load Agent Brain

Read the agent brain to understand who the creator is and what to search for:

```
@data/agent-brain.json
```

**Extract these fields:**
- `pillars[]` — content themes + keywords (drives search queries)
- `icp.segments[]`, `icp.pain_points[]`, `icp.goals[]` — scoring context
- `platforms.research[]` — which platforms to scan
- `learning_weights` — scoring multipliers (icp_relevance, timeliness, content_gap, proof_potential)
- `identity.niche` — overall content niche

**If the brain is empty or `identity.name` is blank:**
Stop and say: *"Your agent brain isn't set up yet. Run `/viral:onboard` first to tell me who you are and what you create."*

---

## Phase A.5: Competitor Recon

Before trend research, check competitor intelligence. This ensures discovery is informed by what's already working in the niche.

**Step 1: Check for recent scrape data**

Look for competitor data in `data/recon/competitors/`. For each competitor in `agent-brain.json`:
- Check if `data/recon/competitors/{handle}/reels.json` exists and was modified within 24 hours
- If stale or missing, note which competitors need scraping

**Step 2: If stale data exists (or no data):**

Display:
```
Competitor Intel: {N} competitors need fresh scrape
Run the Recon UI to scrape: ./scripts/run-recon-ui.sh
Or continue with existing data...
```

If data exists (even stale), continue with what's available. Don't block discovery.

**Step 3: Load competitor content patterns**

For each competitor with scrape data:
- Read `data/recon/competitors/{handle}/reels.json` — top performing content
- Read `data/recon/reports/` — skeleton analysis reports (if available)
- Extract: top hooks, recurring themes, high-engagement formats, content gaps

**Step 4: Generate seed topics from competitors**

Use `recon/bridge.py` logic to convert competitor patterns into seed topics:
- Competitor-sourced topics get `source.platform = "competitor_analysis"`
- These seed topics flow into Phase E scoring alongside trend-discovered topics
- Store seeds temporarily for merging in Phase E

**Output:**
```
Competitor Intel Loaded
═══════════════════════════════
Competitors scanned: {N}
Seed topics from competitors: {N}
Top competitor patterns: {list 3-5 patterns}
═══════════════════════════════
```

---

## Phase B: Determine Search Mode

Parse `$ARGUMENTS` to determine what to discover:

**No arguments (default):**
- Build queries from ALL content pillars
- Use `--quick` mode on last30days

**Specific topic argument (e.g., `/viral:discover AI voice agents`):**
- Use the provided topic as the search query directly
- Still score against ICP

**`--deep` flag present:**
- Use `--deep` mode on last30days instead of `--quick` (more thorough, slower)

---

## Phase C: Build Search Queries

For the default (all pillars) mode, construct search queries:

1. For each content pillar, build 1 search query:
   - Combine: pillar name + top 2-3 keywords + "trends" or "news" or "tools"
   - Example: pillar "AI Automation" with keywords ["n8n", "AI agents", "workflow automation"]
     → Query: "n8n AI agents workflow automation trends"

2. **Add competitor-derived queries** (if competitor data loaded in Phase A.5):
   - If competitors are crushing a topic (>50K views), add it as a search query
   - Example: competitors getting huge views on "AI voice agent" → add "AI voice agent trends" as query

3. **Limit to 3 queries maximum** per invocation (API rate limits)
   - If more than 3 pillars, prioritize the first 3
   - Or combine related pillars into a broader query

3. Display the queries before running:
   ```
   Discovery Queries
   ═══════════════════════════════
   1. "{query 1}" (Pillar: {pillar name})
   2. "{query 2}" (Pillar: {pillar name})
   ═══════════════════════════════
   ```

---

## Phase D: Run Discovery

For each query, execute the bundled last30days research script:

```bash
python3 skills/last30days/scripts/last30days.py "{query}" --emit=compact --quick
```

**Execution rules:**
- Run each query in the **foreground** with a **5-minute timeout**
- If `--deep` mode: replace `--quick` with `--deep`
- If a query fails or times out, log the error and continue with remaining queries
- Collect ALL results from all queries

**After each query completes:**
- Note the sources that returned results (Reddit, X, YouTube, Web)
- Capture key topics, trends, tools, and discussions found

**Important:** Do NOT run more than 3 queries total. If you have more pillars, combine them.

---

## Phase E: Score Topics

From the last30days results, identify **unique topics** worth covering. For each topic, score against the creator's ICP:

### Scoring Criteria (each 1-10):

| Criterion | What to evaluate | Weight key |
|-----------|-----------------|------------|
| **icp_relevance** | Does this directly address the ICP's pain points, goals, or interests? Would their audience care? | `learning_weights.icp_relevance` |
| **timeliness** | Is this trending NOW? New release, breaking news, viral moment? Or old/evergreen? | `learning_weights.timeliness` |
| **content_gap** | Has the topic been covered to death, or is there room for a fresh angle? Check if competitors have already covered it. | `learning_weights.content_gap` |
| **proof_potential** | Can the creator SHOW something on screen? Demo, tutorial, walkthrough? Or just talking-head opinion? | `learning_weights.proof_potential` |

**Scoring Engine Reference:** The programmatic scoring engine at `scoring/engine.py` uses the same criteria. For competitor-sourced topics from Phase A.5, the engine scores them automatically via `recon/bridge.py`. For trend-discovered topics, YOU (Claude) score them using the criteria above — the engine validates consistency.

### Calculate scores:

```
total = icp_relevance + timeliness + content_gap + proof_potential
weighted_total = (icp_relevance × learning_weights.icp_relevance) +
                 (timeliness × learning_weights.timeliness) +
                 (content_gap × learning_weights.content_gap) +
                 (proof_potential × learning_weights.proof_potential)
```

### Competitor validation bonuses:
- Topics matching competitor-validated patterns (from Phase A.5 seed topics) get **+2 content_gap** bonus
- High-engagement competitor topics (>100K views) get **+1 proof_potential** bonus
- Populate `competitor_coverage[]` with any matching competitor handles + their view counts

### Topic selection:
- Score all distinct topics found across all queries AND competitor seed topics from Phase A.5
- A "topic" is a coherent content idea, not just a keyword
- Deduplicate: if the same topic appears from multiple sources, merge and note all sources
- Map each topic to matching content pillars from the agent brain
- Target: **10-20 scored topics** per discovery run
- Minimum score threshold: weighted_total ≥ 20 (out of 40 max at neutral weights)

---

## Phase F: Save to JSONL

Write discovered topics to a date-stamped JSONL file:

**File path:** `data/topics/{YYYY-MM-DD}-topics.jsonl`

**One JSON object per line**, following this schema (from `schemas/topic.schema.json`):

```json
{
  "id": "topic_{YYYYMMDD}_{NNN}",
  "title": "Topic title — clear, specific, content-ready",
  "description": "Why this topic is trending and why it matters to the ICP",
  "source": {
    "platform": "reddit|youtube|x|web|hackernews|github|instagram|tiktok|linkedin|facebook",
    "url": "https://source-url-if-available",
    "author": "Original author if known",
    "engagement_signals": "500 upvotes in 24h, trending on r/n8n"
  },
  "discovered_at": "2026-03-04T12:00:00Z",
  "scoring": {
    "icp_relevance": 8,
    "timeliness": 9,
    "content_gap": 7,
    "proof_potential": 8,
    "total": 32,
    "weighted_total": 32.0
  },
  "pillars": ["AI Automation"],
  "competitor_coverage": [],
  "status": "new",
  "notes": ""
}
```

**Rules:**
- Generate IDs as `topic_{YYYYMMDD}_{NNN}` with zero-padded 3-digit sequence (001, 002, ...)
- Set `status: "new"` for all freshly discovered topics
- Set `discovered_at` to current ISO timestamp
- Include `source.url` when available from last30days output — use empty string `""` if not available
- Set `competitor_coverage` to empty array `[]` (populated by Plan 02-04)
- If the file already exists for today, **append** new topics (don't overwrite)
- Use `notes` to capture any special context about why this topic stood out

---

## Phase F.5: Validate Scores (Optional)

If you want to verify your scoring is consistent with the engine:

```bash
python3 scoring/rescore.py data/topics/{YYYY-MM-DD}-topics.jsonl
```

This re-applies learning weights and prints any significant score differences.

---

## Phase G: Output Summary

After saving, display a ranked summary:

```
═══════════════════════════════════════════════════
DISCOVERY COMPLETE
═══════════════════════════════════════════════════

Sources checked: {list of platforms that returned data}
Total topics found: {N raw} → {N saved} (after dedup + threshold)
Saved to: data/topics/{YYYY-MM-DD}-topics.jsonl

TOP TOPICS BY SCORE
───────────────────────────────────────────────────

 #  │ Score │ Topic                                    │ Pillar
────┼───────┼──────────────────────────────────────────┼──────────────
 1  │ 35.0  │ {topic title}                            │ {pillar}
    │       │ ICP: 9  Time: 9  Gap: 8  Proof: 9       │
    │       │ Why: {one line on why this scored high}   │
────┼───────┼──────────────────────────────────────────┼──────────────
 2  │ 33.0  │ {topic title}                            │ {pillar}
    │       │ ICP: 8  Time: 9  Gap: 8  Proof: 8       │
    │       │ Why: {one line}                           │
────┼───────┼──────────────────────────────────────────┼──────────────
...

RECOMMENDED NEXT STEPS
───────────────────────────────────────────────────

Develop these topics next with /viral:angle:

1. "{top topic}" — {reason it's the best pick}
2. "{second topic}" — {reason}
3. "{third topic}" — {reason}

Run: /viral:angle "{topic title}" to develop angles.

═══════════════════════════════════════════════════
```

**Show the top 10 topics maximum** in the summary. If fewer than 5 topics met the threshold, lower the threshold to 15 and note this in the output.

### Competitor Insights (if competitor data was loaded):

```
COMPETITOR INSIGHTS
───────────────────────────────────────────────────
What competitors are doing well:
- {competitor}: {pattern} ({view count} views)
- {competitor}: {pattern} ({view count} views)

Topics with competitor validation:
- "{topic}" — validated by {competitor} ({views} views)
- "{topic}" — validated by {competitor} ({views} views)
───────────────────────────────────────────────────
```

---

## Important Rules

- **NEVER modify `data/agent-brain.json`** — discover is read-only on the brain
- **NEVER use browser automation** — all discovery is via the bundled last30days CLI script
- **Respect rate limits** — maximum 3 last30days queries per invocation
- **Always score against ICP** — topics without ICP relevance scoring are useless
- **Save before displaying** — write JSONL first, then show summary (data persistence is priority)
- **Idempotent for same day** — running twice on the same day appends (no duplicates by checking existing IDs)

---

## Daily Automation

The discovery pipeline can run unattended via cron:

### Quick Start
```bash
# Test the pipeline manually first:
./scripts/daily-discover.sh --dry-run

# Run it for real:
./scripts/daily-discover.sh
```

The script orchestrates: check stale competitors → scrape new content → score via engine → save topics JSONL.

### macOS launchd (Recommended)

Create `~/Library/LaunchAgents/com.viralcommand.daily-discover.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.viralcommand.daily-discover</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>{PIPELINE_DIR}/scripts/daily-discover.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>6</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>{PIPELINE_DIR}/logs/daily-discover.log</string>
  <key>StandardErrorPath</key>
  <string>{PIPELINE_DIR}/logs/daily-discover-error.log</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.viralcommand.daily-discover.plist
```

Replace `{PIPELINE_DIR}` with your actual content-pipeline path.

### Competitor Tracker

The tracker at `recon/tracker.py` prevents duplicate topic creation:
- Tracks which content has already been processed per competitor
- State persisted in `data/recon/tracker-state.json`
- Auto-cleans entries older than 30 days
- Check stale competitors: `python3 -c "from recon.tracker import get_stale_competitors; print(get_stale_competitors())"`
