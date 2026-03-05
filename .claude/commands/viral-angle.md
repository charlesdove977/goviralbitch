# /viral:angle — Contrast Formula Angle Development

You are running the Viral Command angle engine. Your job is to transform discovered topics into platform-specific content angles using the Contrast Formula (common belief → surprising truth), with funneling/CTA direction baked into every angle.

**Arguments:** $ARGUMENTS

---

## Phase A: Load Agent Brain

Read the agent brain to understand the creator's identity, audience, and monetization strategy:

```
@data/agent-brain.json
```

**Extract these fields:**
- `identity` — name, brand, niche, tone, differentiator
- `icp.segments[]` — audience segments (for target_audience)
- `icp.pain_points[]` — audience pains (for pain_addressed)
- `icp.goals[]` — what the audience wants to achieve
- `pillars[]` — content themes + keywords
- `platforms.posting[]` — where this creator publishes (determines which platform angles to generate)
- `monetization` — primary_funnel, secondary_funnels, cta_strategy (default_cta, community_url, website_url)
- `competitors[]` — competitor handles + platforms (for differentiation)

**If the brain is empty or `identity.name` is blank:**
Stop and say: *"Your agent brain isn't set up yet. Run `/viral:onboard` first to tell me who you are and what you create."*

---

## Phase A.5: Competitor Angle Analysis (--competitors mode)

If `$ARGUMENTS` contains `--competitors`:
Run a standalone competitor angle analysis instead of developing angles for a single topic. **After displaying the analysis, exit — this is analysis-only, not angle generation.**

**Step 1: Load competitor recon data**
- Read `data/recon/reports/` for skeleton analysis reports
- Read `data/recon/competitors/{handle}/` for each competitor listed in `agent-brain.json`
- If no recon data found: Stop and say: *"No competitor data found. Run the Recon UI first: `./scripts/run-recon-ui.sh`"*

**Step 2: Extract angle patterns**
For each competitor with data:
- Identify their top 5 content pieces (by engagement metrics if available, else most recent)
- For each: extract the implied contrast (what belief were they flipping?)
- Categorize proof methods used:
  - **demo** — showing it working on screen
  - **talking head** — opinion/commentary only
  - **data** — numbers, metrics, results
  - **before/after** — visual comparison
  - **case study** — real client/project story
- Note platform-specific patterns (hook style, pacing, visual approach)

**Step 3: Identify gaps and opportunities**
- Topics where competitors use weak contrasts (mild) — room for stronger angles
- Proof methods they DON'T use (if nobody demos, demo is your edge)
- Audience segments they ignore (if everyone targets advanced, beginners are underserved)
- Platforms where competitor angles are weakest

**Step 4: Display analysis**

```
═══════════════════════════════════════════════════
COMPETITOR ANGLE ANALYSIS
═══════════════════════════════════════════════════

{Competitor Name} ({platform})
───────────────────────────────────────────────────
Top contrasts:
  1. "{common belief}" → "{their truth}" [{strength}]
  2. "{common belief}" → "{their truth}" [{strength}]
  3. ...
Proof methods: demo (60%), data (30%), opinion (10%)
Strength: {overall assessment}
Gap: {where they're weak}

{Repeat for each competitor...}

═══════════════════════════════════════════════════
OPPORTUNITIES
═══════════════════════════════════════════════════
- Underused proof: {method} — none of your competitors {details}
- Weak contrast area: {topic} — competitors using mild contrasts
- Audience gap: {segment} — no one targeting {segment} with {topic}
- Platform gap: {platform} — competitors weakest here
═══════════════════════════════════════════════════
```

After displaying, exit. **Do NOT proceed to Phase B or beyond.**

---

## Phase B: Identify Topic

Parse `$ARGUMENTS` to determine the topic to develop angles for:

**If a topic title/description is provided (e.g., `/viral:angle AI voice agents replacing call centers`):**
- Use the provided text as the topic
- Check `data/topics/` for any matching topic files to pull in scoring + metadata
- If a match is found in JSONL, use that topic's full data (scoring, source, pillars, competitor_coverage)
- If no match, treat as a freeform topic — you'll develop angles from the description alone

**If no argument or `--pick` flag:**
1. Scan `data/topics/` for the most recent JSONL file
2. Read it and extract topics with `status: "new"` (not yet angled)
3. Display top 5 by `weighted_total`:
   ```
   ═══════════════════════════════════════
   PICK A TOPIC TO DEVELOP
   ═══════════════════════════════════════

    #  │ Score │ Topic                              │ Pillar
   ────┼───────┼────────────────────────────────────┼──────────
    1  │ 35.0  │ {title}                            │ {pillar}
    2  │ 33.0  │ {title}                            │ {pillar}
    3  │ 31.0  │ {title}                            │ {pillar}
    4  │ 29.0  │ {title}                            │ {pillar}
    5  │ 28.0  │ {title}                            │ {pillar}

   Enter number to select, or type a topic title.
   ═══════════════════════════════════════
   ```
4. Wait for user selection before proceeding

**Output of this phase:** A topic object with at minimum: title, description (if available), pillars, and any competitor_coverage data.

---

## Phase C: Generate Angles (Contrast Formula)

For each platform in `platforms.posting[]`, develop an angle using the **Contrast Formula**:

### The Contrast Formula

Every great piece of content flips an expectation. The formula:

> **Common Belief (A)** → **Surprising Truth (B)**

The bigger the gap between A and B, the stronger the angle.

### For each posting platform, generate one angle:

**Step 1: Identify the Common Belief (A)**
- What does the target audience CURRENTLY believe about this topic?
- Must be genuinely held — not a strawman nobody actually thinks
- Draw from the ICP's pain points and goals for context
- Example: "You need to hire more people to scale your agency"

**Step 2: Develop the Surprising Truth (B)**
- What insight, data, demo, or experience contradicts belief A?
- Must be provable — you need to SHOW evidence, not just claim it
- Should connect to the creator's differentiator from the brain
- Example: "I replaced 3 full-time roles with Claude Code agents that cost $0.50/day"

**Step 3: Rate Contrast Strength**
- **mild**: Slight reframe, audience might think "huh, interesting" (low engagement)
- **moderate**: Meaningful flip, challenges an assumption (good engagement)
- **strong**: Directly contradicts common wisdom with proof (high engagement)
- **extreme**: Paradigm shift, makes audience rethink everything (viral potential, but must be credible)

Target: **moderate to strong** for most content. Extreme only when you have undeniable proof.

**Step 4: Set Platform-Specific Guidance**

For **youtube_longform** (if in posting platforms):
- Title suggestion: curiosity-driven + clarity (e.g., "I Replaced My Team with AI Agents — Here's What Happened")
- Proof method: demo, screen recording, case study, before/after
- Retention strategy: promise payoff in intro, deliver proof throughout, callback to A→B contrast at end
- Target length: 8-20 minutes
- Structure hint: Hook (A→B tease) → Context → Proof → Implementation → CTA

For **youtube_shorts** / **instagram_reels** / **tiktok** (if in posting platforms):
- Hook-first: 3-second rule — state the Common Belief OR the Surprising Truth immediately
- Visual emphasis: what to SHOW on screen in first 3 seconds
- 30-60 second target
- Pattern interrupt: start with the most shocking part of the B truth
- Structure hint: Hook → Quick proof → Payoff → CTA (all under 60s)

For **linkedin** (if in posting platforms):
- Text-first framing: open with a bold statement or contrarian take
- Professional tone: adjust language for business audience
- Personal story angle: tie the A→B contrast to a personal experience
- Engagement prompt: end with a question that invites comments
- Structure hint: Bold opener → Story/proof → Insight → Question

**Step 5: Map ICP Connection**
- `target_audience`: Pick the MOST relevant ICP segment for this angle
- `pain_addressed`: Map to the specific ICP pain point this angle speaks to
- `proof_method`: How will you prove the surprising truth? Rank options:
  1. **demo** — Show it working on screen (strongest)
  2. **data** — Numbers, metrics, results
  3. **before/after** — Visual comparison
  4. **case study** — Real client/project story
  5. **expert testimony** — Quote from authority

**Step 6: Set Funnel Direction**
- `cta_type`: Map from `monetization.cta_strategy.default_cta`:
  - "Join the Skool community" → `community`
  - Contains "lead magnet" → `lead_magnet`
  - Contains "newsletter" → `newsletter`
  - Contains "website" → `website`
  - Contains "DM" → `dm`
  - Contains "book" → `booking`
  - Default → `community`
- `cta_copy`: Select and adapt a CTA from the template library:
  1. Load `data/cta-templates.json`
  2. Select template matching: `templates.{platform}.{cta_type}`
  3. Pick the most relevant template for this angle's topic
  4. Adapt the template:
     - Replace `{{variable}}` placeholders with values from agent brain (see `variables` mapping in cta-templates.json)
     - Replace `{{topic}}`, `{{resource}}`, `{{keyword}}` with angle-specific content
     - Customize any `[bracketed]` references to match the angle's topic
  5. If no matching template found in the JSON, generate CTA copy as fallback:
     - Bad: "Join my community"
     - Good: "I break down exactly how to set up these agents in my Skool community — link in bio"
- `monetization_tie`: How does this specific angle connect to revenue?
  - Example: "Demonstrates agency AI capabilities → positions for consulting leads"

---

## Phase D: Competitor Differentiation

For each angle generated, check if competitors have covered this topic:

**Step 1: Check topic data**
- If the source topic has `competitor_coverage[]`, use it directly
- Extract: which competitor, their URL, their performance

**Step 2: Check recon data**
- Look in `data/recon/competitors/` for skeleton analysis reports
- Look in `data/recon/reports/` for aggregated competitor insights
- Search for keywords from the topic title in competitor content

**Step 3: Articulate differentiation**
For each competitor who covered the topic:
- `competitor`: Their name
- `their_angle`: How they approached it (1 sentence)
- `differentiation`: What makes YOUR angle different:
  - Different proof method (demo vs talking head)
  - Different audience segment (beginners vs advanced)
  - Different use case (agency vs solopreneur)
  - More recent/updated take
  - Personal experience vs theoretical

**If no competitor data found:** Set `competitor_angles: []` — this is fine.

---

## Phase E: Display Angles

Present all generated angles in a clean, scannable format:

```
═══════════════════════════════════════════════════
ANGLES DEVELOPED: {Topic Title}
═══════════════════════════════════════════════════

From topic: {title}
Pillar: {pillar name}

───────────────────────────────────────────────────
📺 YOUTUBE LONGFORM
───────────────────────────────────────────────────
Title: {suggested title}
Common belief: "{A}"
Surprising truth: "{B}"
Contrast: {strength}

Target: {audience segment} | Pain: {pain addressed}
Proof: {method} — {brief description of what to show}

CTA: {cta_copy}
     → {cta_type} | Monetization: {monetization_tie}

Competitors:
  - {competitor}: {their_angle} → Your edge: {differentiation}

───────────────────────────────────────────────────
⚡ YOUTUBE SHORTS
───────────────────────────────────────────────────
Hook (first 3s): "{opening line}"
Common belief: "{A}"
Surprising truth: "{B}"
Contrast: {strength}

Visual: {what to show on screen}
Target: {audience segment} | Pain: {pain addressed}

CTA: {cta_copy}

───────────────────────────────────────────────────
💼 LINKEDIN
───────────────────────────────────────────────────
Opening line: "{bold statement}"
Common belief: "{A}"
Surprising truth: "{B}"
Contrast: {strength}

Story angle: {personal connection}
Engagement Q: "{closing question}"
Target: {audience segment}

CTA: {cta_copy}

═══════════════════════════════════════════════════
```

After displaying, ask:

```
Keep all angles? [Y/n]
Or type numbers to pass on specific angles (e.g., "pass 2, 3")
```

- Default (Enter or "y"): keep all as "draft"
- "pass N": mark those angles with `status: "passed"` (won't develop further)
- User can also type feedback to refine a specific angle

---

## Phase F: Persist Angles

Save all kept angles to `data/angles.jsonl`:

**ID Generation:**
1. Read existing `data/angles.jsonl` (if it exists)
2. Find the highest existing ID number for today's date
3. Increment from there: `angle_{YYYYMMDD}_{NNN}`
4. If no existing angles today, start at 001

**For each angle, write one JSON line:**

```json
{
  "id": "angle_20260304_001",
  "topic_id": "topic_20260304_005",
  "platform": "youtube_longform",
  "title": "I Replaced My Team with AI Agents — Here's What Happened",
  "contrast": {
    "common_belief": "You need to hire more people to scale your agency",
    "surprising_truth": "I replaced 3 full-time roles with Claude Code agents that cost $0.50/day",
    "contrast_strength": "strong"
  },
  "target_audience": "agency owners",
  "pain_addressed": "drowning in manual/repetitive work — can't scale without hiring",
  "proof_method": "demo",
  "funnel_direction": {
    "cta_type": "community",
    "cta_copy": "I break down exactly how to set up these agents in my Skool community — link in bio",
    "monetization_tie": "Demonstrates agency AI capabilities → positions for consulting leads"
  },
  "competitor_angles": [],
  "created_at": "2026-03-04T14:30:00Z",
  "status": "draft",
  "notes": ""
}
```

**Rules:**
- One JSON object per line (JSONL format)
- Append to existing file (never overwrite)
- Validate structure matches `schemas/angle.schema.json`
- Set `created_at` to current ISO timestamp
- Set `status` to "draft" for kept angles, "passed" for rejected ones (don't save passed)
- If source topic was from JSONL, set `topic_id` to its ID; otherwise use empty string `""`

**After saving, display:**
```
═══════════════════════════════════════════════════
✓ Saved {N} angles to data/angles.jsonl

  {id}: {platform} — "{title}" [{contrast_strength}]
  {id}: {platform} — "{title}" [{contrast_strength}]
  ...

Next: Run /viral:script "{angle_id}" to generate hooks and scripts.
═══════════════════════════════════════════════════
```

---

## Phase G: Update Topic Status (Optional)

If the source topic came from a JSONL file:
- Update its `status` from `"new"` to `"developing"` in the original topics file
- This prevents the same topic from showing up again in the pick list

**Note:** This is a best-effort update. If the file can't be modified, skip silently.

---

## Important Rules

- **NEVER modify `data/agent-brain.json`** — angle is read-only on the brain
- **NEVER generate hooks or full scripts** — that's `/viral:script` (Phase 4)
- **NEVER use browser automation** — all data comes from local files
- **Common beliefs must be GENUINE** — if you can't find real people who believe A, the contrast is fake
- **Every angle needs a CTA** — content without funneling is a hobby, not a business
- **Save before displaying** — write JSONL first, then show summary (data persistence is priority)
- **Platform-specific, not generic** — a YouTube longform angle is fundamentally different from a TikTok angle
- **Proof > opinion** — prioritize angles where the creator can DEMONSTRATE the surprising truth
