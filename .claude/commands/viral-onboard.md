# /viral:onboard — Agent Brain Setup

You are running the Viral Command onboarding flow. Your job is to have a conversational coaching session with the user to populate their **agent brain** — the central memory that every module in this system reads from.

---

## Phase A: Check Existing Brain

First, read the current agent brain:

```
@data/agent-brain.json
```

**Check if the brain is already populated:**
- If `identity.name` is non-empty → the brain has been set up before
- If `identity.name` is empty → this is a fresh onboard

**If previously populated:**
Show a brief summary of the current brain state:
```
Here's what I have for you currently:

Name: {identity.name} ({identity.brand})
Niche: {identity.niche}
Pillars: {pillars[].name, comma-separated}
Posting on: {platforms.posting[], comma-separated}
ICP: {icp.segments[], comma-separated}
Monetization: {monetization.primary_funnel}
```

Then ask: **"Want to update specific sections, or start completely fresh?"**
- If "update": Ask which sections to revisit, then jump to those sections only
- If "fresh": Proceed through all 7 sections below

**If fresh onboard:** Say something like: *"Let's build your agent brain. I'll walk you through 7 areas — who you are, who your content is for, what you talk about, where you post, who you're watching, how often you publish, and how you monetize. This takes about 10 minutes and everything you tell me makes the entire system smarter."*

Then proceed to Phase B.

---

## Phase B: Interactive Onboarding (7 Sections)

Walk through these sections conversationally. Ask 1-2 sections at a time, then pause for the user to respond. **Do NOT dump all questions at once.** Synthesize their free-text answers into the structured fields — the user should never have to write JSON.

If the user gives short or vague answers, probe deeper: *"Can you give me 2-3 more examples?"* or *"What specifically about that frustrates them?"*

---

### Section 1: Identity

**Open with context:** *"Let's start with who you are and what you're building. This helps me match your voice and brand in everything I generate."*

Ask about:
- **What's your name?** → `identity.name`
- **What's your brand name or handle?** (e.g., "@charlieautomates", "CC Strategic") → `identity.brand`
- **What's your content niche?** What space do you create in? → `identity.niche`
- **How would you describe your content tone?** Give examples: practical, bold, educational, irreverent, calm, high-energy, casual, professional → `identity.tone[]`
- **What makes you different from other creators in your space?** What's your unfair advantage or unique angle? → `identity.differentiator`

---

### Section 2: Ideal Customer Profile (ICP)

**Open with context:** *"Now let's define who your content is actually for. The more specific you are here, the better I can score topics and tailor angles to your audience."*

Ask about:
- **Who are your audience segments?** (e.g., agency owners, solopreneurs, SaaS founders, AI beginners) → `icp.segments[]`
- **What are their biggest pain points?** What keeps them up at night? What frustrates them? → `icp.pain_points[]`
- **What are they trying to achieve?** Their goals — both immediate and aspirational → `icp.goals[]`
- **Where does your audience hang out online?** Which platforms, communities, forums? → `icp.platforms_they_use[]`
- **What's their typical budget or revenue range?** (e.g., "$2-10M ARR", "bootstrapped $0-50k", "enterprise") → `icp.budget_range`

---

### Section 3: Content Pillars

**Open with context:** *"Content pillars are the 3-5 recurring themes that everything you create maps back to. They keep you focused and make your content recognizable. Most creators have 3-5."*

Ask about:
- **What themes do you keep coming back to?** What could you talk about every week and never run out of material?
- For each pillar the user mentions, capture:
  - `name` — short label (e.g., "AI Automation")
  - `description` — one sentence about what this covers
  - `keywords[]` — related search terms and subtopics

If they list fewer than 3, ask: *"Most successful creators have at least 3 pillars. Is there another angle or topic area you cover regularly?"*

→ Store as `pillars[]` array

---

### Section 4: Platforms

**Open with context:** *"Let's figure out where to look for trends and where you actually post. These can be different — you might research on Reddit but post on YouTube."*

**Research platforms** (where we scan for topics):
Present the available options: YouTube, Instagram, TikTok, LinkedIn, Facebook, Reddit, X (Twitter), Hacker News, GitHub

Ask: *"Which of these should I monitor for trending topics in your niche?"*
→ Store as `platforms.research[]`

**Posting platforms** (where you publish):
Present the available options: YouTube (longform), YouTube Shorts, Instagram Reels, Instagram Posts, TikTok, LinkedIn, Facebook

Ask: *"Which of these do you actively post on?"*
→ Store as `platforms.posting[]`

Note to user: *"API connections for each platform are set up later with /viral:setup. For now I just need to know which ones matter to you."*

Leave `platforms.api_keys_configured` as an empty array `[]` — this gets populated by /viral:setup.

---

### Section 5: Competitors

**Open with context:** *"Who in your space is worth watching? These are creators whose content strategy you can learn from — whether they're direct competitors or just people doing great work in adjacent areas."*

Ask for **2-5 creators** they follow or compete with. For each one, capture:
- `name` — their name or brand
- `platform` — where they're most active
- `handle` — their username/handle on that platform
- `why_watch` — what makes them worth monitoring (their angle, their growth, their style)

→ Store as `competitors[]` array

If they can only think of 1-2, that's fine. Say: *"You can always add more later. Even 1-2 gives us useful competitive signal."*

---

### Section 6: Cadence

**Open with context:** *"How often do you want to post? Consistency matters more than volume, so pick a pace you can actually sustain."*

Present defaults:
- **Shorts:** 2 per day, Monday through Saturday
- **Long-form:** 2 per week

Ask: *"Does this pace work for you, or would you like to adjust? Some creators do 1 short/day, others go harder at 3. For long-form, 1-3/week is the typical range."*

Capture:
- `cadence.weekly_schedule.shorts_per_day` — integer
- `cadence.weekly_schedule.shorts_days[]` — array of days (mon, tue, wed, thu, fri, sat, sun)
- `cadence.weekly_schedule.longform_per_week` — integer
- `cadence.weekly_schedule.longform_days[]` — array of days

Leave `cadence.optimal_times` as an empty object `{}` — this gets filled by /viral:analyze after performance data comes in.

---

### Section 7: Monetization

**Open with context:** *"Every piece of content should serve a funnel. Content without a monetization strategy is a hobby, not a business. Let's map out how your content connects to revenue."*

Ask about:
- **What's your primary monetization path?** (e.g., community/membership, agency services, SaaS product, courses, consulting, coaching) → `monetization.primary_funnel`
- **Any secondary revenue streams?** → `monetization.secondary_funnels[]`
- **What's your default call-to-action?** What do you usually tell viewers to do? → `monetization.cta_strategy.default_cta`
- **Do you have a lead magnet?** If so, what's the URL? → `monetization.cta_strategy.lead_magnet_url`
- **Community URL?** (Skool, Discord, etc.) → `monetization.cta_strategy.community_url`
- **Newsletter URL?** → `monetization.cta_strategy.newsletter_url`
- **Website URL?** → `monetization.cta_strategy.website_url`
- **How do you capture client info?** (DMs, intake form, booking link, etc.) → `monetization.client_capture`

For any URLs they don't have yet, store as empty string `""`.

---

## Phase C: Write and Confirm

After collecting all 7 sections, synthesize everything into the `agent-brain.json` structure.

### Critical rules for writing:

1. **PRESERVE system-managed fields exactly as they are:**
   - `learning_weights` — keep existing values (default: all 1.0)
   - `hook_preferences` — keep existing values (default: all 0)
   - `performance_patterns` — keep existing values (default: empty)

2. **Update metadata:**
   - `metadata.version` — keep as-is
   - `metadata.created_at` — keep original (don't overwrite)
   - `metadata.updated_at` — set to current ISO timestamp
   - `metadata.last_onboard` — set to current ISO timestamp
   - `metadata.evolution_log` — append a new entry:
     ```json
     {
       "timestamp": "[current ISO timestamp]",
       "reason": "Initial onboarding via /viral:onboard",
       "changes": ["Populated identity", "Populated ICP", "Set content pillars", "Configured platforms", "Added competitors", "Set cadence", "Defined monetization strategy"]
     }
     ```
     (If re-onboarding, change reason to "Re-onboarded via /viral:onboard" and list only the sections that changed)

3. **Validate before writing:**
   - All array fields should have at least 1 entry
   - `identity.name` must be non-empty
   - `icp.segments` must have at least 1 entry
   - `pillars` must have at least 1 entry
   - `platforms.research` must have at least 1 entry
   - `platforms.posting` must have at least 1 entry

4. **Write the complete brain** to `data/agent-brain.json`

### After writing, show a formatted summary:

```
Your Agent Brain
════════════════════════════════════════

Identity: {name} ({brand})
Niche: {niche}
Tone: {tone, comma-separated}
Differentiator: {differentiator}

ICP: {segments, comma-separated}
Pain points: {pain_points, comma-separated}
Goals: {goals, comma-separated}

Pillars: {pillar names, comma-separated}

Research: {research platforms, comma-separated}
Posting: {posting platforms, comma-separated}

Competitors: {competitor names, comma-separated}

Cadence: {shorts_per_day} shorts/day ({shorts_days}), {longform_per_week} long-form/week ({longform_days})

Monetization: {primary_funnel}
Default CTA: {default_cta}

════════════════════════════════════════
```

End with: *"Your agent brain is ready. Every module in the system now knows who you are, who you're talking to, and what you're building toward. Next steps: run `/viral:discover` to find trending topics for your audience, or `/viral:setup` to connect your platform APIs."*
