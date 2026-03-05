"""
Recon Bridge — Converts skeleton ripper output into JSONL topics
matching schemas/topic.schema.json for the content-pipeline discovery system.

This is the key integration point: competitor analysis → scored topics.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from recon.config import load_competitors, BRAIN_FILE
from recon.utils.logger import get_logger

# Add project root to path for scoring imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scoring.engine import score_topic as engine_score_topic

logger = get_logger()

PIPELINE_DIR = Path(__file__).parent.parent
DATA_DIR = PIPELINE_DIR / "data"
RECON_DATA_DIR = DATA_DIR / "recon"
TOPICS_DIR = DATA_DIR / "topics"


def load_brain_pillars() -> List[str]:
    """Load content pillar names from agent brain."""
    if not BRAIN_FILE.exists():
        return []
    with open(BRAIN_FILE, 'r') as f:
        brain = json.load(f)
    return [p.get("name", "") for p in brain.get("pillars", [])]


def load_brain_learning_weights() -> Dict[str, float]:
    """Load learning weights from agent brain."""
    if not BRAIN_FILE.exists():
        return {"icp_relevance": 1.0, "timeliness": 1.0, "content_gap": 1.0, "proof_potential": 1.0}
    with open(BRAIN_FILE, 'r') as f:
        brain = json.load(f)
    return brain.get("learning_weights", {
        "icp_relevance": 1.0, "timeliness": 1.0,
        "content_gap": 1.0, "proof_potential": 1.0
    })


def skeleton_to_topic(
    skeleton: Dict,
    topic_index: int,
    date_str: str,
    pillars: List[str],
    weights: Dict[str, float],
) -> Dict:
    """
    Convert a single skeleton into a topic dict matching topic.schema.json.

    Competitor-validated topics get scoring bonuses:
    - High proof_potential (they already proved it works on screen)
    - High icp_relevance (competitor audience overlaps with ICP)
    """
    creator = skeleton.get("creator_username", "unknown")
    platform = skeleton.get("platform", "instagram")
    views = skeleton.get("views", 0)
    hook = skeleton.get("hook", "")
    value = skeleton.get("value", "")
    hook_technique = skeleton.get("hook_technique", "")
    value_structure = skeleton.get("value_structure", "")

    # Build topic title from skeleton content
    title = _generate_topic_title(hook, value, creator)

    # Build description
    description = (
        f"Competitor @{creator} posted a {value_structure} video using a {hook_technique} hook "
        f"that got {views:,} views. Value proposition: {value[:150]}"
    )

    # Score using the scoring engine (dynamic ICP keyword matching + competitor bonuses)
    scoring = engine_score_topic(
        title=title,
        description=description,
        views=views,
        timeliness=6,  # Competitor content is recent, not breaking news
        is_competitor=True,
    )

    # Map to pillars based on content keywords
    matched_pillars = _match_pillars(title + " " + description, pillars)

    topic_id = f"topic_{date_str}_{topic_index:03d}"

    return {
        "id": topic_id,
        "title": title,
        "description": description,
        "source": {
            "platform": "competitor_analysis",
            "url": skeleton.get("url", ""),
            "author": f"@{creator}",
            "engagement_signals": f"{views:,} views on {platform}"
        },
        "discovered_at": datetime.utcnow().isoformat() + "Z",
        "scoring": scoring,
        "pillars": matched_pillars,
        "competitor_coverage": [
            {
                "competitor": f"@{creator}",
                "url": skeleton.get("url", ""),
                "performance": f"{views:,} views"
            }
        ],
        "status": "new",
        "notes": f"Sourced from competitor recon. Hook technique: {hook_technique}. Value structure: {value_structure}."
    }


def _generate_topic_title(hook: str, value: str, creator: str) -> str:
    """Generate a clear topic title from skeleton content."""
    # Use the value summary as the primary title source
    if value and len(value) > 10:
        # Truncate to a reasonable title length
        title = value.split('.')[0].strip()
        if len(title) > 80:
            title = title[:77] + "..."
        return title

    # Fallback to hook
    if hook and len(hook) > 10:
        title = hook.split('.')[0].strip()
        if len(title) > 80:
            title = title[:77] + "..."
        return title

    return f"Content pattern from @{creator}"


def _match_pillars(text: str, pillars: List[str]) -> List[str]:
    """Match text against content pillars using keyword overlap."""
    if not pillars:
        return []

    text_lower = text.lower()
    matched = []
    for pillar in pillars:
        # Check if pillar name appears in the text
        if pillar.lower() in text_lower:
            matched.append(pillar)

    # If no direct match, include the first pillar as a catch-all
    if not matched and pillars:
        matched.append(pillars[0])

    return matched


def generate_topics_from_skeletons(
    skeletons: List[Dict],
    start_index: int = 1,
) -> List[Dict]:
    """
    Convert a list of skeletons into scored JSONL topics.

    Args:
        skeletons: List of skeleton dicts from the extraction pipeline
        start_index: Starting index for topic IDs (to avoid collisions)

    Returns:
        List of topic dicts matching topic.schema.json
    """
    pillars = load_brain_pillars()
    weights = load_brain_learning_weights()
    date_str = datetime.utcnow().strftime("%Y%m%d")

    topics = []
    for i, skeleton in enumerate(skeletons):
        topic = skeleton_to_topic(
            skeleton=skeleton,
            topic_index=start_index + i,
            date_str=date_str,
            pillars=pillars,
            weights=weights,
        )
        topics.append(topic)

    logger.info("BRIDGE", f"Generated {len(topics)} topics from {len(skeletons)} skeletons")
    return topics


def save_topics_jsonl(topics: List[Dict], date_str: Optional[str] = None) -> Path:
    """
    Save topics to a date-stamped JSONL file.
    Appends if file already exists for today.

    Returns:
        Path to the JSONL file
    """
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = TOPICS_DIR / f"{date_str}-topics.jsonl"

    # Load existing IDs to avoid duplicates
    existing_ids = set()
    if output_file.exists():
        with open(output_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        existing = json.loads(line)
                        existing_ids.add(existing.get("id", ""))
                    except json.JSONDecodeError:
                        pass

    new_count = 0
    with open(output_file, 'a', encoding='utf-8') as f:
        for topic in topics:
            if topic["id"] not in existing_ids:
                f.write(json.dumps(topic, ensure_ascii=False) + "\n")
                new_count += 1

    logger.info("BRIDGE", f"Saved {new_count} new topics to {output_file}")
    return output_file


def load_latest_skeletons() -> List[Dict]:
    """Load the most recent skeleton report from data/recon/reports/."""
    reports_dir = RECON_DATA_DIR / "reports"
    if not reports_dir.exists():
        return []

    # Find most recent report directory
    report_dirs = sorted(reports_dir.iterdir(), reverse=True)
    for rd in report_dirs:
        skeletons_file = rd / "skeletons.json"
        if skeletons_file.exists():
            with open(skeletons_file, 'r') as f:
                return json.load(f)

    return []
