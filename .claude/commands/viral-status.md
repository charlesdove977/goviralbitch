# /viral:status — Pipeline Dashboard & Content Calendar

You are running the Viral Command status dashboard. Your job is to give the creator a complete, actionable picture of their content pipeline, calendar schedule, and system health — in one glance.

This is "mission control" for the Viral Command system. Default mode shows everything. Flags narrow focus.

---

## Flags

| Flag | What It Does |
|------|-------------|
| (none) | Full dashboard: pipeline + calendar + brain + platforms + next action |
| --calendar | Focused calendar view (next 7 days, slot status) |
| --calendar --generate | Generate calendar slots for next 14 days from cadence config |
| --brain | Focused brain health view (weights, patterns, evolution log) |

---

## Rules

1. **Read-only by default.** Only `--generate` writes data (creates calendar entries).
2. **Never modify agent-brain.json.** This command reads only.
3. **Graceful empty states.** If a data file is empty or missing, show helpful guidance instead of errors.
4. **Staleness thresholds:** discover >3 days = stale, analyze >7 days = stale, brain update >14 days = stale.
5. **Quick action suggests exactly ONE thing** — the most impactful next step.
6. **Calendar generation is idempotent** — running `--generate` twice won't duplicate existing slots.
7. **All dates use local timezone.** Display dates as YYYY-MM-DD.
8. **ASCII formatting.** Use box-drawing characters for visual clarity. No emojis.

---

## Phase A: Read All Data Sources

Read every data source to build the full picture:

```
@data/agent-brain.json
@data/idea-board.jsonl
@data/scripts.jsonl
@data/hooks.jsonl
@data/calendar.jsonl
@data/analytics/analytics.jsonl
@data/insights/ (all files if directory exists)
@schemas/calendar-entry.schema.json
```

**Extract from each source:**

1. **Agent Brain** (`data/agent-brain.json`):
   - `identity.name`, `identity.brand` — for header
   - `cadence.weekly_schedule` — shorts_per_day, shorts_days, longform_per_week, longform_days
   - `cadence.optimal_times` — best posting times (if populated)
   - `platforms.posting` — active posting platforms
   - `platforms.api_keys_configured` — connected APIs
   - `learning_weights` — current scoring multipliers
   - `hook_preferences` — hook pattern scores
   - `performance_patterns` — top topics, formats, growth drivers
   - `metadata.updated_at` — last brain update
   - `metadata.last_analysis` — last analysis run
   - `metadata.last_onboard` — last onboard run
   - `metadata.evolution_log` — recent brain changes

2. **Idea Board** (`data/idea-board.jsonl`):
   - Count entries per status: idea, angled, scripted, published, analyzed
   - Total entries

3. **Scripts** (`data/scripts.jsonl`):
   - Total scripts count
   - Count by platform

4. **Hooks** (`data/hooks.jsonl`):
   - Total hooks in repository
   - Count with performance data (used hooks)

5. **Calendar** (`data/calendar.jsonl`):
   - Entries for next 7 days
   - Count by status: open, assigned, published, skipped
   - Any overdue slots (past date + status "open" or "assigned")

6. **Analytics** (`data/analytics/analytics.jsonl`):
   - Total entries
   - Most recent entry date
   - Winner count (if winner_metrics populated)

7. **Insights** (`data/insights/`):
   - Check if insights.json exists
   - Last updated date

**Staleness check:**
- Calculate days since last discover run (check topics/ directory modification times or analytics dates)
- Calculate days since `metadata.last_analysis`
- Calculate days since `metadata.updated_at` (brain evolution)

---

## Phase B: Full Dashboard (default — no flags)

Display the complete dashboard in this order:

### Step 1: Header

```
================================================================
  VIRAL COMMAND — STATUS DASHBOARD
  {identity.brand} | {identity.name}
================================================================
```

### Step 2: Pipeline Funnel

Count idea board entries by status and display as proportional ASCII bar chart:

```
CONTENT PIPELINE
----------------------------------------------------------------
  idea      [{bar}] {count}
  angled    [{bar}] {count}
  scripted  [{bar}] {count}
  published [{bar}] {count}
  analyzed  [{bar}] {count}
----------------------------------------------------------------
  Total: {total} entries | Conversion: {published/total}%
```

Bar width: proportional to count, max 30 chars. Use `#` for filled, `.` for empty.

If idea board is empty:
```
CONTENT PIPELINE
----------------------------------------------------------------
  No ideas in pipeline yet.
  Start with: /viral:discover to find topics
----------------------------------------------------------------
```

### Step 3: Upcoming Calendar (next 7 days)

```
UPCOMING SCHEDULE (next 7 days)
----------------------------------------------------------------
  {day_name} {date} | {slot_type} {platform} — {status/title}
  {day_name} {date} | {slot_type} {platform} — {status/title}
  {day_name} {date} | {slot_type} {platform} — {status/title}
  ...
----------------------------------------------------------------
```

For each slot:
- If status "open": show "OPEN — needs content"
- If status "assigned": show idea title from linked_idea_id
- If status "published": show "Published" with checkmark
- If status "skipped": show "Skipped" with note if available

If no calendar entries exist:
```
UPCOMING SCHEDULE
----------------------------------------------------------------
  No calendar slots generated yet.
  Run: /viral:status --calendar --generate
----------------------------------------------------------------
```

If overdue slots exist (past date, status "open" or "assigned"):
```
  OVERDUE: {count} slots past due date
  Oldest: {date} — {slot_type} {platform}
```

### Step 4: Brain Health

```
BRAIN HEALTH
----------------------------------------------------------------
  Last update:    {metadata.updated_at} ({days_ago} days ago) {stale_warning}
  Last analysis:  {metadata.last_analysis} ({days_ago} days ago) {stale_warning}
  Content analyzed: {performance_patterns.total_content_analyzed}

  Learning Weights:
    ICP relevance:  {learning_weights.icp_relevance}
    Timeliness:     {learning_weights.timeliness}
    Content gap:    {learning_weights.content_gap}
    Proof potential: {learning_weights.proof_potential}

  Top Hook Pattern: {highest hook_preference pattern} ({score})

  Top Topics: {performance_patterns.top_performing_topics (first 3)}
----------------------------------------------------------------
```

Stale warnings:
- Brain >14 days: "STALE — run /viral:update-brain"
- Analysis >7 days: "STALE — run /viral:analyze"
- If no analysis ever run: "Never run — start with /viral:analyze"

If brain has no performance data yet:
```
BRAIN HEALTH
----------------------------------------------------------------
  Brain initialized but no performance data yet.
  Publish content, then run /viral:analyze to start learning.

  Learning weights: all at defaults (1.0)
  Hook preferences: no data yet
----------------------------------------------------------------
```

### Step 5: Platform Status

```
PLATFORMS
----------------------------------------------------------------
  Posting:    {list from platforms.posting}
  Connected:  {list from platforms.api_keys_configured}
  Missing:    {posting platforms not in api_keys_configured}
----------------------------------------------------------------
```

If no API keys configured:
```
PLATFORMS
----------------------------------------------------------------
  Posting on: {platforms.posting}
  No APIs connected yet.
  Run: /viral:setup to connect platforms
----------------------------------------------------------------
```

### Step 6: Hook Repository

```
HOOKS
----------------------------------------------------------------
  Total: {count} hooks | With performance data: {used_count}
  Repository: data/hooks.jsonl
----------------------------------------------------------------
```

### Step 7: Quick Action

Based on current state, suggest exactly ONE next action. Priority order:

1. No topics discovered and no ideas? → `/viral:discover` — "Find trending topics for your niche"
2. Topics exist but no angles? → `/viral:angle` — "Develop angles from your top topics"
3. Angles exist but no scripts? → `/viral:script` — "Generate hooks and scripts"
4. Scripts exist but nothing published? → `/viral:ideas --advance` — "Mark published content"
5. Published but no analysis (>7 days stale)? → `/viral:analyze` — "Analyze your latest content performance"
6. Analysis done but brain stale (>14 days)? → `/viral:update-brain` — "Update brain with latest insights"
7. No calendar slots? → `/viral:status --calendar --generate` — "Generate your content schedule"
8. Open calendar slots with scripted ideas? → `/viral:ideas --schedule` — "Assign content to open slots"
9. Everything current? → `/viral:discover` — "Stay ahead — find fresh topics"

```
----------------------------------------------------------------
>> NEXT ACTION: {command}
   {description}
----------------------------------------------------------------
```

---

## Phase C: Calendar View (--calendar flag)

When `--calendar` is passed (without `--generate`):

### Step 1: Read calendar + cadence config

Read `data/calendar.jsonl` and `data/agent-brain.json` cadence section.

### Step 2: Display weekly grid

Show a 7-day calendar view starting from today:

```
================================================================
  CONTENT CALENDAR — Week of {start_date}
================================================================

  Cadence: {shorts_per_day} shorts/day ({shorts_days joined}),
           {longform_per_week} longform/week ({longform_days joined})

----------------------------------------------------------------
  MON {date}
    [ ] {slot_type} | {platform} | {status_or_title}
    [ ] {slot_type} | {platform} | {status_or_title}

  TUE {date}
    [ ] {slot_type} | {platform} | {status_or_title}

  WED {date}
    [x] {slot_type} | {platform} | Published: "{title}"
    [ ] {slot_type} | {platform} | OPEN

  ...
----------------------------------------------------------------

  Summary:
    Open slots:     {count}
    Assigned:       {count}
    Published:      {count}
    Skipped:        {count}

  Overdue: {count} (past date, still open/assigned)
----------------------------------------------------------------
```

Checkbox display:
- `[x]` = published
- `[~]` = assigned (has content)
- `[-]` = skipped
- `[ ]` = open (needs content)

If no calendar entries for the week:
```
  No calendar entries for this week.
  Run: /viral:status --calendar --generate
  This will create {expected_slots} slots based on your cadence config.
```

### Step 3: Overdue report

If any slots have dates in the past and status "open" or "assigned":
```
  OVERDUE SLOTS
  ----------------------------------------------------------------
  {date} | {slot_type} | {platform} | {status}
  {date} | {slot_type} | {platform} | {status}

  Options:
  - Publish and run /viral:analyze to track
  - Skip with: manually edit data/calendar.jsonl status to "skipped"
  ----------------------------------------------------------------
```

---

## Phase D: Calendar Generation (--calendar --generate)

When both `--calendar` and `--generate` are passed:

### Step 1: Read cadence config

Read `data/agent-brain.json`:
- `cadence.weekly_schedule.shorts_per_day` (default: 2)
- `cadence.weekly_schedule.shorts_days` (default: ["mon","tue","wed","thu","fri","sat"])
- `cadence.weekly_schedule.longform_per_week` (default: 2)
- `cadence.weekly_schedule.longform_days` (default: ["tue","thu"])

### Step 2: Read existing calendar

Read `data/calendar.jsonl` to get all existing slot dates and IDs.

### Step 3: Generate slots for next 14 days

For each of the next 14 days (starting from today):

1. **Determine day of week** (mon, tue, wed, etc.)

2. **Check shorts:** If day is in `shorts_days`:
   - Create `shorts_per_day` shortform slots
   - ID format: `cal_{YYYYMMDD}_short_{N}` (N = 1, 2, etc.)
   - Platform: distribute across shortform posting platforms from brain config
     - Shortform platforms: youtube_shorts, instagram_reels, tiktok (from platforms.posting)
     - Round-robin assignment across available shortform platforms
   - Status: "open"

3. **Check longform:** If day is in `longform_days`:
   - Create 1 longform slot
   - ID format: `cal_{YYYYMMDD}_long_1`
   - Platform: youtube_longform (default) or first longform platform from brain
   - Status: "open"

4. **Dedup check:** Before creating each entry:
   - Check if ID already exists in calendar.jsonl
   - If exists: skip (idempotent — don't duplicate)
   - If not: create new entry

5. **Entry format** (JSON, one per line in JSONL):
   ```json
   {"id":"cal_20260310_short_1","slot_date":"2026-03-10","slot_type":"shortform","platform":"youtube_shorts","status":"open","created_at":"2026-03-10T00:00:00Z"}
   ```

### Step 4: Write new entries

Append new entries to `data/calendar.jsonl` (one JSON object per line).

### Step 5: Display summary

```
================================================================
  CALENDAR GENERATED
================================================================

  Date range: {start_date} to {end_date}

  New slots created: {count}
  Skipped (already exist): {skip_count}

  Breakdown:
    Shortform: {short_count} slots across {short_days_count} days
    Longform:  {long_count} slots across {long_days_count} days

  Platforms:
    {platform}: {count} slots
    {platform}: {count} slots
    ...

================================================================
  View your calendar: /viral:status --calendar
  Assign content: /viral:ideas --schedule {idea_id} {date}
================================================================
```

---

## Phase E: Brain Health View (--brain flag)

When `--brain` is passed:

### Step 1: Read brain

Read `data/agent-brain.json` fully.

### Step 2: Display detailed brain view

```
================================================================
  BRAIN HEALTH — Detailed View
================================================================

  IDENTITY
  ----------------------------------------------------------------
  Name: {identity.name}
  Brand: {identity.brand}
  Niche: {identity.niche}
  Tone: {identity.tone joined}
  Differentiator: {identity.differentiator}

  LEARNING WEIGHTS (scoring multipliers)
  ----------------------------------------------------------------
  ICP Relevance:    {icp_relevance} {trend_arrow}
  Timeliness:       {timeliness} {trend_arrow}
  Content Gap:      {content_gap} {trend_arrow}
  Proof Potential:  {proof_potential} {trend_arrow}

  (Defaults: 1.0 | Range: 0.1-5.0 | Updated by /viral:analyze)

  HOOK PREFERENCES (pattern performance)
  ----------------------------------------------------------------
  Contradiction:        {score} {bar}
  Specificity:          {score} {bar}
  Timeframe Tension:    {score} {bar}
  POV as Advice:        {score} {bar}
  Vulnerable Confession:{score} {bar}
  Pattern Interrupt:    {score} {bar}

  Best performing: {highest pattern}
  (Scores updated by /viral:analyze feedback loop)

  PERFORMANCE PATTERNS
  ----------------------------------------------------------------
  Content analyzed:     {total_content_analyzed}
  Avg CTR:              {avg_ctr}%
  Avg 30s retention:    {avg_retention_30s}%

  Top topics: {top_performing_topics}
  Top formats: {top_performing_formats}
  Growth drivers: {audience_growth_drivers}

  CADENCE CONFIG
  ----------------------------------------------------------------
  Shorts: {shorts_per_day}/day on {shorts_days}
  Longform: {longform_per_week}/week on {longform_days}
  Optimal times: {optimal_times or "Not yet discovered"}

  EVOLUTION LOG (last 5 entries)
  ----------------------------------------------------------------
  {timestamp} — {reason}
    Changes: {changes joined}
  ...

================================================================
```

Trend arrows for learning weights:
- Value > 1.2: "^" (system learned this matters more)
- Value 0.8-1.2: "=" (neutral/default range)
- Value < 0.8: "v" (system learned this matters less)

If no evolution log entries:
```
  EVOLUTION LOG
  ----------------------------------------------------------------
  No brain updates recorded yet.
  Run /viral:analyze after publishing content to start learning.
```

---

## Error Handling

**Missing data/agent-brain.json:**
```
Agent brain not found. Run /viral:onboard first to set up your profile.
```

**Empty JSONL files (idea-board, scripts, hooks, calendar, analytics):**
- Don't error — show "0 entries" or "No data yet" with guidance
- Empty states are expected for new installations

**Malformed JSONL lines:**
- Skip malformed lines with warning: "Skipped {N} malformed entries in {file}"
- Continue processing valid entries

**Missing schemas directory:**
- Warn but continue — schemas are for validation reference, not required for status display
