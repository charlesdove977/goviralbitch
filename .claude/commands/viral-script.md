# /viral:script — HookGenie Hook & Script Generator

You are running the Viral Command script engine. Your job is to generate battle-tested hooks from content angles using 6 proven patterns, score them, and build a persistent hook repository that improves over time. With the `--longform` flag, you also generate full YouTube longform scripts with filming cards. With the `--shortform` flag, you generate platform-specific short-form scripts for Shorts, Reels, TikTok, and LinkedIn.

**Arguments:** $ARGUMENTS

---

## Phase A: Load Context

Read the agent brain to understand the creator's identity and preferences:

```
@data/agent-brain.json
```

**Extract these fields:**
- `identity` — name, brand, niche, tone, differentiator
- `hook_preferences` — pattern weights (boost patterns the creator prefers)
- `monetization` — primary_funnel, cta_strategy
- `platforms.posting[]` — where this creator publishes

**Parse $ARGUMENTS to determine input:**

**If an angle ID is provided (e.g., `/viral:script angle_20260304_001`):**
- Search `data/angles.jsonl` for matching ID
- Load the full angle object (contrast, platform, target_audience, proof_method, funnel_direction)
- If not found: "Angle not found: {id}. Run `/viral:angle` first to develop angles."

**If a topic/text is provided (e.g., `/viral:script "AI agents replacing call centers"`):**
- Search `data/angles.jsonl` for angles matching the topic title
- If match found: use that angle
- If no match: generate hooks directly from the topic text (treat as a freeform angle with user-provided contrast)

**If `--pick` flag:**
1. Scan `data/angles.jsonl` for angles with `status: "draft"` (not yet scripted)
2. Display top 5 by most recent:
   ```
   ═══════════════════════════════════════
   PICK AN ANGLE TO HOOK
   ═══════════════════════════════════════

    #  │ Platform         │ Angle Title                        │ Contrast
   ────┼──────────────────┼────────────────────────────────────┼──────────
    1  │ youtube_longform  │ {title}                            │ {strength}
    2  │ youtube_shorts    │ {title}                            │ {strength}
    3  │ linkedin          │ {title}                            │ {strength}
    4  │ instagram_reels   │ {title}                            │ {strength}
    5  │ tiktok            │ {title}                            │ {strength}

   Enter number to select.
   ═══════════════════════════════════════
   ```
3. Wait for user selection before proceeding

**If `--longform` flag (combine with any input method above):**
- Note this flag for later — after hooks are generated (Phase E), continue to Phase F for full YouTube longform script generation
- Can combine: `/viral:script angle_id --longform`, `/viral:script --pick --longform`
- Only generates scripts for youtube_longform platform

**If `--shortform` flag (combine with any input method above):**
- Note this flag for later — after hooks are generated (Phase E), continue to Phase I for short-form script generation
- Can combine: `/viral:script angle_id --shortform`, `/viral:script --pick --shortform`
- Generates scripts for each shortform platform in `platforms.posting[]` (youtube_shorts, instagram_reels, tiktok, linkedin)

**If `--pdf` flag (combine with --longform or --shortform):**
- Note this flag for later — after script persistence (Phase H or Phase J), continue to Phase K for PDF lead magnet generation
- REQUIRES --longform or --shortform. If --pdf used alone: "The --pdf flag requires --longform or --shortform. Pick a script type first."
- Can combine: `/viral:script --pick --longform --pdf`, `/viral:script angle_id --shortform --pdf`

**If both `--longform` and `--shortform` are present:**
- Display: "Pick one: `--longform` or `--shortform`. They're mutually exclusive."
- Exit — do not proceed

**If no arguments:**
Display usage:
```
Usage: /viral:script [angle_id | topic text | --pick] [--longform | --shortform] [--pdf]

  angle_id     Generate hooks for a specific angle
  "topic"      Generate hooks from topic text
  --pick       Choose from draft angles
  --longform   Full YouTube longform script with filming cards
  --shortform  Short-form scripts for Shorts/Reels/TikTok/LinkedIn
  --pdf        Generate PDF lead magnet from script (use with --longform or --shortform)

Examples:
  /viral:script angle_20260304_001
  /viral:script "AI agents replacing call centers"
  /viral:script --pick
  /viral:script angle_20260304_001 --longform
  /viral:script --pick --shortform
  /viral:script --pick --longform --pdf
  /viral:script angle_id --shortform --pdf
```

**Output of this phase:** An angle object with: title, contrast (common_belief, surprising_truth, contrast_strength), platform, target_audience, proof_method, funnel_direction.

---

## Phase B: HookGenie Engine — Generate Hooks

For each platform in `platforms.posting[]`, generate hooks using **ALL 6 patterns**:

### Pattern 1: Contradiction
- **Formula:** "Everyone says {common_belief}, but {surprising_truth}"
- **Variations:**
  - "The biggest lie about {topic}..."
  - "{common_belief}? That's dead wrong."
  - "I believed {common_belief} for years. Then I discovered {truth}."
- **Best for:** strong/extreme contrasts
- **Platform notes:** Works everywhere, especially YouTube thumbnails/titles and LinkedIn openers

### Pattern 2: Specificity
- **Formula:** "I {specific_result} in {specific_timeframe}"
- **Variations:**
  - "How I {achieved X} with {specific tool/method}"
  - "The exact {process} I used to {result}"
  - "{Specific_number} {things} that {specific_outcome}"
- **Best for:** demo, data, case study proof methods
- **Platform notes:** YouTube longform titles, LinkedIn credibility builders

### Pattern 3: Timeframe Tension
- **Formula:** "In {surprisingly_short_time}, I {impressive_result}"
- **Variations:**
  - "{Timeframe} ago, I {before_state}. Now I {after_state}."
  - "What happens when you {action} for {time}"
  - "I went from {before} to {after} in {time}."
- **Best for:** before/after, transformation stories
- **Platform notes:** Short-form gold (Reels, TikTok), YouTube Shorts

### Pattern 4: POV as Advice
- **Formula:** "Stop {common_practice}. {better_alternative}."
- **Variations:**
  - "If you're still {common_practice}, you're {consequence}"
  - "The {old_way} is dead. Here's what replaced it."
  - "Nobody should be {common_practice} in {current_year}."
- **Best for:** moderate-strong contrasts, educational content
- **Platform notes:** LinkedIn (authoritative tone), YouTube (commanding opener)

### Pattern 5: Vulnerable Confession
- **Formula:** "I was wrong about {common_belief}. {what_changed}."
- **Variations:**
  - "I spent {time/money} on {wrong_approach} before discovering {truth}"
  - "Nobody talks about the {hidden_downside} of {popular_thing}"
  - "Here's what I wish someone told me about {topic}."
- **Best for:** building trust, personal brand, LinkedIn
- **Platform notes:** LinkedIn (authenticity), YouTube longform (personal story angle)

### Pattern 6: Pattern Interrupt
- **Formula:** Unexpected opening that breaks scroll behavior
- **Techniques:** Start mid-action, unusual visual, counter-intuitive statement, sound effect cue
- **Variations:**
  - "{surprising_statement}. Let me explain."
  - "This {object} just {impossible_action}."
  - "[action happening on screen] — and that's why {lesson}"
  - "Don't scroll past this if you {audience_qualifier}."
- **Best for:** short-form (Reels, TikTok, Shorts)
- **Platform notes:** TikTok/Reels (visual-first), YouTube Shorts (pattern break in feed)

### Scoring Each Hook

For every hook generated, compute:

1. **contrast_fit** (0-10): How well does this hook leverage the common_belief → surprising_truth gap?
   - 10: Hook directly states or implies both A and B
   - 7-9: Hook strongly references the contrast
   - 4-6: Hook loosely connects to the contrast
   - 1-3: Weak connection to the angle's contrast

2. **pattern_strength** (0-10): How well does this pattern match the content type?
   - Consider: proof_method, contrast_strength, topic type
   - demo proof + specificity pattern = high score
   - mild contrast + contradiction pattern = lower score

3. **platform_fit** (0-10): How native does this hook feel for the target platform?
   - YouTube longform: conversational, curiosity-driven = high
   - Short-form: punchy, under 10 words, visual = high
   - LinkedIn: professional, statement form = high

4. **composite**: `contrast_fit * 0.4 + pattern_strength * 0.35 + platform_fit * 0.25`

5. **Apply brain hook_preferences:**
   - If `hook_preferences.{pattern}` > 0, boost composite by that amount (capped at 10)
   - This lets the system learn which patterns work for this creator over time
   - If all preferences are 0 (new brain), apply no boost — show all patterns equally

---

## Phase C: Platform Formatting

Apply platform-specific formatting after generating hooks:

**youtube_longform:**
- Hook as spoken opening line (conversational, 10-15 words)
- Suggest a title derived from the hook (curiosity + clarity)
- No visual_cue needed (not applicable)

**youtube_shorts / instagram_reels / tiktok:**
- Hook follows 3-second rule (punchy, under 10 words ideal)
- visual_cue REQUIRED: What to show on screen in first 3 seconds
  - Examples: "Screen recording of AI agent running", "Split screen: before vs after", "Close-up of dashboard metrics"
- Text overlay suggestion if applicable

**linkedin:**
- Hook as text-first bold opener (professional, provocative statement)
- First line must standalone (LinkedIn truncates after ~2 lines)
- No visual_cue (text-only platform)

---

## Phase D: Rank and Display

Rank all hooks by composite score (highest first). Display:

```
═══════════════════════════════════════════════════
HOOKS GENERATED: {Angle Title}
═══════════════════════════════════════════════════

From angle: {angle_id} — "{title}"
Contrast: "{common_belief}" → "{surprising_truth}" [{strength}]
Proof method: {proof_method}

───────────────────────────────────────────────────
📺 YOUTUBE LONGFORM
───────────────────────────────────────────────────

 #  │ Score │ Pattern              │ Hook
────┼───────┼──────────────────────┼──────────────────────────────────
 1  │  8.5  │ contradiction        │ "{hook_text}"
 2  │  8.2  │ specificity          │ "{hook_text}"
 3  │  7.8  │ timeframe_tension    │ "{hook_text}"
 4  │  7.5  │ pattern_interrupt    │ "{hook_text}"
 5  │  7.0  │ pov_as_advice        │ "{hook_text}"
 6  │  6.5  │ vulnerable_confession│ "{hook_text}"

Title suggestion: "{title based on top hook}"

───────────────────────────────────────────────────
⚡ YOUTUBE SHORTS
───────────────────────────────────────────────────

 #  │ Score │ Pattern              │ Hook
────┼───────┼──────────────────────┼──────────────────────────────────
 1  │  8.7  │ pattern_interrupt    │ "{hook_text}"
    │       │                      │ 👁 Visual: {visual_cue}
 2  │  8.3  │ timeframe_tension    │ "{hook_text}"
    │       │                      │ 👁 Visual: {visual_cue}
...

{Repeat for each posting platform}

═══════════════════════════════════════════════════
Keep all hooks? [Y/n] or type numbers to drop (e.g., "drop 3, 5")
═══════════════════════════════════════════════════
```

- Default (Enter or "y"): keep all as "draft"
- "drop N, N": remove those hooks before saving
- User can also type feedback to regenerate specific hooks

---

## Phase E: Persist Hooks

Save approved hooks to `data/hooks.jsonl`:

**ID Generation:**
1. Read existing `data/hooks.jsonl` (if it exists and has content)
2. Find the highest existing ID number for today's date
3. Increment from there: `hook_{YYYYMMDD}_{NNN}`
4. If no existing hooks today, start at 001

**For each hook, write one JSON line:**

```json
{
  "id": "hook_20260304_001",
  "angle_id": "angle_20260304_001",
  "platform": "youtube_longform",
  "pattern": "contradiction",
  "hook_text": "Everyone says you need to hire to scale. I replaced 3 full-time roles with AI agents.",
  "visual_cue": "",
  "score": {
    "contrast_fit": 9.0,
    "pattern_strength": 8.5,
    "platform_fit": 8.0,
    "composite": 8.58
  },
  "cta_pairing": "I break down exactly how to set up these agents in my Skool community — link in the description",
  "status": "draft",
  "performance": {},
  "created_at": "2026-03-04T14:30:00Z",
  "notes": ""
}
```

**CTA Pairing:**
- Load `data/cta-templates.json`
- Match template by: `templates.{platform}.{angle's cta_type}`
- Pick the template most relevant to the hook's promise
- Adapt with angle-specific content
- If no match: use the angle's `funnel_direction.cta_copy` as fallback

**After saving:**
- Update source angle status from `"draft"` to `"scripted"` in `data/angles.jsonl`

**Rules:**
- One JSON object per line (JSONL format)
- Append to existing file (never overwrite)
- Validate structure matches `schemas/hook.schema.json`
- Set `created_at` to current ISO timestamp
- Set `status` to "draft" for all hooks

**Display confirmation:**

**If neither --longform nor --shortform was used:**
```
═══════════════════════════════════════════════════
✓ Saved {N} hooks to data/hooks.jsonl

Top hook: "{best_hook}" [score: X.X]
  Pattern: {pattern} | Platform: {platform}

Angle "{angle_title}" status → scripted

Want scripts? Re-run with a flag:
  /viral:script {angle_id} --longform    (YouTube longform + filming cards)
  /viral:script {angle_id} --shortform   (Shorts/Reels/TikTok/LinkedIn)
═══════════════════════════════════════════════════
```

**If --longform WAS used:**
```
═══════════════════════════════════════════════════
✓ Saved {N} hooks to data/hooks.jsonl

Angle "{angle_title}" status → scripted

Generating longform YouTube script...
═══════════════════════════════════════════════════
```
Then continue to Phase F.

**If --shortform WAS used:**
```
═══════════════════════════════════════════════════
✓ Saved {N} hooks to data/hooks.jsonl

Angle "{angle_title}" status → scripted

Generating shortform scripts...
═══════════════════════════════════════════════════
```
Then continue to Phase I.

---

## Phase F: Longform Script Generation (--longform only)

**Skip this phase if --longform was NOT in $ARGUMENTS.** Only proceed if the user explicitly requested longform script generation.

### Step 1: Select Opening Hook

From the youtube_longform hooks generated in Phase D, select the **top-scoring** hook as the opening:
- Use the #1 ranked youtube_longform hook from Phase D
- Record its hook_id for the script object
- Extract the hook_text as the spoken opening line
- Note the pattern used for visual direction:
  - contradiction → talking head, direct to camera
  - specificity → screen recording showing the result
  - timeframe_tension → split screen or before/after visual
  - pov_as_advice → talking head, authoritative posture
  - vulnerable_confession → talking head, intimate/close framing
  - pattern_interrupt → mid-action or unexpected visual

### Step 2: Generate Retention Hook

Create a mini-hook at the ~30-second mark that re-engages viewers about to click away:
- **Technique options:**
  - **Preview payoff:** "By the end of this video, you'll know exactly how to {specific outcome}"
  - **Open loop:** "But first, there's something most people get wrong about {topic} that I need to address"
  - **Pattern interrupt:** "Now before you think this is just another {topic} video..."
  - **Social proof tease:** "I tested this with {N} clients and the results were {surprising}"
- Pick the technique that best matches the angle's proof_method:
  - demo → preview payoff (tease the demo coming)
  - data → social proof tease (tease the numbers)
  - story/before_after → open loop (tease the transformation)
  - talking_head → pattern interrupt (break expectations)
- Record the retention hook text, timestamp_target ("30s"), and technique

### Step 3: Generate Body Sections (3-5)

Create 3-5 body sections that deliver on the hook's promise. Follow this structure:

**Section flow:**
1. **Context / Problem** — Why this matters, who faces this problem, the common belief
2. **Core Reveal** — The surprising truth (the angle's contrast payoff)
3. **Evidence / Proof** — Demo, data, or story that proves the reveal
4. **Application / How-To** — Practical steps the viewer can take
5. **Result / Transformation** — What happens when they apply this (optional 5th section, use for strong transformations)

**For each section, generate:**
- `title`: Clear section heading
- `talking_points`: 3-5 conversational bullet points (what to say, NOT verbatim teleprompter text)
  - Each point is a natural sentence or phrase a creator would riff on
  - Include specific examples, numbers, or references where relevant
  - Write in the creator's tone (from `identity.tone` in agent brain)
- `proof_element`: What evidence supports this section
  - Match to the angle's `proof_method`:
    - demo → "Show screen recording of {specific_action}"
    - data → "Display metric: {specific_stat}"
    - story → "Tell the story of {specific_event}"
    - before_after → "Show side-by-side: {before} vs {after}"
    - case_study → "Walk through {client/project} example"
  - Be specific — "Show screen recording of AI agent answering a call" not just "Show demo"
- `transition`: How to bridge to the next section
  - Examples: "Now that you see the problem, here's what I discovered..."
  - "The real question is... how do you actually set this up?"
  - "But don't just take my word for it — let me show you the numbers"
- `duration_estimate`: Estimated time ("1-2 min", "2-3 min") — target ~2 min per section

**Section count guidance:**
- 3 sections: Quick, punchy video (6-8 min) — best for how-to content
- 4 sections: Standard depth (8-12 min) — best for most topics
- 5 sections: Deep dive (12-15 min) — best for complex topics with strong proof

Choose section count based on: topic complexity, proof_method depth, and contrast_strength.

### Step 4: Generate Mid-Video CTA

Place a soft, value-driven CTA after the "Core Reveal" section (typically after section 2) when trust is highest:
- Source from `data/cta-templates.json` → `templates.youtube_longform.{cta_type}`
- Use `monetization.primary_funnel` to determine cta_type (community, lead_magnet, website, etc.)
- The mid-CTA should feel natural, not salesy:
  - Good: "If you're finding this useful, I go way deeper on {topic} in my Skool community — link in the description"
  - Bad: "SMASH that subscribe button and join my community NOW"
- Record: text, type, placement ("after section 2")

### Step 5: Generate Closing CTA

Place a direct CTA after the final body section, before the outro:
- Source from `data/cta-templates.json` → `templates.youtube_longform.{cta_type}`
- Use the angle's `funnel_direction.cta_type` if available, else use `monetization.cta_strategy.default_cta`
- The closing CTA should be direct and specific:
  - Reference what was taught in the video
  - Connect to the angle's promise
  - Include the specific URL/action from cta_strategy
- Record: text, type, template_source (which template was used)

### Step 6: Generate Outro

- **Subscribe prompt:** Tie to the video's value — not generic "please subscribe"
  - Template: "If {video_promise} was useful to you, subscribe — I post {cadence} about {niche}"
  - Use `identity.niche` and posting cadence from brain
- **Next video tease:** Suggest a follow-up topic related to the angle
  - Template: "Next {day}, I'm going to show you {related_topic} — so make sure you're subscribed"
  - The tease should create an open loop that makes them want to come back

### Step 7: Calculate Duration

Estimate total video duration:
- Opening hook: 15-30s
- Retention hook: 10-15s
- Body sections: sum of duration_estimates
- Mid CTA: 15-20s
- Closing CTA: 15-20s
- Outro: 20-30s
- Format as range: "{min}-{max} minutes"

### Step 8: Display Script

```
═══════════════════════════════════════════════════════════════
LONGFORM YOUTUBE SCRIPT: {title}
═══════════════════════════════════════════════════════════════

Title: "{suggested_title}"
Duration: {estimated_duration}
Angle: {angle_id} — "{angle_title}"

───────────────────────────────────────────────────────────────
🎬 OPENING HOOK ({pattern})
───────────────────────────────────────────────────────────────

"{opening_hook_text}"

Visual: {visual_direction}

───────────────────────────────────────────────────────────────
⏱ RETENTION HOOK (~{timestamp_target})
───────────────────────────────────────────────────────────────

"{retention_hook_text}"
Technique: {technique}

───────────────────────────────────────────────────────────────
📝 SECTION 1: {section_title} ({duration_estimate})
───────────────────────────────────────────────────────────────

Talking points:
  • {point_1}
  • {point_2}
  • {point_3}

Proof: {proof_element}
Transition: "{transition}"

{Repeat for each section}

───────────────────────────────────────────────────────────────
💡 MID-VIDEO CTA (after {placement})
───────────────────────────────────────────────────────────────

"{mid_cta_text}"
Type: {cta_type}

───────────────────────────────────────────────────────────────
🎯 CLOSING CTA
───────────────────────────────────────────────────────────────

"{closing_cta_text}"
Type: {cta_type} | Source: {template_source}

───────────────────────────────────────────────────────────────
👋 OUTRO
───────────────────────────────────────────────────────────────

Subscribe: "{subscribe_prompt}"
Next video: "{next_video_tease}"

═══════════════════════════════════════════════════════════════
Keep this script? [Y/n] or provide feedback to revise
═══════════════════════════════════════════════════════════════
```

- Default (Enter or "y"): proceed to Phase G (filming cards)
- "n": discard script, return to hooks
- Feedback text: revise specific sections based on user input, then re-display

---

## Phase G: Filming Cards (--longform only)

**Skip this phase if Phase F was skipped.**

Generate one filming card per scene from the script structure. Map script sections to scenes:

| Scene | Source | Shot Type Default |
|-------|--------|-------------------|
| 1 | Opening hook | Inferred from hook pattern (see Phase F Step 1) |
| 2 | Retention hook | talking_head |
| 3-N | Body sections | Inferred from proof_element |
| N+1 | Mid CTA | talking_head |
| N+2 | Closing CTA | talking_head |
| N+3 | Outro | talking_head |

**For each filming card:**
- `scene_number`: Sequential (1, 2, 3...)
- `section_name`: Matches script section (e.g., "Opening Hook", "Context / Problem", "Closing CTA")
- `shot_type`: Inferred from content:
  - talking_head — opinion, advice, CTA, outro
  - screen_recording — demos, walkthroughs, showing tools
  - b_roll — transitions, establishing shots, product shots
  - split_screen — before/after comparisons, side-by-side
  - whiteboard — explaining concepts, diagrams
- `say`: 2-3 key bullet points (NOT verbatim — just the essence of what to communicate)
- `show`: Visual direction for this scene
  - Be specific: "Screen recording of Claude Code terminal running /viral:discover" not "Show tool"
  - Include camera angles for talking head: "Direct to camera, medium shot" or "Close-up, intimate"
- `duration_estimate`: Match from script section
- `notes`: Energy/tone guidance
  - Scene 1 (hook): "High energy, confident, direct to camera"
  - Middle sections: "Steady, educational, authoritative"
  - Proof/demo: "Calm, methodical, let the screen do the talking"
  - CTA: "Warm, genuine, not salesy"
  - Outro: "Relaxed, friendly, looking forward"

**Display filming cards:**

```
═══════════════════════════════════════════════════════════════
🎬 FILMING CARDS: {title}
═══════════════════════════════════════════════════════════════

 #  │ Section              │ Shot Type         │ Duration │ Energy
────┼──────────────────────┼───────────────────┼──────────┼────────
 1  │ Opening Hook         │ talking_head      │ 15-30s   │ High
 2  │ Retention Hook       │ talking_head      │ 10-15s   │ Steady
 3  │ {section_1}          │ {shot_type}       │ {dur}    │ {energy}
 4  │ {section_2}          │ {shot_type}       │ {dur}    │ {energy}
...
 N  │ Outro                │ talking_head      │ 20-30s   │ Relaxed

═══════════════════════════════════════════════════════════════

CARD DETAILS:

───────────────────────────────────────────────────────────────
Card 1: Opening Hook | talking_head | 15-30s
───────────────────────────────────────────────────────────────
SAY:
  • {key_point_1}
  • {key_point_2}
SHOW: {visual_direction}
NOTES: {energy_and_tone}

{Repeat for each card}

═══════════════════════════════════════════════════════════════
Save script + filming cards? [Y/n]
═══════════════════════════════════════════════════════════════
```

- Default (Enter or "y"): proceed to Phase H (persist)
- "n": discard and return to script display

---

## Phase H: Persist Script (--longform only)

**Skip this phase if Phase F was skipped.**

Save the complete script to `data/scripts.jsonl`:

**ID Generation:**
1. Read existing `data/scripts.jsonl` (if it exists and has content)
2. Find the highest existing ID number for today's date
3. Increment from there: `script_{YYYYMMDD}_{NNN}`
4. If no existing scripts today, start at 001

**Build script object matching `schemas/script.schema.json`:**
- `id`: Generated ID
- `angle_id`: Source angle ID
- `hook_ids`: Array of hook IDs used (opening hook + any referenced hooks)
- `platform`: "youtube_longform"
- `title`: Suggested video title from Phase F
- `script_structure`: Complete structure from Phase F (opening_hook, retention_hook, sections, mid_cta, closing_cta, outro)
- `filming_cards`: Array from Phase G
- `estimated_duration`: From Phase F Step 7
- `status`: "draft"
- `performance`: {} (empty — populated by /analyze)
- `created_at`: Current ISO timestamp
- `notes`: ""

**Write one JSON line to `data/scripts.jsonl`** (append, never overwrite).

**Display confirmation:**
```
═══════════════════════════════════════════════════════════════
✓ Script saved: {script_id}

Title: "{title}"
Duration: {estimated_duration}
Sections: {N} body sections + hook + CTAs + outro
Filming cards: {N} scenes ready

Hooks: {N} saved to data/hooks.jsonl
Script: saved to data/scripts.jsonl

Ready to film! Print your filming cards or review with:
  cat data/scripts.jsonl | jq 'select(.id=="{script_id}") | .filming_cards'
═══════════════════════════════════════════════════════════════
```

**If --pdf was used:** After displaying the above confirmation, add:
```
Generating PDF lead magnet...
```
Then continue to Phase K.

---

## Phase I: Shortform Script Generation (--shortform only)

**Skip this phase if --shortform was NOT in $ARGUMENTS.** Only proceed if the user explicitly requested shortform script generation.

### Step 1: Identify Shortform Platforms

From `platforms.posting[]` in agent brain, filter for shortform platforms:
- `youtube_shorts`
- `instagram_reels`
- `tiktok`
- `linkedin`

Only generate scripts for platforms the creator actually posts on. If a platform isn't in `platforms.posting[]`, skip it.

### Step 2: Generate Beat-Based Scripts (YouTube Shorts / Instagram Reels / TikTok)

For each video-based shortform platform in the creator's posting list, generate a beat-based script (5-8 beats, 15-60s total):

| Beat | Time | Purpose | Requirements |
|------|------|---------|-------------|
| 1 | 0-3s | HOOK | Top-scoring hook for this platform from Phase D. visual_cue required. |
| 2 | 3-8s | CONTEXT | One sentence setting up the problem/contrast. Visual: relevant B-roll or text overlay. |
| 3-5 | 8-25s | DELIVER | 2-3 beats delivering the core value. Each beat: action (what to say), visual (what to show), text_overlay (on-screen text reinforcing the point). |
| 6 | 25-30s | PROOF | Quick proof element (show result, stat, or before/after). Visual direction matched to proof_method. |
| 7 | 30-45s | CTA | Platform-appropriate CTA from cta-templates.json. |
| 8 | 45-60s | LOOP (optional) | Callback to hook or visual loop point for replay value. |

**Platform-specific adjustments:**

**YouTube Shorts:**
- Optimize for subscribe CTA ("Subscribe for more {niche} tips")
- No link-in-bio (Shorts don't support it well)
- Text overlays should be bold, centered, large font

**Instagram Reels:**
- Include caption draft with hashtags
- CTA style: "Comment '{keyword}'" or "Link in bio"
- Add `audio_note` with trending audio placeholder: "🎵 Trending audio: [use current viral sound or original audio]"
- Caption should standalone — many viewers read caption without watching

**TikTok:**
- Text-on-screen for EVERY beat (TikTok is text-heavy)
- Add `audio_note` with trending sound placeholder: "🎵 Sound: [trending sound or original]"
- Consider stitch/duet hooks if applicable: "Stitch this with your {topic} results"
- Shorter is better — aim for 15-30s when possible

### Step 3: Generate LinkedIn Post (Text-Based)

For LinkedIn (if in `platforms.posting[]`), generate a text post structure — NOT beat-based:

**LinkedIn Post Structure:**
- **Hook line:** Top-scoring linkedin hook from Phase D (bold, standalone first line)
- **Body:** 3-5 short paragraphs (1-2 sentences each) delivering the angle's contrast
  - Each paragraph should be punchy
  - Use line breaks between paragraphs (LinkedIn rewards white space)
  - Weave in proof element matching proof_method (data, story, experience)
- **CTA:** From cta-templates.json linkedin section, matched to `monetization.cta_strategy`
- **Hashtags:** 3-5 relevant hashtags
- **Character count estimate:** LinkedIn optimal is 1,200-1,500 chars

For LinkedIn persistence, represent paragraphs as "beats" in shortform_structure:
- beat_number: paragraph number
- timestamp: "paragraph {N}" (not time-based)
- action: the paragraph text
- visual: "" (text-only platform)
- text_overlay: "" (not applicable)
- audio_note: "" (not applicable)

### Step 4: Display All Shortform Scripts

```
═══════════════════════════════════════
SHORTFORM SCRIPTS: {Angle Title}
═══════════════════════════════════════

From angle: {angle_id} — "{title}"
Contrast: "{common_belief}" → "{surprising_truth}"

⚡ YOUTUBE SHORTS (estimated: {duration})
─────────────────────────────────────
Beat │ Time  │ Action              │ Visual              │ Text Overlay
─────┼───────┼─────────────────────┼─────────────────────┼──────────────
 1   │ 0-3s  │ {hook}              │ {visual}            │ {overlay}
 2   │ 3-8s  │ {context}           │ {visual}            │ {overlay}
 3   │ 8-15s │ {deliver_1}         │ {visual}            │ {overlay}
 4   │ 15-20s│ {deliver_2}         │ {visual}            │ {overlay}
 5   │ 20-25s│ {proof}             │ {visual}            │ {overlay}
 6   │ 25-30s│ {cta}               │ {visual}            │ {overlay}

📱 INSTAGRAM REELS (estimated: {duration})
─────────────────────────────────────
Beat │ Time  │ Action              │ Visual              │ Text Overlay
─────┼───────┼─────────────────────┼─────────────────────┼──────────────
{same beat table}

Caption: {caption_draft}
Audio: 🎵 {trending_audio_placeholder}
Hashtags: {hashtags}

🎵 TIKTOK (estimated: {duration})
─────────────────────────────────────
Beat │ Time  │ Action              │ Visual              │ Text Overlay
─────┼───────┼─────────────────────┼─────────────────────┼──────────────
{same beat table — text_overlay on every beat}

Sound: 🎵 {trending_sound_placeholder}

💼 LINKEDIN POST (~{char_count} chars)
─────────────────────────────────────
{full post text with line breaks}

Hashtags: {hashtags}
CTA: {cta_text}

═══════════════════════════════════════
Keep all scripts? [Y/n] or type platform name to drop
═══════════════════════════════════════
```

- Default (Enter or "y"): keep all, proceed to Phase J
- "drop {platform}": remove that platform's script before saving
- "n": discard all and return to hooks

---

## Phase J: Persist Shortform Scripts (--shortform only)

**Skip this phase if Phase I was skipped.**

Save each platform's script as a separate JSONL line to `data/scripts.jsonl`:

**ID Generation:**
1. Read existing `data/scripts.jsonl` (if it exists and has content)
2. Find the highest existing ID number for today's date
3. Increment from there: `script_{YYYYMMDD}_{NNN}`
4. If no existing scripts today, start at 001
5. One ID per platform — e.g., 4 platforms = 4 sequential IDs

**For each platform script, build a JSON object:**
- `id`: Generated ID (sequential per platform)
- `angle_id`: Source angle ID
- `hook_ids`: Array containing the hook ID used for this platform's opening
- `platform`: The specific platform (e.g., "youtube_shorts", "instagram_reels", "tiktok", "linkedin")
- `title`: Angle title (used as script reference title)
- `shortform_structure`: The beat-based structure from Phase I
  - `beats`: Array of beat objects
  - `caption`: Post caption (IG/TikTok/LinkedIn) or empty string
  - `hashtags`: Array of hashtag strings
  - `cta`: Object with text, type, placement
  - `estimated_duration`: Duration estimate or character count
- `script_structure`: null (not used for shortform)
- `filming_cards`: null (not used for shortform)
- `estimated_duration`: Duration string (e.g., "30-45s") or character count for LinkedIn
- `status`: "draft"
- `performance`: {} (empty — populated by /analyze)
- `created_at`: Current ISO timestamp
- `notes`: ""

**Write one JSON line per platform** to `data/scripts.jsonl` (append, never overwrite).

**Display confirmation:**
```
═══════════════════════════════════════════════════
✓ Saved {N} shortform scripts to data/scripts.jsonl

Platform        │ Script ID            │ Duration
────────────────┼──────────────────────┼─────────
YouTube Shorts  │ script_20260304_001  │ 30-45s
Instagram Reels │ script_20260304_002  │ 30-45s
TikTok          │ script_20260304_003  │ 15-30s
LinkedIn        │ script_20260304_004  │ ~1,300 chars

Angle "{angle_title}" → {N} shortform scripts ready

Next steps:
  • Film your shorts using the beat tables above
  • Copy your LinkedIn post directly from the output
  • Run /viral:script {angle_id} --longform for a full YouTube script
  • Add --pdf to any script command for a lead magnet PDF
═══════════════════════════════════════════════════
```

**If --pdf was used:** After displaying the above confirmation, add:
```
Generating PDF lead magnet...
```
Then continue to Phase K.

---

## Phase K: Generate PDF Lead Magnet (--pdf only)

**Skip this phase if --pdf was NOT in $ARGUMENTS.** Only proceed if the user explicitly requested PDF generation.

Phase K runs AFTER script persistence (Phase H for longform, Phase J for shortform).

### Step 1: Determine Script ID

- **From longform (Phase H):** Use the single script_id that was just saved
- **From shortform (Phase J):** Multiple scripts were saved (one per platform). Ask user:
  ```
  Multiple shortform scripts saved. Which one for the PDF?

    1. YouTube Shorts  (script_20260304_001)
    2. Instagram Reels  (script_20260304_002)
    3. TikTok           (script_20260304_003)
    4. LinkedIn          (script_20260304_004)
    5. All of the above

  Enter number:
  ```
  - If "5" or "all": generate one PDF per script
  - Otherwise: generate for the selected script only

### Step 2: Generate PDF

Run the PDF generation script for each selected script_id:

```bash
python3 scripts/generate-pdf.py --script-id {script_id}
```

The script reads from `data/scripts.jsonl` and `data/agent-brain.json`, generates a 2-page PDF:
- Page 1: Key takeaways / framework extracted from the script content
- Page 2: CTA page with creator's funnel link

Output: `data/pdfs/{script_id}.pdf`

### Step 3: Display Results

**If generation succeeds:**
```
═══════════════════════════════════════
📄 PDF LEAD MAGNET GENERATED
═══════════════════════════════════════

File: data/pdfs/{script_id}.pdf
Title: "{script_title}"
Pages: 2

Use this PDF as:
  • Lead magnet (gate behind email capture)
  • Skool community bonus content
  • DM deliverable ("Comment 'GUIDE' and I'll send this")
  • LinkedIn article attachment

═══════════════════════════════════════
```

**If generation fails:**
```
⚠ PDF generation failed: {error_message}

Your scripts were saved successfully — PDF is optional.
To retry: python3 scripts/generate-pdf.py --script-id {script_id}
Requires: pip install reportlab>=4.0.0
```

Do NOT fail the entire command if PDF generation fails — scripts are already saved.

---

## Important Rules

- **NEVER modify `data/agent-brain.json`** — script engine is read-only on the brain
- **Full scripts ONLY with --longform or --shortform flag** — without either, command generates hooks only
- **--longform and --shortform are mutually exclusive** — if both provided, error and exit
- **--pdf requires --longform or --shortform** — can't generate PDF from hooks alone
- **PDF generation uses external Python script** — requires reportlab (`pip install reportlab`)
- **Short-form scripts use beats (timed actions), not sections** — beats are precise to the second
- **LinkedIn posts are text-based, not beat-based** — format as a readable post, represent paragraphs as beats only for storage
- **Scripts are conversational talking points, NOT verbatim teleprompter text** — keep it natural, the creator riffs on bullet points
- **Every section must connect back to the angle's core contrast** — the contrast is the thread through the entire video
- **NEVER use browser automation** — all data comes from local files
- **Every hook MUST connect to the angle's contrast** — no generic hooks allowed
- **Show all 6 patterns** — hook_preferences should boost scores, not filter patterns out
- **CTA pairing is advisory** — it suggests a CTA that pairs with the hook's promise, not the full script CTA
- **Save before displaying** — write JSONL first, then show summary (data persistence is priority)
- **Platform-specific formatting is mandatory** — a YouTube longform hook is fundamentally different from a TikTok hook
- **Filming cards are quick reference, not detailed scripts** — 2-3 bullet points per scene, visual direction, energy level
