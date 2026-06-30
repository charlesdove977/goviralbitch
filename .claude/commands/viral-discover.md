# /viral:discover — Multi-Platform Topic Discovery

You are running the Viral Command discovery engine. Your job is to find winning content ideas through competitor analysis, keyword-based search (YouTube, Reddit, GitHub), or both — all scored against the creator's ICP.

**Arguments:** $ARGUMENTS

**Flags:**
| Flag | Description |
|------|-------------|
| `--competitors` | Skip mode selection, run competitor scrape only |
| `--keywords` | Skip mode selection, run keyword search only (YouTube + Reddit + GitHub) |
| `--all` | Skip mode selection, run both competitor scrape + keyword search |
| `--deep` | Use deep mode for trend queries (slower, more thorough) |
| (none) | Interactive — asks which discovery mode to use |

---

## ⚠️ EXECUTION ORDER — READ THIS FIRST

**You MUST follow this exact sequence. Do NOT skip steps or jump ahead.**

1. **Phase A**: Load agent brain (read `data/agent-brain.json`)
2. **Phase A.5**: Show keywords table + ask discovery mode [C/K/B] — **STOP HERE AND WAIT FOR USER INPUT**
3. **Only after user responds**: proceed to Phase 1 (competitor), Phase 1.5 (keyword), or both

**The #1 rule: After loading the brain, your VERY FIRST output to the user must be the keyword table and mode selector from Phase A.5. Do NOT start fetching YouTube data, Instagram data, or any API calls before the user picks a mode. No exceptions.**

---

## Phase A: Load Agent Brain

Read the agent brain to understand who the creator is:

```
@data/agent-brain.json
```

**Extract these fields:**
- `identity` — who the creator is, niche, tone
- `competitors[]` — competitor list with platform + handle
- `icp.segments[]`, `icp.pain_points[]`, `icp.goals[]` — scoring context + CCN fit evaluation
- `pillars[]` — content themes + keywords
- `learning_weights` — scoring multipliers
- `platforms.api_keys_configured` — available APIs

**If the brain is empty or `identity.name` is blank:**
Stop and say: *"Your agent brain isn't set up yet. Run `/viral:onboard` first to tell me who you are and what you create."*

---

## Phase A.5: Discovery Mode Selection — MANDATORY GATE

**⚠️ CRITICAL: This phase MUST run BEFORE any competitor scraping or data fetching. Do NOT skip this phase. Do NOT start pulling YouTube or Instagram data until the user has selected a discovery mode. Display the keyword table and mode selector, then STOP and wait for input.**

**Show the creator their current discovery keywords from the brain, then ask how they want to discover:**

```
═══════════════════════════════════════════════════
DISCOVERY KEYWORDS (from your agent brain)
═══════════════════════════════════════════════════

{For each pillar in pillars[]:}
{pillar.name}: {pillar.keywords[], comma-separated}

═══════════════════════════════════════════════════

These keywords drive YouTube Search, Reddit, and GitHub discovery.
To update them permanently, run /viral:onboard or /viral:update-brain.

How do you want to discover today?

  [C] Competitor scrape — analyze your competitors' recent content
  [K] Keyword search — search YouTube, Reddit, and GitHub for what's trending
  [B] Both — competitor scrape + keyword search

Choice [C/K/B]:
```

**Wait for user input.**

- If user says anything about updating/changing/editing keywords before choosing a mode, let them edit for THIS session only:
  - Show current keywords
  - Accept additions or removals
  - Use the modified list for this run
  - Note: *"Using modified keywords for this session. Run /viral:update-brain to save permanently."*

- Store the choice as `DISCOVERY_MODE` (competitor / keyword / both)
- **If `--competitors` flag in arguments:** skip this prompt, set `DISCOVERY_MODE = competitor`
- **If `--keywords` flag in arguments:** skip this prompt, set `DISCOVERY_MODE = keyword`
- **If `--all` flag in arguments:** skip this prompt, set `DISCOVERY_MODE = both`

**Based on DISCOVERY_MODE:**
- `competitor` → Run Phase 1 only, skip Phase 1.5
- `keyword` → Skip Phase 1, run Phase 1.5 only
- `both` → Run Phase 1, then Phase 1.5

---

## Phase 1: Competitor Analysis (Core)

**⚠️ PREREQUISITE: Phase A.5 must have completed first. The user must have selected a DISCOVERY_MODE. If you haven't shown the keyword table and mode selector yet, GO BACK to Phase A.5 now.**

**Skip this phase entirely if `DISCOVERY_MODE = keyword`.**

Pull and rank competitor **longform** content from the last 30 days.

**IMPORTANT: Longform only.** Filter out YouTube Shorts and any video under 5 minutes. We only care about longform content (5+ minutes) for competitor analysis. Shorts have different dynamics and aren't useful for longform content strategy.

### Step 1: Pull YouTube Competitor Content

For each competitor where `platform == "YouTube"`:

1. **Get channel ID from handle** using YouTube Data API:
   ```bash
   # Load API key from .env
   source "$(pwd)/.env" 2>/dev/null || source "$(dirname "$(pwd)")/.env" 2>/dev/null

   # Search for channel by handle
   curl -s "https://www.googleapis.com/youtube/v3/search?part=snippet&q=${HANDLE}&type=channel&key=${YOUTUBE_API_KEY}"
   ```
   Extract the `channelId` from the response.

2. **Pull recent videos** (last 30 days):
   ```bash
   # Get date 30 days ago in RFC3339 format
   PUBLISHED_AFTER=$(date -u -v-30d '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -d '30 days ago' '+%Y-%m-%dT%H:%M:%SZ')

   curl -s "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=${CHANNEL_ID}&order=date&publishedAfter=${PUBLISHED_AFTER}&maxResults=50&type=video&key=${YOUTUBE_API_KEY}"
   ```

3. **Get video statistics + duration** (views, likes, comments, contentDetails):
   ```bash
   # Comma-separated video IDs from step 2
   curl -s "https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&id=${VIDEO_IDS}&key=${YOUTUBE_API_KEY}"
   ```

4. **Filter to longform only** — parse `contentDetails.duration` (ISO 8601 format like `PT11M8S`) and **discard any video under 5 minutes**. YouTube Shorts and short clips are noise for this analysis.

5. **Calculate engagement rate** for each remaining video:
   ```
   engagement_rate = (likes + comments) / views × 100
   ```

### Step 2: Pull Instagram Competitor Content

For each competitor where `platform == "Instagram"`:

1. **Scrape recent posts/reels** using instaloader:
   ```bash
   # Create temp directory for scrape
   mkdir -p /tmp/viral-discover-ig

   # PRE-FLIGHT: instaloader freshness check (run ONCE per session)
   # Instagram changes its API frequently — stale instaloader = 403/login errors
   if [ -z "$INSTALOADER_CHECKED" ]; then
     INSTA_AGE_DAYS=$(python3 -c "
import importlib.metadata, datetime, re
v = importlib.metadata.version('instaloader')
parts = [int(x) for x in re.findall(r'\d+', v)[:3]]
d = datetime.datetime(parts[0] + (2000 if parts[0] < 100 else 0), parts[1], parts[2])
print((datetime.datetime.now() - d).days)
" 2>/dev/null || echo "999")
     if [ "$INSTA_AGE_DAYS" -gt 60 ]; then
       echo "⚠ instaloader is ${INSTA_AGE_DAYS} days old — updating to avoid Instagram 403 blocks..."
       pip3 install -U instaloader 2>&1 | tail -2
     fi
     INSTALOADER_CHECKED=1
   fi

   # Pull posts from last 30 days (metadata only — no media download)
   # IMPORTANT: Use python3 -m instaloader (not bare instaloader) for PATH compatibility
   python3 -m instaloader --no-pictures --no-videos --no-video-thumbnails --post-metadata-txt="" --dirname-pattern="/tmp/viral-discover-ig/{profile}" -- ${HANDLE}
   ```

   **Note:** If instaloader hits 403 rate limits, it auto-retries — that's normal. If it fully fails or requires login, inform the user and skip that competitor. Don't block the whole discovery on Instagram failures.

2. **Parse the scraped metadata** for each post:
   - Caption text (this is the "title" equivalent)
   - Likes count
   - Comments count
   - Post date
   - Post type (reel, carousel, single image)
   - **URL** — build from shortcode: `https://www.instagram.com/reel/{shortcode}/` for reels, `https://www.instagram.com/p/{shortcode}/` for posts. The shortcode is in the JSON filename or metadata.

3. **Calculate engagement rate:**
   ```
   engagement_rate = (likes + comments) / followers × 100
   ```
   (If follower count unavailable, use likes + comments as raw engagement)

### Step 3: Rank All Content

Combine YouTube and Instagram results into a single ranked list:

1. **Normalize engagement** across platforms (YouTube views-based, Instagram followers-based)
2. **Sort by raw engagement** (total likes + comments + views) as primary sort
3. **Display the TOP 10 performing pieces** across all competitors:

```
═══════════════════════════════════════════════════
COMPETITOR CONTENT — TOP 10 (Last 30 Days)
═══════════════════════════════════════════════════

 #  │ Platform  │ Competitor       │ Title/Caption                    │ Views/Likes  │ Eng%
────┼───────────┼──────────────────┼──────────────────────────────────┼──────────────┼──────
 1  │ YouTube   │ Chase Hannegan   │ {title}                          │ {views}      │ {rate}%
    │           │                  │ https://youtube.com/watch?v=...  │              │
────┼───────────┼──────────────────┼──────────────────────────────────┼──────────────┼──────
 2  │ Instagram │ Cooper Simson    │ {caption first 50 chars}...      │ {likes}      │ {rate}%
    │           │                  │ https://instagram.com/reel/...   │              │
────┼───────────┼──────────────────┼──────────────────────────────────┼──────────────┼──────
...

═══════════════════════════════════════════════════
```

**Every entry must include the direct URL** — YouTube: `https://youtube.com/watch?v={VIDEO_ID}`, Instagram: `https://www.instagram.com/reel/{SHORTCODE}/` or `https://www.instagram.com/p/{SHORTCODE}/`

### Step 4: Interactive Transcription

After showing the top 10, ask the user:

```
Want to transcribe any of these for deeper analysis?
Enter numbers (e.g., "1,3,5") or "skip" to continue without transcription:
```

**For each selected video/reel:**

**YouTube transcription + visual analysis:**
```bash
# Chrome cookies bypass SABR detection — fallback retries without cookies if Chrome unavailable
# IMPORTANT: Track all failures — never silently skip a failed step

# PRE-FLIGHT: yt-dlp freshness check (run ONCE before first download in batch)
# YouTube changes bot detection frequently — stale yt-dlp = 403 errors, hung downloads
# Only runs once per session (guard with YT_DLP_CHECKED variable)
if [ -z "$YT_DLP_CHECKED" ]; then
  YTDLP_AGE_DAYS=$(python3 -c "
import subprocess, datetime
v = subprocess.check_output(['yt-dlp', '--version']).decode().strip()
d = datetime.datetime.strptime(v, '%Y.%m.%d')
print((datetime.datetime.now() - d).days)
" 2>/dev/null || echo "999")
  if [ "$YTDLP_AGE_DAYS" -gt 30 ]; then
    echo "⚠ yt-dlp is ${YTDLP_AGE_DAYS} days old — updating to avoid YouTube 403 blocks..."
    pip3 install -U yt-dlp 2>&1 | tail -2
  fi
  YT_DLP_CHECKED=1
fi

# 1. Download audio for transcription (primary: with cookies, fallback: without)
yt-dlp --cookies-from-browser chrome -x --audio-format mp3 -o "/tmp/viral-discover-yt/%(id)s.%(ext)s" "https://youtube.com/watch?v=${VIDEO_ID}" 2>/tmp/viral-discover-yt/${VIDEO_ID}_audio_err.txt
if [ $? -ne 0 ]; then
  yt-dlp -x --audio-format mp3 -o "/tmp/viral-discover-yt/%(id)s.%(ext)s" "https://youtube.com/watch?v=${VIDEO_ID}" 2>>/tmp/viral-discover-yt/${VIDEO_ID}_audio_err.txt
  if [ $? -ne 0 ]; then
    echo "⚠ [${VIDEO_TITLE}]: audio download failed — $(tail -1 /tmp/viral-discover-yt/${VIDEO_ID}_audio_err.txt)"
    # Add to FAILURES list: {title, step: "audio download", error: last line of err, retryable: true if 429/timeout}
  fi
fi

# 2. Download first 60 seconds of video for visual hook analysis (480p max to keep size small)
# Primary: with cookies, fallback: without
yt-dlp --cookies-from-browser chrome --download-sections "*0-60" -f "best[height<=480][ext=mp4]/best[height<=480]/best" \
  -o "/tmp/viral-discover-yt/%(id)s_visual.%(ext)s" "https://youtube.com/watch?v=${VIDEO_ID}" 2>/tmp/viral-discover-yt/${VIDEO_ID}_video_err.txt
if [ $? -ne 0 ]; then
  yt-dlp --download-sections "*0-60" -f "best[height<=480][ext=mp4]/best[height<=480]/best" \
    -o "/tmp/viral-discover-yt/%(id)s_visual.%(ext)s" "https://youtube.com/watch?v=${VIDEO_ID}" 2>>/tmp/viral-discover-yt/${VIDEO_ID}_video_err.txt
  if [ $? -ne 0 ]; then
    echo "⚠ [${VIDEO_TITLE}]: video download failed — $(tail -1 /tmp/viral-discover-yt/${VIDEO_ID}_video_err.txt)"
    # Add to FAILURES list: {title, step: "video download", error: last line of err, retryable: true if 429/timeout}
  fi
fi

# 3. Extract frames from hook section (0-20 seconds for longform, 1 frame/sec = 20 frames)
mkdir -p "/tmp/viral-discover-yt/${VIDEO_ID}_frames"
ffmpeg -i "/tmp/viral-discover-yt/${VIDEO_ID}_visual.mp4" -t 20 -vf "fps=1" \
  "/tmp/viral-discover-yt/${VIDEO_ID}_frames/frame_%02d.jpg" -y 2>/tmp/viral-discover-yt/${VIDEO_ID}_ffmpeg_err.txt
if [ $? -ne 0 ]; then
  ffmpeg -i "/tmp/viral-discover-yt/${VIDEO_ID}_visual.webm" -t 20 -vf "fps=1" \
    "/tmp/viral-discover-yt/${VIDEO_ID}_frames/frame_%02d.jpg" -y 2>/tmp/viral-discover-yt/${VIDEO_ID}_ffmpeg_err.txt
  if [ $? -ne 0 ]; then
    echo "⚠ [${VIDEO_TITLE}]: frame extraction failed — $(tail -1 /tmp/viral-discover-yt/${VIDEO_ID}_ffmpeg_err.txt)"
    # Add to FAILURES list: {title, step: "frame extraction", error: last line of err, retryable: true if corrupt download}
    # Proceed with transcript-only analysis (graceful degradation — no visual)
  fi
fi

# 4. Transcribe with OpenAI Whisper API (preferred — faster, more reliable)
curl -s https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -F file="@/tmp/viral-discover-yt/${VIDEO_ID}.mp3" \
  -F model="whisper-1" \
  -F response_format="text"
```

If OpenAI API unavailable, fall back to local whisper:
```bash
whisper "/tmp/viral-discover-yt/${VIDEO_ID}.mp3" --model base --output_format txt --output_dir /tmp/viral-discover-yt/
```

**Instagram transcription + visual analysis:**
```bash
# IMPORTANT: Track all failures — never silently skip a failed step

# 1. Download reel video (used for BOTH audio + visual — no need to download twice)
python3 -m instaloader --dirname-pattern="/tmp/viral-discover-ig/{profile}" -- -${SHORTCODE} 2>/tmp/viral-discover-ig/${SHORTCODE}_dl_err.txt
if [ $? -ne 0 ]; then
  echo "⚠ [${VIDEO_TITLE}]: Instagram download failed — $(tail -1 /tmp/viral-discover-ig/${SHORTCODE}_dl_err.txt)"
  # Add to FAILURES list: {title, step: "Instagram download", error: last line of err, retryable: true if 403 rate limit}
  # Skip steps 2-3 for this video — no file to extract from
fi

# 2. Extract audio for transcription
ffmpeg -i "/tmp/viral-discover-ig/${HANDLE}/${POST_FILE}" -vn -acodec libmp3lame \
  "/tmp/viral-discover-ig/${HANDLE}/${SHORTCODE}.mp3" 2>/tmp/viral-discover-ig/${SHORTCODE}_audio_err.txt
if [ $? -ne 0 ]; then
  echo "⚠ [${VIDEO_TITLE}]: audio extraction failed — $(tail -1 /tmp/viral-discover-ig/${SHORTCODE}_audio_err.txt)"
  # Add to FAILURES list: {title, step: "audio extraction", error: last line of err, retryable: false if source file missing}
fi

# 3. Extract frames from hook section (0-15 seconds, 1 frame/sec)
mkdir -p "/tmp/viral-discover-ig/${HANDLE}/${SHORTCODE}_frames"
ffmpeg -i "/tmp/viral-discover-ig/${HANDLE}/${POST_FILE}" -t 15 -vf "fps=1" \
  "/tmp/viral-discover-ig/${HANDLE}/${SHORTCODE}_frames/frame_%02d.jpg" -y 2>/tmp/viral-discover-ig/${SHORTCODE}_ffmpeg_err.txt
if [ $? -ne 0 ]; then
  echo "⚠ [${VIDEO_TITLE}]: frame extraction failed — $(tail -1 /tmp/viral-discover-ig/${SHORTCODE}_ffmpeg_err.txt)"
  # Add to FAILURES list: {title, step: "frame extraction", error: last line of err, retryable: true if corrupt download}
  # Proceed with transcript-only analysis (graceful degradation — no visual)
fi

# 4. Then use OpenAI Whisper API or local whisper (same as YouTube above)
```

**Visual analysis — read frames directly (no separate API key needed):**

After frame extraction, use the Read tool to load the images directly into the current Claude Code session and analyze them visually. This requires **no API key** — it runs on your existing Claude Code subscription.

```
VISUAL ANALYSIS INSTRUCTIONS (run after frames are extracted):

1. Confirm frames exist:
   - YouTube: /tmp/viral-discover-yt/{VIDEO_ID}_frames/frame_*.jpg
   - Instagram: /tmp/viral-discover-ig/{HANDLE}/{SHORTCODE}_frames/frame_*.jpg

2. Use the Read tool to load up to 10 frames — read each file path directly as an image:
   - **YouTube longform (20s window):** Priority: frame_01-04.jpg (hook), then sample: frame_06, frame_08, frame_10, frame_14, frame_18, frame_20.jpg
   - **Instagram / YouTube Shorts (15s window):** Priority: frame_01-04.jpg (hook), then sample: frame_06, frame_08, frame_10, frame_12.jpg

3. After reading the frames, analyze what's visible and produce:
   - VISUAL HOOK (0-3s): What does the viewer SEE instantly?
     • Creator on camera? Expression/energy?
     • Text overlays? Exact wording if legible?
     • Background/setting?
     • B-roll, screen recording, or demo footage?
     • What makes it visually impossible to scroll past?
   - TEXT ON SCREEN: Any captions, title cards, or overlays
   - VISUAL PACING: Slow/medium/fast? Zoom or motion effects?
   - WHAT'S BEING SHOWN (not said): Results proof, tool demo, problem scenario?
   - VISUAL HOOK TYPE: face_reaction | screen_demo | result_reveal | text_hook | b_roll_contrast | talking_head | pattern_interrupt_visual
   - STEAL THIS: One specific visual tactic Charles could replicate immediately

4. If any step fails, log it to a failures list with the reason. Track each failure as:
   - Which video (title + URL)
   - Which step failed (video download / frame extraction / frame read)
   - Why it failed (error message from yt-dlp, ffmpeg, or Read tool)
   - Whether it's retryable (yes for rate limits/timeouts, no for missing content/private accounts)

   Common failure reasons:
   - yt-dlp: "Video unavailable" (not retryable), "HTTP 429" (retryable — rate limit)
   - ffmpeg: "No such file" (video download failed first), "Invalid data" (corrupt download — retryable)
   - instaloader: "403 Forbidden" (retryable — rate limit), "Login required" (not retryable without auth)
   - Read tool: "No such file" (frames weren't extracted — check ffmpeg step)

   Continue without blocking the rest of the flow.
```

**After all selected videos are processed, if any failures occurred, display a failures table BEFORE the transcript dissection output:**

```
═══════════════════════════════════════════════════
⚠ DOWNLOAD/EXTRACTION FAILURES ({N} of {M} videos)
═══════════════════════════════════════════════════

 #  │ Video                           │ Step Failed         │ Error                          │ Retryable
────┼─────────────────────────────────┼─────────────────────┼────────────────────────────────┼──────────
 1  │ {title}                         │ {step}              │ {error msg, 1 line}            │ {YES/NO}
────┼─────────────────────────────────┼─────────────────────┼────────────────────────────────┼──────────
...

{If ALL selected videos failed:}
⚠ All downloads failed. Diagnostic tips:
  1. Check Chrome is installed and you're logged into YouTube
  2. Run: yt-dlp --version (must be 2024.01+)
  3. Run: yt-dlp --cookies-from-browser chrome --print title "https://youtube.com/watch?v=dQw4w9WgXcQ"
  4. If Chrome cookies fail, try updating yt-dlp: pip install -U yt-dlp

═══════════════════════════════════════════════════
```

**Rule:** Videos that failed download are excluded from transcript dissection (Step 5) but still appear in the failures table. Videos where only frame extraction failed proceed to Step 5 with transcript-only analysis (visual section shows "visual: unavailable — frame extraction failed").

### Step 5: Dissect Transcripts + Visual Analysis

For each transcribed piece, produce a breakdown combining **verbal** (from transcript) and **visual** (from frame analysis) insights:

```
═══════════════════════════════════════════════════
CONTENT BREAKDOWN: {title}
By: {competitor} ({platform})
Views: {views} | Engagement: {rate}%
═══════════════════════════════════════════════════

VERBAL HOOK (first 3 seconds — what they SAY):
"{exact opening words from transcript}"
→ Hook type: {contradiction/specificity/pattern interrupt/etc.}
→ Why it works: {1-2 sentences}

VISUAL HOOK (first 3 seconds — what viewer SEES):
→ On screen: {what's visible — creator face/expression, B-roll, screen demo, etc.}
→ Text overlays: "{any text cards or captions on screen}"
→ Visual type: {face_reaction | screen_demo | result_reveal | text_hook | b_roll_contrast | talking_head | pattern_interrupt_visual}
→ Pattern interrupt: {what makes it visually impossible to scroll past}
→ Pacing: {slow/medium/fast cuts, any zoom or motion}
[If visual unavailable: visual: unavailable — {reason}]

WHAT'S SHOWN (not said) during setup (0:03-0:20 for longform, 0:03-0:15 for shorts/reels):
→ {what's on screen — results proof, tool demo, problem scenario, etc.}

STRUCTURE:
1. Hook (0:00-0:03): {verbal + visual combined — what they say AND show}
2. Setup (0:03-0:15 shorts | 0:03-0:20 longform): {what happens}
3. Body (0:15-0:45): {what happens}
4. CTA (0:45-end): {what happens}

ANGLES USED:
- {angle 1}: {how it's applied}
- {angle 2}: {how it's applied}

WHY IT WORKED:
- {engagement signal 1}
- {engagement signal 2}
- {what Charles could learn from this — verbal}
- {what Charles could steal visually — one specific tactic}

═══════════════════════════════════════════════════
```

### Step 6: Save Swipe Hooks (Transcribed Content Only)

**This step only runs if at least one video/reel was transcribed in Step 4.** Skip entirely if the user selected "skip" in Step 4 or if no transcriptions completed successfully.

After displaying all transcript breakdowns, present the swipe save prompt:

```
═══════════════════════════════════════════════════
SWIPE FILE — Save Hook Inspiration
═══════════════════════════════════════════════════

These hooks came from real competitor videos with verified engagement.
Saving them lets /viral:script generate swipe-influenced hooks alongside its standard output.

{For each transcribed video, list the dissected hook:}

 #  │ Competitor        │ Hook (opening words)                    │ Pattern
────┼───────────────────┼─────────────────────────────────────────┼──────────────────────
 1  │ {competitor}      │ "{first ~8 words of hook}"...           │ {pattern type}
 2  │ {competitor}      │ "{first ~8 words of hook}"...           │ {pattern type}
...

Which hooks do you want to save to your swipe file?
Enter numbers (e.g., "1, 3"), "all", or "skip":
```

**Wait for user input before proceeding.**

**If "skip":** Continue to Phase 2 immediately. Do not write any files.

**If "all" or specific numbers:**

For each selected hook, build a swipe entry object matching `schemas/swipe-hook.schema.json`:

**ID Generation:**
1. Create `data/recon/swipe/` directory if it doesn't exist (`mkdir -p data/recon/swipe/`)
2. Check today's swipe file: `data/recon/swipe/{YYYY-MM-DD}-hooks.jsonl`
3. Find the highest existing sequence number in today's file (if any)
4. Increment: `swipe_{YYYYMMDD}_{NNN}` with zero-padded 3-digit sequence
5. If no file exists today, start at 001

**For each selected hook, build the object:**

```json
{
  "id": "swipe_{YYYYMMDD}_{NNN}",
  "hook_text": "{exact opening words from transcript dissection — full hook line, not truncated}",
  "pattern": "{pattern identified in Step 5 dissection — use exact enum value: contradiction/specificity/timeframe_tension/pov_as_advice/vulnerable_confession/pattern_interrupt}",
  "why_it_works": "{the 'Why it works' analysis from Step 5 dissection — 1-2 sentences}",
  "visual_hook": {
    "available": true,
    "type": "{face_reaction | screen_demo | result_reveal | text_hook | b_roll_contrast | talking_head | pattern_interrupt_visual — from Step 5 VISUAL HOOK section, or null if unavailable}",
    "on_screen": "{what the viewer sees in the first 3 seconds — from Step 5 visual analysis, or null}",
    "text_overlays": "{any text cards or captions visible on screen in hook, or null}",
    "pattern_interrupt": "{the visual tactic that makes it impossible to scroll past, or null}",
    "steal_this": "{one specific visual tactic Charles could copy — from Step 5 TAKEAWAY, or null}"
  },
  "competitor": "{competitor name from agent brain}",
  "platform": "{youtube_longform or instagram_reels — whichever this content came from}",
  "url": "{direct URL from Step 3 table}",
  "engagement": {
    "views": 0,
    "likes": 0,
    "comments": 0,
    "engagement_rate": 0
  },
  "competitor_angle": "{the contrast/angle the competitor used — from 'ANGLES USED' section of Step 5 breakdown, if identifiable, else ''}",
  "topic_keywords": ["{extract 3-6 keywords from the hook text and video title — these drive /viral:script matching}"],
  "source_video_title": "{full video title or first 100 chars of caption}",
  "saved_at": "{current ISO timestamp}",
  "used_count": 0,
  "notes": ""
}
```

**If visual analysis was unavailable** for a video (frame extraction failed or `ANTHROPIC_API_KEY` not set), set `visual_hook.available = false` and all other `visual_hook` fields to `null`.

**Fill `engagement` with actual stats** from the Step 3 ranking table (views, likes, comments, engagement_rate).

**Write each entry as one JSON line to `data/recon/swipe/{YYYY-MM-DD}-hooks.jsonl`** (append if file exists for today).

**Display confirmation:**

```
═══════════════════════════════════════════════════
✓ Saved {N} hook(s) to swipe file

data/recon/swipe/{YYYY-MM-DD}-hooks.jsonl

These hooks will appear as inspiration options next time you run:
  /viral:script {angle_id}

═══════════════════════════════════════════════════
```

**Rules:**
- Save `hook_text` as the FULL hook line from the transcript — not the truncated display version
- `pattern` must use the exact enum values from the schema
- `topic_keywords` should be thoughtful — extract what the angle is ABOUT, not filler words
- Idempotent: if the same hook text already exists in today's file (check existing entries), skip it and note "already saved"
- Do NOT save hooks from non-transcribed content (titles/captions only) — this step is transcript-exclusive

---

## Phase 1.5: Keyword Search Discovery

**Skip this phase if `DISCOVERY_MODE = competitor`.**

Search YouTube, Reddit, GitHub, and optional X source packets using the
creator's pillar keywords to find what's trending RIGHT NOW.

### Step 1: Build Search Queries

Combine pillar keywords into 3-5 focused search queries. Prioritize keywords that appear across multiple pillars (higher signal). Use the session-modified keywords if the user edited them in Phase A.5.

Example for pillars with keywords ["Claude Code", "AI agents", "MCP servers"]:
- "Claude Code" (exact match — highest priority)
- "AI agents automation" (combined)
- "MCP servers Claude" (combined)

### Step 2: YouTube Search

For each query, hit the YouTube Data API `search.list`:

```bash
source "$(pwd)/.env" 2>/dev/null || source "$(dirname "$(pwd)")/.env" 2>/dev/null

# Search YouTube for trending content (last 7 days, sorted by view count)
PUBLISHED_AFTER=$(date -u -v-7d '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%SZ')

curl -s "https://www.googleapis.com/youtube/v3/search?part=snippet&q=${QUERY}&type=video&order=viewCount&publishedAfter=${PUBLISHED_AFTER}&maxResults=10&key=${YOUTUBE_DATA_API_KEY}"
```

Then fetch stats for the returned video IDs:
```bash
curl -s "https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&id=${VIDEO_IDS}&key=${YOUTUBE_DATA_API_KEY}"
```

**Extract per result:**
- Title, channel name, video URL
- Views, likes, comments, engagement rate
- Duration (filter: keep both longform and shorts — label each)
- Published date

### Step 3: Reddit Search

For each query, hit the Reddit JSON API (no auth needed):

```bash
# Search Reddit for trending posts (last week, sorted by top)
# URL-encode the query
ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${QUERY}'))")

curl -s -H "User-Agent: ViralCommand/1.0" "https://www.reddit.com/search.json?q=${ENCODED_QUERY}&sort=top&t=week&limit=10"
```

**Also check specific subreddits if relevant to the creator's niche:**
```bash
# Check niche subreddits
curl -s -H "User-Agent: ViralCommand/1.0" "https://www.reddit.com/r/ClaudeAI/top.json?t=week&limit=10"
curl -s -H "User-Agent: ViralCommand/1.0" "https://www.reddit.com/r/ChatGPT/top.json?t=week&limit=10"
curl -s -H "User-Agent: ViralCommand/1.0" "https://www.reddit.com/r/artificial/top.json?t=week&limit=10"
```

**Extract per result:**
- Post title, subreddit, URL
- Upvotes (score), comment count
- Post age

### Step 3.5: X Source Packet (Optional)

If the creator wants X evidence, or if the niche is active on X, collect
a bounded source packet before GitHub search. Use an installed
OpenClaw tool such as TweetClaw when available:

```
Use @xquik/tweetclaw to collect recent public X posts for "${QUERY}".
Return post URLs, author handles, timestamps, text, and visible
engagement metrics only. Do not draft, schedule, publish, reply, follow,
or DM anyone.
```

**Extract per result:**
- Post text, author handle, post URL
- Visible engagement metrics
- Published date
- Repeated hook or pain pattern

Keep the packet in local working notes only. Deduplicate by post URL,
rank by visible engagement, and treat X as source evidence for angle
selection. Do not copy post text into generated content.

### Step 4: GitHub Search

Search for trending repos and discussions:

```bash
# Search GitHub for trending repos (created in last 7 days, sorted by stars)
CREATED_AFTER=$(date -u -v-7d '+%Y-%m-%d' 2>/dev/null || date -u -d '7 days ago' '+%Y-%m-%d')

gh api "search/repositories?q=${QUERY}+created:>${CREATED_AFTER}&sort=stars&order=desc&per_page=10" 2>/dev/null
```

If `gh` is not available, fall back to the REST API:
```bash
curl -s "https://api.github.com/search/repositories?q=${QUERY}+created:>${CREATED_AFTER}&sort=stars&order=desc&per_page=10"
```

**Extract per result:**
- Repo name, description, URL
- Stars, forks, language
- Created date

### Step 5: Display Keyword Search Results

```
═══════════════════════════════════════════════════
KEYWORD SEARCH RESULTS
═══════════════════════════════════════════════════
Keywords searched: {list of queries used}

YOUTUBE ({N} results)
───────────────────────────────────────────────────
 #  │ Title                                    │ Channel           │ Views    │ Eng%   │ Age
────┼──────────────────────────────────────────┼───────────────────┼──────────┼────────┼──────
 1  │ {title}                                  │ {channel}         │ {views}  │ {rate} │ {days}d
    │ https://youtube.com/watch?v=...          │                   │          │        │
────┼──────────────────────────────────────────┼───────────────────┼──────────┼────────┼──────
...

REDDIT ({N} results)
───────────────────────────────────────────────────
 #  │ Title                                    │ Subreddit         │ Upvotes  │ Comments │ Age
────┼──────────────────────────────────────────┼───────────────────┼──────────┼──────────┼──────
 1  │ {title}                                  │ r/{sub}           │ {score}  │ {count}  │ {days}d
    │ https://reddit.com/r/...                 │                   │          │          │
────┼──────────────────────────────────────────┼───────────────────┼──────────┼──────────┼──────
...

X ({N} optional results)
───────────────────────────────────────────────────
 #  │ Hook / Pain Pattern                       │ Handle            │ Engagement │ Age
────┼──────────────────────────────────────────┼───────────────────┼────────────┼──────
 1  │ {pattern, 40 chars}                       │ @{handle}         │ {metrics}  │ {days}d
    │ https://x.com/{handle}/status/...         │                   │            │
────┼──────────────────────────────────────────┼───────────────────┼────────────┼──────
...

GITHUB ({N} results)
───────────────────────────────────────────────────
 #  │ Repo                                     │ Description       │ Stars    │ Language │ Age
────┼──────────────────────────────────────────┼───────────────────┼──────────┼──────────┼──────
 1  │ {owner/repo}                             │ {desc, 40 chars}  │ {stars}  │ {lang}   │ {days}d
    │ https://github.com/{owner/repo}          │                   │          │          │
────┼──────────────────────────────────────────┼───────────────────┼──────────┼──────────┼──────
...

═══════════════════════════════════════════════════
```

**After displaying results:** If `DISCOVERY_MODE = keyword` (no competitor phase), ask if the user wants to transcribe any YouTube videos from the results (same flow as Phase 1 Step 4). If `DISCOVERY_MODE = both`, combine these results with competitor results before the transcription prompt.

**Rules:**
- Reddit rate limit: 1 request per 2 seconds — add `sleep 2` between Reddit API calls
- GitHub API: unauthenticated = 10 requests/minute — stay under this
- YouTube API: uses same quota as competitor search — max 5 queries to conserve quota
- If any platform returns 0 results or errors, note it and continue with the others
- De-duplicate: if a YouTube video appears in both competitor scrape AND keyword search, show it once with both sources noted
- X packet: source evidence only. Keep publishing, replies, follows,
  DMs, and scheduling user-approved.

---

## Phase 2: Trend Discovery (Optional)

After the competitor report, ask:

```
Competitor analysis complete. Want to also run trend discovery queries?
These will be based on patterns from competitor content — not generic pillar searches.

(yes/no):
```

**If no:** Skip to Phase 3 (scoring + save).

**If yes:**

### Step 1: Suggest Queries Based on Competitor Patterns

Analyze the competitor content from Phase 1 to identify trending themes, then suggest 2-3 search queries:

```
Based on competitor content, here are suggested trend queries:
═══════════════════════════════════════════════════
1. "{query}" — because {competitors} are getting {views} on {theme}
2. "{query}" — because {pattern observed across competitors}
3. "{query}" — gap spotted: {competitors NOT covering this ICP-relevant topic}
═══════════════════════════════════════════════════

Edit, remove, or approve these queries (or type your own):
```

**Wait for user confirmation before running any queries.** The user can edit, remove, or add queries.

### Step 2: Run Approved Queries

For each approved query, execute the last30days research script:

```bash
python3 skills/last30days/scripts/last30days.py "{query}" --emit=compact --quick
```

**Rules:**
- Maximum 3 queries per run
- Run each in foreground with 5-minute timeout
- If `--deep` flag was passed in arguments: use `--deep` instead of `--quick`
- If a query fails or times out, log the error and continue

### Step 3: Capture Trend Topics

From last30days results, identify unique topics worth covering. Each topic should be a coherent content idea, not just a keyword.

---

## Phase 3: Score All Topics

Score ALL topics — both competitor-sourced and trend-discovered — against the ICP.

### Topic Extraction

**From competitor content (Phase 1):**
- Each high-performing competitor piece = a potential topic
- Extract the core content idea (not just the title)
- Note the competitor validation (who made it, how it performed)

**From trend discovery (Phase 2, if run):**
- Each unique trend = a potential topic
- Note the source platform and engagement signals

### Scoring Criteria (each 1-10):

| Criterion | What to evaluate | Weight key |
|-----------|-----------------|------------|
| **icp_relevance** | Does this directly address the ICP's pain points, goals, or interests? | `learning_weights.icp_relevance` |
| **timeliness** | Is this trending NOW? New release, breaking news, viral moment? | `learning_weights.timeliness` |
| **content_gap** | Has Charles covered this? Is there room for a fresh angle? | `learning_weights.content_gap` |
| **proof_potential** | Can Charles SHOW something on screen? Demo, tutorial, walkthrough? | `learning_weights.proof_potential` |

### Calculate scores:

```
weighted_total = (icp_relevance × learning_weights.icp_relevance) +
                 (timeliness × learning_weights.timeliness) +
                 (content_gap × learning_weights.content_gap) +
                 (proof_potential × learning_weights.proof_potential)
```

### Competitor validation bonuses:
- Topics validated by competitor performance (>50K views) get **+2 content_gap** bonus
- Topics from top 3 competitor pieces get **+1 proof_potential** bonus

### CCN Fit (Core / Casual / New Audience):

After calculating scores, evaluate each topic's audience fit:

- **CORE**: Does this solve a $5K+ problem? Check against `icp.pain_points` — if the topic directly addresses a pain point that costs the audience real money/time, it's core.
- **CASUAL**: Interesting to 2+ audience segments from `icp.segments[]`? If only one segment would care, it's not casual.
- **NEW**: Could a stranger with zero AI context understand the hook? If it requires niche jargon or prior knowledge, it fails new.

**Rule:** Must hit 2 of 3 to be saved. Topics hitting only 1 are shown in the summary but excluded from JSONL output with a note: `[CCN: {which one} only — too niche]` or `[CCN: {which one} only — too broad]`.

Add `ccn_fit` object to each topic's `scoring` in JSONL output:
```json
"ccn_fit": { "core": true, "casual": true, "new_audience": false, "pass": true }
```

### Selection:
- Deduplicate: merge same topic from multiple sources
- CCN fit: must pass (2 of 3) to be saved — failed topics displayed but not written to JSONL
- Minimum threshold: weighted_total ≥ 20 (out of 40)
- If fewer than 5 topics meet threshold, lower to 15 and note it
- Target: 10-20 scored topics per run

---

## Phase 4: Save to JSONL

Write discovered topics to a date-stamped JSONL file:

**File path:** `data/topics/{YYYY-MM-DD}-topics.jsonl`

**One JSON object per line:**

```json
{
  "id": "topic_{YYYYMMDD}_{NNN}",
  "title": "Topic title — clear, specific, content-ready",
  "description": "Why this topic matters and why it's trending",
  "source": {
    "platform": "youtube|youtube_search|instagram|reddit|github|x|web|hackernews",
    "url": "https://source-url",
    "author": "Original author / competitor name",
    "engagement_signals": "500K views, 15K likes, 3.2% engagement"
  },
  "discovered_at": "2026-03-05T12:00:00Z",
  "scoring": {
    "icp_relevance": 8,
    "timeliness": 9,
    "content_gap": 7,
    "proof_potential": 8,
    "total": 32,
    "weighted_total": 32.0
  },
  "pillars": ["AI Automation"],
  "competitor_coverage": [
    {"name": "Chase Hannegan", "platform": "YouTube", "views": 150000, "url": "https://..."}
  ],
  "status": "new",
  "notes": ""
}
```

**Rules:**
- IDs: `topic_{YYYYMMDD}_{NNN}` with zero-padded 3-digit sequence
- Set `status: "new"` for all freshly discovered topics
- Set `discovered_at` to current ISO timestamp
- If file exists for today, **append** (no duplicates — check existing IDs)
- `competitor_coverage` should be populated for competitor-sourced topics

---

## Phase 5: Output Summary

```
═══════════════════════════════════════════════════
DISCOVERY COMPLETE
═══════════════════════════════════════════════════

Discovery mode: {competitor / keyword / both}

{If competitor mode or both:}
Competitors analyzed: {N}
  YouTube: {list handles} — {N} videos pulled
  Instagram: {list handles} — {N} posts pulled
Transcriptions done: {N} ({N} verbal + {N} visual)

{If keyword mode or both:}
Keyword search results:
  YouTube Search: {N} results across {N} queries
  Reddit: {N} posts from {N} subreddits
  GitHub: {N} repos trending
  Keywords used: {list of queries}

Trend queries run: {N} (or "skipped")
Total topics scored: {N} → {N saved} (after dedup + threshold)
Saved to: data/topics/{YYYY-MM-DD}-topics.jsonl

FAILURES ({N} of {M} videos failed — {N} retryable)
───────────────────────────────────────────────────
{If no failures: "None — all steps completed successfully."}

{For each failure:}
 ⚠ {video title} ({platform})
   Step: {video download | frame extraction | transcription | frame read}
   Error: {actual error message, truncated to 1 line}
   Retryable: {YES — retry later / NO — {reason}}

{If ALL selected videos failed:}
⚠ All downloads failed. Check:
  1. Chrome cookies: yt-dlp --cookies-from-browser chrome --print title "https://youtube.com/watch?v=dQw4w9WgXcQ"
  2. yt-dlp version: yt-dlp --version (must be 2024.01+)
  3. Update: pip install -U yt-dlp
───────────────────────────────────────────────────
{If any retryable failures:}
To retry failed items only, run /viral:discover again — cached
successes won't re-download, only failures will re-attempt.

TOP TOPICS BY SCORE
───────────────────────────────────────────────────

 #  │ Score │ Topic                                    │ Source
────┼───────┼──────────────────────────────────────────┼──────────────
 1  │ 35.0  │ {topic title}                            │ {competitor or trend}
    │       │ ICP: 9  Time: 9  Gap: 8  Proof: 9       │
    │       │ Why: {one line on why this scored high}   │
────┼───────┼──────────────────────────────────────────┼──────────────
 2  │ 33.0  │ {topic title}                            │ {source}
    │       │ ICP: 8  Time: 9  Gap: 8  Proof: 8       │
    │       │ Why: {one line}                           │
────┼───────┼──────────────────────────────────────────┼──────────────
...

COMPETITOR INSIGHTS
───────────────────────────────────────────────────
What's working for competitors right now:
- {competitor}: {pattern/theme} ({engagement stats})
- {competitor}: {pattern/theme} ({engagement stats})

Content gaps (competitors NOT covering):
- {gap 1} — relevant to Charles's ICP because {reason}
- {gap 2} — {reason}
───────────────────────────────────────────────────

RECOMMENDED NEXT STEPS
───────────────────────────────────────────────────

Develop these topics next with /viral:angle:

1. "{top topic}" — {reason it's the best pick}
2. "{second topic}" — {reason}
3. "{third topic}" — {reason}

Run: /viral:angle "{topic title}" to develop angles.

═══════════════════════════════════════════════════
```

Show top 10 topics maximum in the summary.

---

## Caching

To avoid re-scraping within the same day:

- **Cache directory:** `data/recon/cache/`
- **Cache files:** `{handle}_{YYYY-MM-DD}.json` for each competitor
- Before pulling competitor data, check if today's cache exists
- If cache hit: load from cache instead of API calls
- Cache includes: video/post list, statistics, engagement rates

---

## Important Rules

- **NEVER modify `data/agent-brain.json`** — discover is read-only on the brain
- **Competitor analysis is the core** — trend discovery is optional and secondary
- **No hardcoded queries** — all trend queries are suggested based on competitor patterns, user approves before running
- **Interactive transcription** — always ask which videos to transcribe, never auto-transcribe all
- **Always score against ICP** — topics without ICP relevance scoring are useless
- **Save before displaying** — write JSONL first, then show summary
- **Idempotent for same day** — running twice appends without duplicates (check existing IDs)
- **Graceful degradation** — if Instagram scraping fails, continue with YouTube only. If no API keys, explain what's missing.
- **Clean up temp files** after transcription (`/tmp/viral-discover-*`)
- **Maximum 3 trend queries** per run (API rate limits)
