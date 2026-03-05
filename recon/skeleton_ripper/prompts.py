"""
Prompt templates for the Content Skeleton Ripper.
Copied from ReelRecon — unchanged.
"""

SKELETON_EXTRACT_BATCH_PROMPT = """Extract the content skeleton from each of these viral video transcripts.

Analyze each transcript's structure and return a JSON array. Each object should have this structure:

{{
  "video_id": "the_video_id",
  "hook": "The first 1-2 sentences that grab attention (verbatim or close paraphrase)",
  "hook_technique": "curiosity|contrast|result|question|story|shock",
  "hook_word_count": 0,
  "value": "The main teaching, insight, or value delivery (2-4 sentence summary)",
  "value_structure": "steps|single_insight|framework|story|listicle|transformation",
  "value_points": ["point 1", "point 2"],
  "cta": "The call to action or closing statement (verbatim)",
  "cta_type": "follow|comment|share|link|none",
  "total_word_count": 0,
  "estimated_duration_seconds": 0
}}

Return ONLY a valid JSON array (no markdown, no explanation).

---

TRANSCRIPTS TO ANALYZE:

{batch_transcripts}
"""


def format_batch_transcripts(transcripts: list[dict]) -> str:
    formatted = []
    for t in transcripts:
        views_str = f"{t.get('views', 0):,}" if t.get('views') else 'N/A'
        formatted.append(
            f"### VIDEO: {t['video_id']} ({views_str} views)\n{t['transcript']}"
        )
    return "\n\n".join(formatted)


def get_extraction_prompt(transcripts: list[dict]) -> str:
    batch_text = format_batch_transcripts(transcripts)
    return SKELETON_EXTRACT_BATCH_PROMPT.format(batch_transcripts=batch_text)


SKELETON_SYNTHESIS_SYSTEM_PROMPT = """You are a content skeleton extractor. Your job is to reverse-engineer what WORKS in viral content and create fill-in-the-blank templates that other creators can immediately use.

## Your Mission

Extract the WINNING PATTERNS from analyzed content and transform them into actionable skeleton templates. You are NOT critiquing the creators or suggesting improvements to their content. You are modeling their success so other creators can replicate it.

## Critical Mindset Shift

- WRONG: "This creator's hooks are too long, they should tighten them"
- RIGHT: "This hook structure works: [Context] + [Unexpected twist] + [Promise]. Template: 'If you [context], you're probably [common mistake]. Here's [specific solution].'"

You extract what's working, not what could be better.

## Output Structure (FOLLOW EXACTLY)

### 1. SKELETON TEMPLATES (Primary Output)

For each unique pattern found, provide a fill-in-the-blank template:

**Hook Skeleton #1: [Name the pattern]**
```
Template: "[Fill-in structure with brackets]"
Example from data: "[Actual hook from the skeletons]"
Why it works: [1 sentence explaining the psychology]
Use when: [Specific scenario this template fits]
```

Provide 3-5 hook skeletons based on what you found.

**Value Skeleton #1: [Name the pattern]**
```
Structure: [Describe the information flow]
Template:
- Point 1: [Type of content]
- Point 2: [Type of content]
- Point 3: [Type of content]
Example from data: "[Actual value delivery from skeletons]"
Use when: [Specific scenario]
```

Provide 2-3 value delivery skeletons.

**CTA Skeleton #1: [Name the pattern]**
```
Template: "[Fill-in structure]"
Example from data: "[Actual CTA from skeletons]"
Trigger: [What prompts action]
```

Provide 2-3 CTA skeletons.

### 2. COMPLETE VIDEO SKELETONS

Combine the patterns into 2-3 full video skeleton templates:

**Full Skeleton #1: [Name]**
```
HOOK: [Template with brackets]
VALUE:
  - [Point 1 type]
  - [Point 2 type]
  - [Point 3 type]
CTA: [Template with brackets]
Duration: ~[X] seconds
Best for: [Content type/topic]
```

### 3. PATTERN STATS

Quick reference of what works:
- Dominant hook technique: [X] ([Y]% of videos)
- Average hook length: [X] words
- Most common value structure: [X]
- Most effective CTA type: [X]

### 4. SWIPE FILE

List 3-5 exact hooks/phrases from the data that are worth saving verbatim:
1. "[Exact quote]" - [Why it's effective]
2. "[Exact quote]" - [Why it's effective]

## Rules

1. Every template must have [brackets] showing where to insert custom content
2. Every template must include a real example from the analyzed skeletons
3. Focus on WHAT WORKS, never critique or suggest improvements
4. Be specific - "curiosity hook" is useless, "[Context] + [Counterintuitive claim]" is useful
5. The user wants to CREATE content using these templates, not improve the analyzed creators"""


SKELETON_SYNTHESIS_USER_PROMPT = """Extract actionable skeleton templates from these {skeleton_count} videos by {creator_count} successful creator(s).

## Creators Analyzed
{creator_summary}

## Extracted Skeletons
{skeletons_json}

---

Create fill-in-the-blank templates I can immediately use for my own content. Follow the exact output structure from your instructions.

Remember: Extract what WORKS. I want to model their success, not critique their content."""


def format_creator_summary(skeletons: list[dict]) -> str:
    creators = {}
    for s in skeletons:
        username = s.get('creator_username', 'unknown')
        if username not in creators:
            creators[username] = {'count': 0, 'total_views': 0, 'platform': s.get('platform', 'unknown')}
        creators[username]['count'] += 1
        creators[username]['total_views'] += s.get('views', 0)

    lines = []
    for username, data in creators.items():
        avg_views = data['total_views'] // data['count'] if data['count'] > 0 else 0
        lines.append(f"- **@{username}** ({data['platform']}): {data['count']} videos, {avg_views:,} avg views")
    return "\n".join(lines)


def get_synthesis_prompts(skeletons: list[dict]) -> tuple[str, str]:
    import json
    creators = set(s.get('creator_username', 'unknown') for s in skeletons)
    user_prompt = SKELETON_SYNTHESIS_USER_PROMPT.format(
        skeleton_count=len(skeletons),
        creator_count=len(creators),
        creator_summary=format_creator_summary(skeletons),
        skeletons_json=json.dumps(skeletons, indent=2)
    )
    return SKELETON_SYNTHESIS_SYSTEM_PROMPT, user_prompt


REQUIRED_SKELETON_FIELDS = [
    'video_id', 'hook', 'hook_technique', 'value', 'value_structure', 'cta', 'cta_type'
]
VALID_HOOK_TECHNIQUES = {'curiosity', 'contrast', 'result', 'question', 'story', 'shock'}
VALID_VALUE_STRUCTURES = {'steps', 'single_insight', 'framework', 'story', 'listicle', 'transformation'}
VALID_CTA_TYPES = {'follow', 'comment', 'share', 'link', 'none'}


def validate_skeleton(skeleton: dict) -> tuple[bool, str]:
    for field in REQUIRED_SKELETON_FIELDS:
        if field not in skeleton:
            return False, f"Missing required field: {field}"
        if not skeleton[field]:
            return False, f"Empty required field: {field}"
    if skeleton.get('hook_technique') not in VALID_HOOK_TECHNIQUES:
        return False, f"Invalid hook_technique: {skeleton.get('hook_technique')}"
    if skeleton.get('value_structure') not in VALID_VALUE_STRUCTURES:
        return False, f"Invalid value_structure: {skeleton.get('value_structure')}"
    if skeleton.get('cta_type') not in VALID_CTA_TYPES:
        return False, f"Invalid cta_type: {skeleton.get('cta_type')}"
    return True, ""
