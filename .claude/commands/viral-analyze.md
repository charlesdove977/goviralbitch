# /viral:analyze — Multi-Platform Analytics Collection

You are the Analytics Collection Engine for the Viral Command system. You gather performance data for published content across all platforms, store it for pattern analysis, and prepare the feedback loop.

## Arguments

$ARGUMENTS

Parse for:
- `--youtube` — Analyze YouTube content only
- `--instagram` — Analyze Instagram content only
- `--tiktok` — Analyze TikTok content only
- `--linkedin` — Analyze LinkedIn content only
- `--all` — Analyze all platforms (default if no platform flag)
- `--content-id [ID]` — Analyze a specific script by ID
- `--recent [N]` — Analyze last N published pieces (default: 5)
- `--manual` — Non-interactive mode for cron/automation (skips prompts, analyzes all published content, runs full pipeline A-H without pauses)

---

## Phase A: Initialization & Mode Selection

### Step 1: Load Agent Brain

Read `data/agent-brain.json` and extract:
- `platforms.posting` — which platforms the user posts to
- `platforms.api_keys_configured` — which APIs are set up
- `performance_patterns.total_content_analyzed` — how much data we have

### Step 1.5: Detect Manual Mode

If `--manual` flag is present:
- Set `MANUAL_MODE = true`
- Behavior changes:
  - **Phase B**: Skip content selection prompts — automatically select ALL entries in `data/scripts.jsonl` (no user confirmation needed)
  - **Phase C/C.5**: Skip interactive metric input for platforms without API — only collect YouTube API data automatically. Skip thumbnail questions entirely.
  - **Phase D-F**: Run normally (validation, schema, persistence are automated anyway)
  - **Phase G-G.5**: Run winner extraction + pattern identification without confirmation prompts
  - **Phase H**: Run feedback loop without confirmation prompts
- Platform flags still respected: `--manual --youtube` analyzes only YouTube content non-interactively
- If no platform flag with `--manual`: defaults to `--all`
- **Important**: In manual mode, platforms without API access (Instagram, TikTok, LinkedIn) are SKIPPED since they require interactive user input. Only YouTube (with API key configured) collects new data automatically.

### Step 2: Determine Platform Scope

Based on flags:
- If `--youtube`, `--instagram`, `--tiktok`, or `--linkedin`: analyze only that platform
- If `--all` or no platform flag: analyze all platforms in `platforms.posting`
- If `MANUAL_MODE`: filter to only platforms with API access (currently YouTube only). Log skipped platforms: "Skipping [platform] — requires interactive input (not available in manual mode)"
- Filter to only platforms the user actually posts on

### Step 3: Determine API vs Interactive Mode

For each platform in scope, classify:

| Platform | API Available? | Method |
|----------|---------------|--------|
| YouTube (longform/shorts) | Yes (if `youtube_data_v3` in api_keys_configured) | YouTube Data API v3 + user input for Studio metrics |
| Instagram Reels | No | Interactive user input |
| TikTok | No | Interactive user input |
| LinkedIn | No | Interactive user input |

Display:
```
════════════════════════════════════════
/viral:analyze — Performance Analytics
════════════════════════════════════════

Platforms in scope: [list]
API collection: [YouTube ✓ / None]
Interactive input: [list platforms needing manual metrics]

Content to analyze: [--content-id / --recent N / ask user]
════════════════════════════════════════
```

---

## Phase B: Content Discovery

### Step 1: Find Content to Analyze

**If `--content-id [ID]` provided:**
- Look up script in `data/scripts.jsonl` by ID
- If found: use script metadata (title, platform, hook_ids, angle_id)
- If not found: tell user "Script ID not found. Provide details manually."

**If `--recent [N]` provided:**
- Read last N entries from `data/scripts.jsonl` (by created_at)
- Display list with ID, title, platform, created date
- Ask user: "Which of these have you published? (Enter numbers, 'all', or 'none')"

**If neither flag:**
- Ask: "What content would you like to analyze? You can provide:
  1. A script ID from /viral:script (e.g., script_20260304_001)
  2. A video/post URL
  3. A title to search for
  4. Or describe the content"

### Step 2: Build Analysis Queue

For each content piece, collect:
- `content_id` — script ID if from scripts.jsonl, or generate `adhoc_{YYYYMMDD}_{NNN}`
- `platform` — from script metadata or ask user
- `title` — from script or user
- `published_at` — ask user if not known: "When did you publish this? (date or 'today', 'yesterday', 'last week')"
- `source_url` — ask user: "What's the URL? (paste link or 'skip')"
- `hook_pattern_used` — from linked script's hook data if available
- `content_pillar` — from linked angle/topic if traceable

### Step 3: Confirm Queue

Display analysis queue:
```
Content to analyze:
┌────┬──────────────────────────┬──────────────┬─────────────┐
│ #  │ Title                    │ Platform     │ Published   │
├────┼──────────────────────────┼──────────────┼─────────────┤
│ 1  │ [title]                  │ [platform]   │ [date]      │
│ 2  │ [title]                  │ [platform]   │ [date]      │
└────┴──────────────────────────┴──────────────┴─────────────┘

Proceed? (yes / edit / cancel)
```

---

## Phase C: YouTube Data API Collection

**Only runs if:**
- YouTube content is in the analysis queue
- `youtube_data_v3` is in `platforms.api_keys_configured`

### Step 1: Get Video ID

From the source_url, extract video ID:
- `youtube.com/watch?v=VIDEO_ID` → extract VIDEO_ID
- `youtu.be/VIDEO_ID` → extract VIDEO_ID
- `youtube.com/shorts/VIDEO_ID` → extract VIDEO_ID
- If no URL: ask user for video ID or URL

### Step 2: Fetch via YouTube Data API v3

Run this bash command (API key from .env):
```bash
source .env 2>/dev/null
curl -s "https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id=${VIDEO_ID}&key=${YOUTUBE_DATA_API_KEY}"
```

Extract from response:
- `snippet.title` — verify matches expected content
- `snippet.publishedAt` — published timestamp
- `statistics.viewCount` → metrics.views
- `statistics.likeCount` → metrics.likes
- `statistics.commentCount` → metrics.comments
- `snippet.thumbnails` → extract thumbnail URL using fallback chain: `maxres.url` → `high.url` → `medium.url` → `default.url`. Store as `thumbnail_url` for use in Phase C.5 and Phase E.

### Step 3: Collect Studio Metrics (User Input)

The YouTube Data API v3 does NOT provide CTR, retention, or subscriber data. These require the YouTube Analytics API (OAuth), which is out of scope for v0.1.

Ask the user to check YouTube Studio:

```
📊 YouTube Studio metrics for: "[title]"

Open YouTube Studio > Content > Click the video > Analytics

1. CTR (Click-through rate): ___% (found under "Reach" tab)
   → Type the number, or 'skip'

2. Average view duration: ___ (found under "Engagement" tab, e.g., "4:32")
   → Type as seconds (e.g., 272) or "M:SS" format, or 'skip'

3. Average percentage viewed: ___% (found under "Engagement" tab)
   → Type the number, or 'skip'

4. 30-second retention: ___% (found in retention graph, hover at 0:30)
   → Type the number, or 'skip'

5. Subscribers gained: ___ (found under "Reach" tab > "Subscribers")
   → Type the number, or 'skip'
```

Parse responses:
- Accept "skip", "don't know", "n/a", "-" → leave metric null
- Accept percentage with or without % sign
- Accept duration as seconds (272) or M:SS (4:32) → convert to seconds
- Accept fuzzy numbers: "5k" → 5000, "2.3k" → 2300, "~800" → 800

---

## Phase D: Interactive Platform Collection

**Runs for each non-API platform in the analysis queue.**

### Instagram Reels / Posts

```
📊 Instagram metrics for: "[title]"

Open Instagram > Go to the Reel/Post > Tap "View Insights"

1. Views/Plays: ___ (top of insights)
   → Type the number, or 'skip'

2. Likes: ___
   → Type the number, or 'skip'

3. Comments: ___
   → Type the number, or 'skip'

4. Shares: ___
   → Type the number, or 'skip'

5. Saves: ___
   → Type the number, or 'skip'

6. Reach: ___ (under "Accounts reached")
   → Type the number, or 'skip'

7. Completion rate: ___% (if shown, for Reels)
   → Type the number, or 'skip'
```

### TikTok

```
📊 TikTok metrics for: "[title]"

Open TikTok > Profile > Tap the video > Tap "..." > View Analytics

1. Views: ___ (main counter)
   → Type the number, or 'skip'

2. Likes: ___
   → Type the number, or 'skip'

3. Comments: ___
   → Type the number, or 'skip'

4. Shares: ___
   → Type the number, or 'skip'

5. Saves: ___
   → Type the number, or 'skip'

6. Completion rate: ___% (under "Watched full video")
   → Type the number, or 'skip'

7. Average watch time: ___ seconds
   → Type the number, or 'skip'
```

### LinkedIn

```
📊 LinkedIn metrics for: "[title]"

Open LinkedIn > Go to the post > Click "View analytics"

1. Impressions: ___ (total views)
   → Type the number, or 'skip'

2. Reactions: ___ (likes, celebrates, etc.)
   → Type the number, or 'skip'

3. Comments: ___
   → Type the number, or 'skip'

4. Reposts: ___
   → Type the number, or 'skip'

5. Engagement rate: ___% (if shown)
   → Type the number, or 'skip'
```

### Fuzzy Number Parsing Rules

For ALL interactive input, parse these formats:
- `5k` or `5K` → 5000
- `2.3k` → 2300
- `1.5M` or `1.5m` → 1500000
- `~800` or `approx 800` → 800
- `12.5%` or `12.5` (for percentage fields) → 12.5
- `4:32` (duration) → 272 seconds
- `skip`, `n/a`, `don't know`, `-`, `?` → null (omit metric)

### Validation Rules

- Views/impressions: must be >= 0
- Percentages (CTR, retention, completion, engagement): must be 0-100
- Likes/comments/shares/saves: must be >= 0
- Duration: must be > 0 seconds
- If a value seems wrong (e.g., CTR of 500%), ask: "That seems high — CTR is usually 2-15%. Did you mean ___?"

---

## Phase C.5: Thumbnail / Cover Analysis

**Runs for EVERY content piece in the analysis queue, after metrics collection (Phase C or D).**

If user says "skip all thumbnails" at any point, skip this phase for all remaining entries in the batch.

For each content piece, display:

```
🖼️ Thumbnail/Cover analysis for: "[title]"
```

If YouTube and thumbnail URL was auto-fetched in Phase C:
```
Thumbnail auto-fetched: [thumbnail_url]
```

If any other platform:
```
No auto-fetch available — your answers help track what works.
```

Then ask:

```
1. Text overlay on thumbnail/cover? (yes/no)
   → If yes: What text? ___

2. Face visible? (yes/no)
   → If yes: What emotion? (excited, surprised, frustrated, serious, smiling, other)

3. Visual style? (choose one)
   → clean-minimal, bold-text, before-after, screenshot, face-closeup, listicle, dramatic, other

4. How did this thumbnail perform vs your other content? (choose one)
   → below_average, average, above_average, top_performer, skip
```

### Parsing Rules

- Accept "yes"/"no"/"y"/"n" for boolean questions
- Accept "skip" for any field → leave that thumbnail sub-field null
- If user skips ALL 4 questions → set entire thumbnail to null (don't store empty object)
- Emotion mapping: "happy" → "smiling", "shocked" → "surprised", "angry" → "frustrated"
- Style: exact match from predefined list, or store as "other" if user provides custom input
- "skip all thumbnails" or "skip thumbnails" → skip Phase C.5 for all remaining entries

---

## Phase E: Entry Construction

For each content piece analyzed, build an analytics entry per `schemas/analytics-entry.schema.json`:

```json
{
  "id": "analytics_{YYYYMMDD}_{NNN}",
  "content_id": "[script ID or adhoc ID]",
  "platform": "[platform enum]",
  "published_at": "[ISO 8601]",
  "analyzed_at": "[current ISO 8601]",
  "days_since_publish": "[calculated]",
  "metrics": {
    "views": null,
    "impressions": null,
    "ctr": null,
    "retention_30s": null,
    "avg_view_duration": null,
    "avg_view_percentage": null,
    "completion_rate": null,
    "likes": null,
    "comments": null,
    "shares": null,
    "saves": null,
    "subscribers_gained": null,
    "engagement_rate": null
  },
  "thumbnail": {
    "url": "[YouTube auto-fetched URL or null]",
    "text_overlay": "[from Phase C.5 Q1 or null]",
    "emotion": "[from Phase C.5 Q2 or null]",
    "style": "[from Phase C.5 Q3 or null]",
    "ctr_performance": "[from Phase C.5 Q4 or null]"
  },
  "hook_pattern_used": "[from linked script or null]",
  "topic_category": "[from linked angle/topic or null]",
  "content_pillar": "[from linked angle or null]",
  "is_winner": false,
  "winner_reason": null,
  "collection_method": "[youtube_data_api | user_input | mixed]",
  "source_url": "[URL or null]",
  "notes": null
}
```

### Field Population Rules

- `id`: Generate as `analytics_{YYYYMMDD}_{NNN}` where NNN increments based on existing entries for that date
- `content_id`: Use script ID from scripts.jsonl if linked, otherwise `adhoc_{YYYYMMDD}_{NNN}`
- `days_since_publish`: Calculate from published_at to now
- `engagement_rate`: If not provided by user, calculate: `(likes + comments + shares) / views * 100` (use impressions if views unavailable)
- `collection_method`: `youtube_data_api` if all metrics from API, `user_input` if all manual, `mixed` if combination
- `is_winner`: Always `false` in this plan — winner extraction happens in Plan 05-03
- `hook_pattern_used`: Look up from linked script's hook_ids → hooks.jsonl → pattern field
- `content_pillar`: Look up from linked script's angle_id → angles.jsonl → pillar field
- `thumbnail`: Populate from Phase C.5 responses. For YouTube, set `url` from auto-fetched thumbnail. Set `text_overlay`, `emotion`, `style`, `ctr_performance` from user answers. If ALL thumbnail fields are null/skipped, set entire `thumbnail` to null (omit from entry).

### Null Handling

- Only include metrics the user provided or API returned
- Null/skipped metrics are stored as absent (not included in JSON)
- At least ONE metric must be present per entry (otherwise skip the entry)

---

## Phase F: Persistence & Summary

### Step 1: Save Analytics Entries

Append each constructed entry to `data/analytics/analytics.jsonl` (one JSON object per line).

If the file doesn't exist, create it.

### Step 2: Display Summary

```
════════════════════════════════════════
ANALYSIS COMPLETE
════════════════════════════════════════

┌──────────────────────────┬──────────────┬────────┬──────────┬───────┬────────────┐
│ Content                  │ Platform     │ Views  │ Eng Rate │ CTR   │ Method     │
├──────────────────────────┼──────────────┼────────┼──────────┼───────┼────────────┤
│ [title]                  │ [platform]   │ [N]    │ [N%]     │ [N%]  │ [API/user] │
│ [title]                  │ [platform]   │ [N]    │ [N%]     │ [N%]  │ [API/user] │
└──────────────────────────┴──────────────┴────────┴──────────┴───────┴────────────┘

Entries saved: [N] → data/analytics/analytics.jsonl
Total analyzed (all time): [N]

Notable observations:
- [Any standout metrics — highest views, engagement, etc.]
- [Compare to averages if enough data exists]
```

### Step 3: Feedback Loop Readiness Check

Check `performance_patterns.total_content_analyzed` in agent brain:

- If < 5 total entries: "📊 [N]/5 content pieces analyzed. The feedback loop activates after 5+ entries to ensure reliable patterns."
- If >= 5: "✅ Feedback loop ready. Run winner extraction with a future /viral:analyze --extract-winners to identify patterns and update your brain."

### Step 4: Next Steps

```
────────────────────────────────────────
What's next:
- Run /viral:analyze again after publishing more content
- Recommended: analyze weekly (Fridays) for consistent tracking
- Coming soon: automatic winner extraction + brain updates
────────────────────────────────────────
```

---

## Phase G: Winner Extraction

**Only runs if:** Total entries in `data/analytics/analytics.jsonl` (all time) >= 5.

### Step 1: Check Minimum Data

Read ALL entries from `data/analytics/analytics.jsonl` (not just current batch).

Count total entries. If fewer than 5:
```
📊 Winner extraction needs more data ([N]/5 entries).
   Keep analyzing content — winners activate after 5+ entries!
```
Skip Phase G entirely.

### Step 2: Calculate Platform Baselines

Group ALL historical entries by platform. For each platform with 2+ entries, calculate **median** values for key metrics:

| Platform | Primary Metrics for Baseline |
|----------|------------------------------|
| youtube_longform | median CTR, median avg_view_percentage, median engagement_rate |
| youtube_shorts | median views, median completion_rate, median engagement_rate |
| instagram_reels | median views, median completion_rate, median engagement_rate |
| instagram_posts | median views, median engagement_rate |
| tiktok | median views, median completion_rate, median shares |
| linkedin | median impressions, median engagement_rate, median comments |
| facebook | median views, median engagement_rate |

**Median calculation:** Sort values, take middle value (or average of two middle values for even count). Ignore null/missing values when calculating.

Baselines use ALL historical data, not just the current batch.

### Step 3: Apply Winner Criteria

For EACH entry in the **current batch only** (the entries just saved in Phase F), evaluate against platform-specific thresholds:

| Platform | Winner if ANY of these are true |
|----------|--------------------------------|
| youtube_longform | CTR >= median × 1.5 OR avg_view_percentage >= median × 1.3 OR engagement_rate >= median × 2.0 |
| youtube_shorts | views >= median × 2.0 OR completion_rate >= median × 1.3 |
| instagram_reels | views >= median × 2.0 OR completion_rate >= median × 1.3 |
| instagram_posts | views >= median × 2.0 OR engagement_rate >= median × 1.5 |
| tiktok | views >= median × 2.0 OR shares >= median × 3.0 |
| linkedin | engagement_rate >= median × 1.5 OR comments >= median × 2.0 |
| facebook | views >= median × 2.0 OR engagement_rate >= median × 1.5 |

**Rules:**
- If a metric is null/missing on the entry, skip that criterion (don't penalize missing data)
- If the platform has fewer than 2 historical entries (not enough for baseline), skip winner check for that entry
- A piece needs to exceed ANY ONE threshold to be a winner
- Use the FIRST threshold exceeded as the primary reason

### Step 4: Mark Winners

For each entry in the current batch:

**If winner:**
- Set `is_winner: true`
- Set `winner_reason`: human-readable, e.g., "CTR 8.5% exceeds platform median 4.2% by 2.0x" or "Views 12,400 exceeds platform median 3,100 by 4.0x"
- Set `winner_metrics.threshold_used`: the specific threshold, e.g., "ctr >= median * 1.5"
- Set `winner_metrics.percentile`: calculate where this content ranks among ALL same-platform entries for the triggering metric. Formula: `(count of entries with lower value / total entries) * 100`, rounded to nearest integer.

**If not winner:**
- Keep `is_winner: false`, `winner_reason: null`, `winner_metrics` absent

**Persistence:** Read the full `data/analytics/analytics.jsonl` file, find entries matching the current batch by `id`, update their winner fields, write the entire file back.

### Step 5: Winner Summary Display

Display after the Phase F summary:

```
════════════════════════════════════════
WINNER EXTRACTION (baselines from [N] total entries)
════════════════════════════════════════
```

If winners found:
```
Winners: [N] of [batch size]

🏆 [title] — [platform]
   [winner_reason]

🏆 [title] — [platform]
   [winner_reason]

Did not qualify: [list remaining titles]
```

If no winners:
```
No winners this batch. Your content is tracking near baseline.
Keep publishing — performance data improves pattern detection!
```

```
════════════════════════════════════════
```

---

## Phase G.5: Pattern Report

**Only runs if:** At least 2 entries with `is_winner: true` exist across ALL analytics data (current + historical).

If fewer than 2 winners total:
```
📊 Need more winners for pattern analysis (have [N], need 2+).
   Keep publishing — patterns emerge after multiple wins!
```
Skip Phase G.5.

### Step 1: Aggregate Winner Data

Read ALL entries from `data/analytics/analytics.jsonl`. Separate into two groups:
- **Winners:** entries where `is_winner: true`
- **All entries:** every entry (for calculating win rates)

### Step 2: Analyze Patterns

For each dimension below, count occurrences among winners vs all entries. Calculate **win rate** = (winners with this value / total entries with this value) × 100%.

**Dimensions to analyze:**

1. **Hook Patterns** (`hook_pattern_used`): Count each of the 6 hook patterns among winners vs all. Skip entries where `hook_pattern_used` is null.

2. **Thumbnail Styles** (`thumbnail.style`): Count each style enum among winners vs all. Skip entries where thumbnail or style is null.

3. **Thumbnail Emotions** (`thumbnail.emotion`): Count each emotion enum among winners vs all. Skip entries where thumbnail or emotion is null.

4. **Content Pillars** (`content_pillar`): Count each pillar among winners vs all. Skip entries where `content_pillar` is null.

5. **Platform Win Rates** (`platform`): Count winners per platform vs total entries per platform.

**Only include dimensions that have at least 2 data points** (2+ entries with non-null values for that dimension).

### Step 3: Display Pattern Report

```
════════════════════════════════════════
WINNER PATTERNS (across [N] total winners)
════════════════════════════════════════

🎣 Hook Patterns (win rate):
   [pattern]: [X] wins / [Y] total = [Z]% win rate
   [pattern]: [X] wins / [Y] total = [Z]% win rate
```

If hook data insufficient: `   Not enough hook data yet.`

```
🖼️ Thumbnail Styles (win rate):
   [style]: [X] wins / [Y] total = [Z]% win rate
```

If thumbnail style data insufficient: `   Not enough thumbnail style data yet.`

```
😀 Thumbnail Emotions (win rate):
   [emotion]: [X] wins / [Y] total = [Z]% win rate
```

If thumbnail emotion data insufficient: `   Not enough thumbnail emotion data yet.`

```
📂 Content Pillars (win rate):
   [pillar]: [X] wins / [Y] total = [Z]% win rate
```

If pillar data insufficient: `   Not enough pillar data yet.`

```
📊 Platform Win Rates:
   [platform]: [X] wins / [Y] total = [Z]% win rate
```

```
💡 Key Insight: [Identify highest win-rate value across all dimensions with 2+ data points.
   If a combination stands out (e.g., a hook pattern + thumbnail style both top), mention both.
   Example: "contradiction hooks have 75% win rate — your strongest pattern"
   Example: "face-closeup thumbnails + contradiction hooks dominate with 80%+ win rate"]
════════════════════════════════════════
```

**Sort** each category by win rate descending.
**Key Insight** generation: Find the single dimension value with the highest win rate (minimum 2 data points). If two dimensions both have 60%+ win rate, combine them into a combo insight.

---

## Phase H: Feedback Loop

**Runs after Phase G.5.** Auto-updates the hook repository and agent brain based on winner data.

### Step 1: Minimum Data Check

If fewer than 5 total entries in `data/analytics/analytics.jsonl`:
```
🧠 Feedback loop needs more data ([N]/5 entries).
   Brain updates activate after 5+ entries. Keep analyzing!
```
Skip Phase H entirely.

If 5+ entries: proceed.

### Step 2: Update Hook Repository

For each entry in the CURRENT batch that has:
- Non-null `hook_pattern_used`
- `content_id` starting with `script_` (not adhoc content)

Do:
1. Look up the script in `data/scripts.jsonl` by `content_id`
2. From the script, get `hook_ids` array
3. For each hook_id, find matching hook in `data/hooks.jsonl`
4. Apply status update:

| Condition | New Status | Action |
|-----------|-----------|--------|
| Entry `is_winner: true` | `winner` | Set status → "winner", populate `performance` object (ctr, retention_30s, engagement_rate, analyzed_at) |
| Entry `is_winner: false` AND `days_since_publish` >= 7 | `dud` | Set status → "dud", populate `performance` with available metrics |
| Entry `is_winner: false` AND `days_since_publish` < 7 | `used` (if currently draft/approved) | Too early to judge — mark as used but don't declare dud |

5. Write updated hooks back to `data/hooks.jsonl`
6. Display: `"Hooks updated: [N] winners, [N] duds, [N] too early"`

**Rules:**
- Only update hooks that actually exist in hooks.jsonl (skip if not found)
- If a hook already has status "winner", don't downgrade it
- Performance data overwrites previous performance (latest analysis wins)

### Step 3: Update Agent Brain

Read `data/agent-brain.json`. Update these sections:

**A. hook_preferences** (pattern scoring adjustments):

For each of the 6 hook patterns:
1. Count wins: entries in ALL analytics where `is_winner: true` AND `hook_pattern_used` matches
2. Count total uses: ALL analytics entries where `hook_pattern_used` matches
3. Calculate win rate = wins / total
4. Apply adjustment:
   - Win rate >= 50% → add +0.5 to current preference value
   - Win rate > 0% and < 50% → no change
   - Win rate == 0% AND total uses >= 3 → add -0.2
5. Clamp all values to [-2.0, 5.0]
6. Only update patterns with 2+ total uses (skip patterns with 0-1 uses)

**B. learning_weights** (topic/pillar scoring):

For each unique `content_pillar` in ALL analytics:
1. Calculate pillar win rate = pillar winners / pillar total
2. If win rate >= 50% → add +0.1 to `icp_relevance` weight
3. Clamp `icp_relevance` to [0.5, 2.0]
4. Only adjust for pillars with 2+ entries

Note: learning_weights are global in v0.1. Winning pillars boost `icp_relevance` since they validate ICP alignment.

**C. performance_patterns:**

Update with running aggregates from ALL analytics data:
- `total_content_analyzed`: total entry count
- `avg_ctr`: average of all non-null `metrics.ctr` values (round to 1 decimal)
- `avg_retention_30s`: average of all non-null `metrics.retention_30s` values (round to 1 decimal)
- `top_performing_topics`: top 5 `topic_category` values by win rate (minimum 2 entries each), as array of strings
- `top_performing_formats`: top 3 `platform` values by win rate (minimum 2 entries each), as array of strings
- `audience_growth_drivers`: top 3 `topic_category` values by total `subscribers_gained`, as array of strings (empty if no subscriber data)

**D. metadata:**

- Set `metadata.updated_at` to current ISO 8601 timestamp
- Append to `metadata.evolution_log`:
  ```json
  {
    "timestamp": "[current ISO 8601]",
    "reason": "Auto-update via /viral:analyze feedback loop",
    "changes": [
      "hook_preferences: [list changes, e.g., 'contradiction +0.5 (67% win rate)']",
      "performance_patterns: [N] total analyzed, avg CTR [X]%",
      "other notable changes..."
    ]
  }
  ```

Write updated brain back to `data/agent-brain.json`.

### Step 4: Feedback Summary

Display:
```
════════════════════════════════════════
FEEDBACK LOOP
════════════════════════════════════════

🎣 Hook Updates:
   Winners: [N] | Duds: [N] | Too early: [N]

🧠 Brain Updates:
   hook_preferences: [list changes or "no adjustment needed"]
   learning_weights: [changes or "no adjustment needed"]
   performance_patterns: [N] total analyzed, avg CTR [X]%

📊 Running Averages:
   CTR: [X]% | 30s Retention: [X]% | Content Analyzed: [N]

🔄 Evolution logged to agent-brain.json
════════════════════════════════════════
```

If no hooks were linked (all adhoc content or no hook data):
```
🎣 No hooks to update (content not linked to hook repository)
```

If no brain changes were needed (all patterns neutral):
```
🧠 Brain stable — no preference adjustments triggered
   (Changes require 50%+ win rate for boosts, 0% with 3+ uses for penalties)
```

---

## Automation & Cron

### Weekly Cron (Friday 1 AM EST)

The analysis pipeline can run automatically via `scripts/weekly-analyze.sh`:

```bash
# Manual run
./scripts/weekly-analyze.sh

# Dry run (see what would happen without executing)
./scripts/weekly-analyze.sh --dry-run
```

**Schedule:** Friday 06:00 UTC (1:00 AM EST) via macOS launchd.

**Install launchd plist:**
```bash
# Edit the plist to set your content-pipeline path, then:
cp com.viralcommand.weekly-analyze.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.viralcommand.weekly-analyze.plist
```

The cron script invokes `claude -p "/viral:analyze --manual --all"` which runs the full pipeline (Phases A-H) non-interactively. Only platforms with API access (YouTube) collect new data automatically — platforms requiring interactive input are skipped in manual mode.

### Manual Trigger

Run a full analysis cycle manually at any time:
```
/viral:analyze --manual --all
```

Or target a specific platform:
```
/viral:analyze --manual --youtube
```

### Companion Cron

- **Daily discovery:** `scripts/daily-discover.sh` — competitor scraping + topic scoring (daily 6 AM)
- **Weekly analysis:** `scripts/weekly-analyze.sh` — performance analytics + feedback loop (Friday 1 AM EST)

Together these two crons form the automated learning cycle: discover → create → analyze → learn → repeat.

---

## Important Rules

1. **NEVER fabricate metrics** — only use YouTube Data API responses or user-provided data. If you can't verify a number, don't include it.
2. **ALWAYS accept "skip"** for any metric. Partial data is better than no data.
3. **Parse fuzzy numbers** — users will type "5k", "~800", "2.3M". Convert to integers.
4. **YouTube Data API key** comes from `.env` file as `YOUTUBE_DATA_API_KEY`, not from agent-brain.json. The brain's `api_keys_configured` array only tracks WHICH APIs are set up.
5. **Do NOT attempt YouTube Analytics API** — it requires OAuth and is out of scope for v0.1.
6. **Validate ranges** — CTR 0-100%, views >= 0, etc. Ask for confirmation if values seem wrong.
7. **One entry per content piece per analysis run** — don't merge with previous entries. Multiple entries for the same content show performance over time.
8. **is_winner is determined by Phase G** winner extraction using median-based platform-specific thresholds. Minimum 5 total analytics entries required before extraction activates. Multipliers are hardcoded for v0.1.
9. **Phase H updates agent-brain.json** (hook_preferences, learning_weights, performance_patterns, evolution_log) **and hooks.jsonl** (status, performance). These updates require 5+ total analytics entries. Updates are additive — they adjust existing values, never reset them.
10. **Ad-hoc content welcome** — users can analyze content not generated by /viral:script. Generate adhoc_ IDs for these.
11. **Thumbnail questions are optional** — if user says "skip all thumbnails" during a batch, skip Phase C.5 for all remaining entries. Partial thumbnail data is fine (e.g., only style + ctr_performance).
