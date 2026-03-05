"""
Scoring engine — scores topics against agent brain ICP, pillars, and learning weights.

No external dependencies beyond stdlib. Does NOT import from recon.
Read-only on agent-brain.json.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

BRAIN_FILE = Path(__file__).parent.parent / "data" / "agent-brain.json"

# Action keywords that indicate demonstrable/tutorial content
ACTION_KEYWORDS = [
    "build", "tutorial", "how to", "how-to", "demo", "walkthrough",
    "setup", "set up", "install", "create", "deploy", "step by step",
    "guide", "implement", "configure", "automate",
]

# Opinion keywords that indicate talking-head content (lower proof potential)
OPINION_KEYWORDS = [
    "opinion", "debate", "thoughts", "rant", "hot take", "unpopular",
    "controversial", "prediction", "review",
]


def load_brain_context() -> Dict:
    """
    Read agent-brain.json and return structured context for scoring.

    Returns dict with:
        icp_keywords: flattened list from icp.pain_points + goals + segments
        pillar_keywords: dict of {pillar_name: [keywords]}
        learning_weights: the 4 weight values
        competitor_handles: list of competitor handles
    """
    if not BRAIN_FILE.exists():
        return {
            "icp_keywords": [],
            "pillar_keywords": {},
            "learning_weights": {
                "icp_relevance": 1.0,
                "timeliness": 1.0,
                "content_gap": 1.0,
                "proof_potential": 1.0,
            },
            "competitor_handles": [],
        }

    with open(BRAIN_FILE, "r") as f:
        brain = json.load(f)

    icp = brain.get("icp", {})
    icp_keywords = []
    for field in ["pain_points", "goals", "segments"]:
        icp_keywords.extend(icp.get(field, []))

    pillar_keywords = {}
    for pillar in brain.get("pillars", []):
        name = pillar.get("name", "")
        keywords = pillar.get("keywords", [])
        if name:
            pillar_keywords[name] = keywords

    learning_weights = brain.get("learning_weights", {
        "icp_relevance": 1.0,
        "timeliness": 1.0,
        "content_gap": 1.0,
        "proof_potential": 1.0,
    })

    competitor_handles = []
    for comp in brain.get("competitors", []):
        handle = comp.get("handle", "")
        if handle:
            competitor_handles.append(handle.lstrip("@").lower())

    return {
        "icp_keywords": icp_keywords,
        "pillar_keywords": pillar_keywords,
        "learning_weights": learning_weights,
        "competitor_handles": competitor_handles,
    }


def _tokenize(text: str) -> str:
    """Lowercase and normalize text for matching."""
    return text.lower()


def _count_keyword_matches(text: str, keywords: List[str]) -> int:
    """
    Count how many keywords appear in the text.
    Uses partial/stem matching — 'automation' matches 'automate'.
    """
    text_lower = _tokenize(text)
    matches = 0
    for keyword in keywords:
        kw_lower = keyword.lower()
        # Extract key stems (first 5+ chars) for partial matching
        stems = _extract_stems(kw_lower)
        for stem in stems:
            if stem in text_lower:
                matches += 1
                break  # Count each keyword once
    return matches


def _extract_stems(text: str) -> List[str]:
    """
    Extract matchable stems from a keyword or phrase.
    For phrases like 'scale revenue without adding headcount',
    extract meaningful words as individual stems.
    """
    # Split into words, keep words with 4+ chars
    words = re.findall(r"[a-z]{4,}", text.lower())
    if not words:
        # Fall back to the whole text if no long words
        return [text.lower()] if len(text) >= 3 else []
    return words


def _count_pain_point_matches(text: str, pain_points: List[str]) -> int:
    """Count how many distinct pain points are referenced in text."""
    text_lower = _tokenize(text)
    matched = 0
    for pain in pain_points:
        stems = _extract_stems(pain.lower())
        # Require at least 2 stem matches for a pain point to count
        stem_hits = sum(1 for s in stems if s in text_lower)
        if stem_hits >= min(2, len(stems)):
            matched += 1
    return matched


def score_icp_relevance(text: str, brain_ctx: Dict) -> int:
    """
    Score ICP relevance (1-10) based on keyword overlap with brain ICP data.

    Scoring tiers:
        0 matches = 3
        1-2 matches = 5
        3-4 matches = 7
        5-6 matches = 8
        7+ matches = 9
        2+ pain_points matched = +1 (max 10)
    """
    icp_keywords = brain_ctx.get("icp_keywords", [])
    matches = _count_keyword_matches(text, icp_keywords)

    # Also count pillar keyword matches
    for pillar_kws in brain_ctx.get("pillar_keywords", {}).values():
        matches += _count_keyword_matches(text, pillar_kws)

    if matches == 0:
        score = 3
    elif matches <= 2:
        score = 5
    elif matches <= 4:
        score = 7
    elif matches <= 6:
        score = 8
    else:
        score = 9

    # Bonus for matching multiple pain points
    pain_points = [kw for kw in icp_keywords if len(kw) > 20]  # Pain points are longer phrases
    if _count_pain_point_matches(text, pain_points) >= 2:
        score = min(score + 1, 10)

    return score


def score_content_gap(text: str, brain_ctx: Dict) -> int:
    """
    Score content gap (1-10). Base heuristic — /analyze refines later.

    Base score: 6
    Matches pillar keywords: +2 (room for creator's unique angle)
    """
    score = 6
    text_lower = _tokenize(text)

    # Check if topic matches pillar keywords (indicates niche relevance)
    for pillar_name, keywords in brain_ctx.get("pillar_keywords", {}).items():
        for kw in keywords:
            if kw.lower() in text_lower:
                score = min(score + 2, 10)
                return score  # One pillar match is enough for the bonus

    return score


def score_proof_potential(text: str) -> int:
    """
    Score proof potential (1-10) based on action vs opinion keywords.

    Action keywords (build, tutorial, demo...): higher scores
    Opinion keywords (debate, rant, thoughts...): capped at 6
    """
    text_lower = _tokenize(text)

    # Check opinion keywords first (caps the score)
    opinion_count = sum(1 for kw in OPINION_KEYWORDS if kw in text_lower)
    if opinion_count > 0:
        return 6

    # Count action keywords
    action_count = sum(1 for kw in ACTION_KEYWORDS if kw in text_lower)

    if action_count == 0:
        return 5
    elif action_count <= 2:
        return 7
    else:
        return 8


def apply_competitor_bonuses(scores: Dict, views: int) -> Dict:
    """
    Apply competitor validation bonuses to scores.

    >100K views: content_gap +2, proof_potential +1
    >50K views: content_gap +1
    All capped at 10.
    """
    scores = dict(scores)  # Don't mutate input

    if views > 100_000:
        scores["content_gap"] = min(scores["content_gap"] + 2, 10)
        scores["proof_potential"] = min(scores["proof_potential"] + 1, 10)
    elif views > 50_000:
        scores["content_gap"] = min(scores["content_gap"] + 1, 10)

    return scores


def calculate_weighted_total(scores: Dict, weights: Dict) -> float:
    """
    Calculate weighted total from scores and learning weights.

    weighted = sum(scores[k] * weights[k]) for each criterion.
    Returns rounded to 1 decimal.
    """
    criteria = ["icp_relevance", "timeliness", "content_gap", "proof_potential"]
    total = sum(
        scores.get(k, 0) * weights.get(k, 1.0)
        for k in criteria
    )
    return round(total, 1)


def score_topic(
    title: str,
    description: str,
    views: int = 0,
    timeliness: int = 6,
    is_competitor: bool = False,
) -> Dict:
    """
    Orchestrator: score a topic against the agent brain.

    Args:
        title: Topic title
        description: Topic description
        views: View count (for competitor bonus calculation)
        timeliness: Timeliness score (1-10), provided by caller
        is_competitor: Whether this is from competitor analysis

    Returns:
        Scoring dict matching topic.schema.json scoring object:
        {icp_relevance, timeliness, content_gap, proof_potential, total, weighted_total}
    """
    brain_ctx = load_brain_context()
    text = f"{title} {description}"

    scores = {
        "icp_relevance": score_icp_relevance(text, brain_ctx),
        "timeliness": timeliness,
        "content_gap": score_content_gap(text, brain_ctx),
        "proof_potential": score_proof_potential(text),
    }

    if is_competitor and views > 0:
        scores = apply_competitor_bonuses(scores, views)

    scores["total"] = sum(scores[k] for k in ["icp_relevance", "timeliness", "content_gap", "proof_potential"])
    scores["weighted_total"] = calculate_weighted_total(scores, brain_ctx["learning_weights"])

    return scores
