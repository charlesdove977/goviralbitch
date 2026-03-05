# /viral:update-brain — Brain Evolution Protocol

You are running the Viral Command brain update. Your job is to analyze recent performance data and evolve the **system-managed** sections of the agent brain — learning what works so future content recommendations get smarter.

This command is the feedback loop. It's called after `/viral:analyze` collects new performance data, or manually when the user wants to recalibrate.

---

## ⛔ DO NOT MODIFY — User-Managed Fields

The following fields are **owned by /viral:onboard** and must NEVER be changed by this command:

- `identity` (name, brand, niche, tone, differentiator)
- `icp` (segments, pain_points, goals, platforms_they_use, budget_range)
- `pillars` (content pillar definitions)
- `platforms` (research, posting, api_keys_configured)
- `competitors` (monitored creators)
- `cadence` (weekly_schedule — but `optimal_times` CAN be updated)
- `monetization` (primary_funnel, secondary_funnels, cta_strategy, client_capture)

**If you touch these fields, you are breaking the system.** The only exception is `cadence.optimal_times`, which is data-driven and updated by analysis.

---

## Phase A: Read Current State

Read all data sources to understand what's available:

```
@data/agent-brain.json
@data/insights/insights.json
@data/hooks/hook-repo.jsonl
@schemas/agent-brain.schema.json
```

Also scan for recent analytics entries:
```
@data/analytics/
```

**Check for new data:**

1. Read `metadata.last_analysis` from the brain — this is the last time an update ran
2. Check `data/analytics/` for entries newer than `last_analysis`
3. Check `data/hooks/hook-repo.jsonl` for entries with performance data

**If no new data since last analysis:**
```
No new performance data since last brain update ({last_analysis date}).

Run /viral:analyze first to collect fresh analytics,
or add performance data manually to data/analytics/.
```
Exit without changes.

**If new data exists,** summarize what's available:
```
Brain Update Data Available
════════════════════════════════════════

Last brain update: {last_analysis or "never"}
New content analyzed: {count} pieces
Hook data available: {count} hooks with performance metrics
Platforms with data: {list}

Proceeding to analysis...
════════════════════════════════════════
```

---

## Phase B: Analyze and Propose Updates

Analyze the performance data and propose changes to the three system-managed sections. Show your reasoning for each proposed change.

### B1: Learning Weights

**Current weights** (from `learning_weights`):
- `icp_relevance`: {current value}
- `timeliness`: {current value}
- `content_gap`: {current value}
- `proof_potential`: {current value}

**Analysis method:**
1. For each scored topic in analytics, check which scoring criteria correlated with high performance
2. "High performance" = above-median views, engagement, or retention for that platform
3. Increase weights for criteria that correlate with winners (bump +0.1 to +0.3)
4. Decrease weights for criteria that correlate with underperformers (reduce -0.1 to -0.2)
5. Clamp all weights to range 0.1–5.0

**Minimum data threshold:** If fewer than 5 content pieces have been analyzed total, skip weight adjustments and explain:
```
⏸ Skipping weight adjustments — only {N} pieces analyzed.
Need at least 5 for meaningful signal. Current weights preserved.
```

### B2: Hook Preferences

**Current scores** (from `hook_preferences`):
- `contradiction`: {current}
- `specificity`: {current}
- `timeframe_tension`: {current}
- `pov_as_advice`: {current}
- `vulnerable_confession`: {current}
- `pattern_interrupt`: {current}

**Analysis method:**
1. Read hook-repo.jsonl entries that have `metrics` data
2. For each hook pattern, calculate a composite performance score:
   - Score = (CTR weight × avg_ctr) + (retention weight × avg_retention_30s) + (engagement weight × avg_engagement_rate)
   - Default weights: CTR=0.4, Retention=0.35, Engagement=0.25
3. Normalize scores to 0–100 scale
4. Patterns with no usage data stay at 0

### B3: Performance Patterns

Update the aggregated view of what's working:

- **top_performing_topics**: Extract topics that scored above the median across all analyzed content. Keep top 10 max.
- **top_performing_formats**: Rank content formats (long-form, short-form, LinkedIn post, carousel, etc.) by average performance. Keep top 5.
- **audience_growth_drivers**: Identify content that drove subscriber/follower growth (if data available). Keep top 5.
- **avg_ctr**: Calculate rolling average CTR across all analyzed content. Weight recent content more heavily (last 30 days = 2x weight).
- **avg_retention_30s**: Calculate rolling average 30-second retention. Same recency weighting.
- **total_content_analyzed**: Increment by the number of new pieces analyzed this cycle.

### B4: Optimal Posting Times (optional)

If analytics data includes timestamps and performance correlation:
- Update `cadence.optimal_times` with best-performing posting windows per platform
- Format: `{ "platform_name": "HH:MM EST" }`
- Only update if confidence is medium or high (10+ data points per platform)

---

## Phase C: Apply and Log

### Show Proposed Changes

Present all proposed changes as a clear diff:

```
Proposed Brain Updates
════════════════════════════════════════

Learning Weights:
  icp_relevance:  {old} → {new}  ({reason})
  timeliness:     {old} → {new}  ({reason})
  content_gap:    {old} (no change)
  proof_potential: {old} → {new}  ({reason})

Hook Preferences:
  contradiction:        {old} → {new}
  specificity:          {old} → {new}
  timeframe_tension:    {old} (no data)
  pov_as_advice:        {old} → {new}
  vulnerable_confession: {old} (no data)
  pattern_interrupt:    {old} → {new}

Performance Patterns:
  Top topics: {list}
  Top formats: {list}
  Avg CTR: {old} → {new}
  Avg retention: {old} → {new}
  Total analyzed: {old} → {new}

{Optimal times changes if any}

════════════════════════════════════════
```

### Ask for Approval

Ask: **"Apply these brain updates? (yes/no)"**

- If **no**: Exit without changes. Say: *"No changes applied. Brain preserved as-is."*
- If **yes**: Proceed to write.

### Write Updates

1. **Read the current brain** (fresh read, in case anything changed)
2. **Update ONLY** the three system-managed sections + metadata:
   - `learning_weights` — new values
   - `hook_preferences` — new scores
   - `performance_patterns` — updated aggregates
   - `cadence.optimal_times` — if data supports it
   - `metadata.updated_at` — current ISO timestamp
   - `metadata.last_analysis` — current ISO timestamp
3. **Append to `metadata.evolution_log`:**
   ```json
   {
     "timestamp": "[current ISO timestamp]",
     "reason": "[trigger description, e.g., 'Weekly analysis — 8 new pieces analyzed']",
     "changes": [
       "icp_relevance weight 1.0 → 1.3 (ICP-aligned topics outperformed by 40%)",
       "specificity hook score 0 → 72 (3 uses, avg CTR 8.2%)",
       "avg_ctr updated: 0 → 6.1%",
       "top_performing_topics updated: [list]"
     ]
   }
   ```
4. **Write complete brain** to `data/agent-brain.json`
5. **Verify** the written file is valid JSON with all 11 required top-level keys

### Confirmation

```
Brain Updated
════════════════════════════════════════

Changes applied: {count} fields modified
Evolution log: entry #{N} added
Total content analyzed: {total}

Your discovery scoring and hook recommendations
will now reflect these patterns.

Next: Run /viral:discover to find topics with
updated scoring, or /viral:script to generate
hooks using updated preferences.
════════════════════════════════════════
```

---

## Edge Cases

**First-ever update (no prior analysis):**
- `metadata.last_analysis` will be empty/missing
- Treat ALL analytics data as "new"
- Log reason: "First brain update — baseline established"

**Only hook data, no analytics:**
- Update hook_preferences only
- Skip learning_weights (need topic-level analytics)
- Note in log: "Partial update — hook data only"

**Conflicting signals:**
- If a topic scores high on one platform but low on another, don't change weights
- Note the conflict in the evolution_log changes list
- Example: "icp_relevance: conflicting signal (YouTube high, LinkedIn low) — weight preserved"

**Weight drift guard:**
- If any weight would exceed 3.0, add a note: "⚠️ Weight {name} reaching {value} — consider reviewing with /viral:onboard if ICP has shifted"
- Never auto-clamp below the schema minimum (0.1) or above maximum (5.0)

---

## Arguments

Parse `$ARGUMENTS` for the following flags:

| Flag | Description |
|------|-------------|
| `--insights` | Run insight aggregation mode (populates insights library) |
| (no flags) | Default behavior — brain evolution protocol (Phases A-C above) |

If `--insights` is present, skip Phases A-C above and execute Phase D below instead.

---

## Phase D: Insight Aggregation (`--insights`)

This mode synthesizes patterns across ALL analytics cycles into a persistent insights library. It reads from analytics, hooks, and brain data — writing ONLY to `data/insights/insights.json`.

### Step 1: Load Data Sources

Read all source data:
```
@data/analytics/analytics.jsonl (all analytics entries)
@data/hooks.jsonl (hook repository with performance data)
@data/agent-brain.json (current brain state — pillars, performance_patterns)
@data/insights/insights.json (existing insights to update)
@schemas/insight.schema.json (validation reference)
```

**Minimum data guard:** If fewer than 3 entries in analytics.jsonl:
```
Need more data ([N]/3 analytics entries).
Run /viral:analyze to collect performance data first.
```
Exit without changes.

### Step 2: Aggregate Top Topics

Group analytics entries by `topic_category` (fall back to `content_pillar` if topic_category is null).

For each topic with 2+ entries:
1. Calculate avg_performance as a composite:
   - If views + engagement data: `(normalized_views × 0.4) + (normalized_engagement × 0.3) + (normalized_shares × 0.3)`
   - Normalize each metric: `value / max_value_in_dataset × 100`
   - If some metrics missing, weight the available ones proportionally
2. Determine `best_platform` — the platform with highest avg performance for this topic
3. Determine `trend`:
   - Split entries by date into recent half vs older half
   - Recent avg > older avg × 1.1 → "rising"
   - Recent avg < older avg × 0.9 → "declining"
   - Otherwise → "stable"
4. Record `content_count` — total entries for this topic

Sort by avg_performance descending. Keep top 10.

### Step 3: Aggregate Hook Performance

For each of the 6 hook patterns (contradiction, specificity, timeframe_tension, pov_as_advice, vulnerable_confession, pattern_interrupt):

1. Filter analytics entries where `hook_pattern_used` matches this pattern
2. If fewer than 2 entries: skip this pattern (set all stats to 0/null)
3. Calculate:
   - `times_used`: count of matching entries
   - `avg_ctr`: average of non-null `metrics.ctr` values (round to 1 decimal)
   - `avg_retention_30s`: average of non-null `metrics.retention_30s` values (round to 1 decimal)
   - `avg_engagement`: average of non-null `metrics.engagement_rate` values (round to 1 decimal)
   - `best_platform`: platform with highest avg_ctr for this pattern
   - `trend`: compare recent half vs older half (same method as Step 2)

### Step 4: Aggregate Thumbnail Patterns

Group analytics entries by `thumbnail.style` (skip entries with null thumbnail or null style).

For each style with 2+ samples:
1. `style`: the thumbnail style enum value
2. `text_approach`: most common `thumbnail.text_overlay` value among entries with this style
3. `avg_ctr`: average CTR for entries using this thumbnail style (round to 1 decimal)
4. `sample_count`: number of entries

Sort by avg_ctr descending.

### Step 5: Aggregate Content Format Performance

Group analytics entries by `platform`.

For each platform:
1. `avg_views`: average of `metrics.views` (round to integer)
2. `avg_engagement`: average of `metrics.engagement_rate` (round to 1 decimal)
3. `content_count`: total entries for this platform
4. `trend`: compare recent half vs older half (same method as Step 2)

### Step 6: Optimal Posting Times

Only populate if 5+ analytics entries have `published_at` timestamp data.

For each platform with 5+ entries:
1. Group winners by day of week
2. Find the day with most winners → `best_day`
3. Find approximate time range of winners → `best_time` (HH:MM format)
4. Set `timezone`: "EST" (default from brain)
5. Set `confidence`:
   - <10 entries: "low"
   - 10-25 entries: "medium"
   - 25+ entries: "high"

If insufficient data: leave `optimal_posting_times` as empty object `{}`.

### Step 7: Competitor Insights

Check if recon data exists:
```
@data/recon/ (competitor scraping data)
```

If competitor recon data exists:
1. For each competitor in agent-brain.json competitors list:
   - `competitor`: name from brain
   - `strategy_summary`: brief description of their content approach (from recon analysis)
   - `top_performing_topics`: their most common/successful topic categories (up to 5)
   - `posting_frequency`: estimated posts per week
2. Only populate for competitors with actual recon data

If no recon data: leave `competitor_insights` as empty array `[]`.

### Step 8: Write Insights

Build the complete insights object:
```json
{
  "last_updated": "[current ISO 8601 timestamp]",
  "analysis_count": [previous count + 1],
  "top_topics": [from Step 2],
  "hook_performance": {
    "contradiction": { ... },
    "specificity": { ... },
    ...
  },
  "thumbnail_patterns": [from Step 4],
  "content_format_performance": {
    "youtube_longform": { ... },
    ...
  },
  "optimal_posting_times": {from Step 6},
  "competitor_insights": [from Step 7]
}
```

Write to `data/insights/insights.json`.

### Step 9: Display Summary

```
════════════════════════════════════════
INSIGHTS UPDATED
════════════════════════════════════════

Top Topics: [N] tracked ([top 3 topic names])
Hook Performance: [N]/6 patterns with data
Thumbnail Patterns: [N] styles tracked
Format Performance: [N] platforms tracked
Posting Times: [populated/insufficient data]
Competitor Insights: [N] competitors / none

Analysis runs: [N] total
Last updated: [timestamp]
════════════════════════════════════════

Insights saved to data/insights/insights.json
Other commands can now reference these patterns.
```

---

## Rules for Insight Aggregation

1. **READ-ONLY on source data** — never modify analytics.jsonl, hooks.jsonl, or agent-brain.json from --insights mode
2. **Only writes to** `data/insights/insights.json`
3. **Minimum 2 data points** per category before including in aggregation (prevents noise from single entries)
4. **Minimum 3 total analytics entries** before aggregation runs at all
5. **Trends require 4+ entries** in a category to calculate (need enough data for recent vs older split)
6. **Round all percentages** to 1 decimal place
7. **Normalize metrics** within dataset — don't compare raw numbers across platforms
8. **analysis_count** increments by 1 each time --insights runs successfully
