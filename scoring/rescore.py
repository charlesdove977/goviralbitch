#!/usr/bin/env python3
"""
Re-score existing topics when learning weights change.

Usage:
    python3 scoring/rescore.py [path/to/topics.jsonl]

If no path provided, finds the latest file in data/topics/.
"""

import json
import sys
from pathlib import Path

# Add project root to path so scoring imports work
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scoring.engine import load_brain_context, score_icp_relevance, score_content_gap, score_proof_potential, apply_competitor_bonuses, calculate_weighted_total


def find_latest_topics_file() -> Path:
    """Find the most recent topics JSONL file."""
    topics_dir = PROJECT_ROOT / "data" / "topics"
    if not topics_dir.exists():
        print("Error: data/topics/ directory not found")
        sys.exit(1)

    files = sorted(topics_dir.glob("*-topics.jsonl"), reverse=True)
    if not files:
        print("Error: No topics JSONL files found in data/topics/")
        sys.exit(1)

    return files[0]


def rescore_topics(filepath: Path) -> None:
    """Re-score all topics in a JSONL file using current brain weights."""
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    brain_ctx = load_brain_context()
    weights = brain_ctx["learning_weights"]

    topics = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                topics.append(json.loads(line))

    if not topics:
        print("No topics found in file.")
        return

    old_avg = sum(t["scoring"]["weighted_total"] for t in topics) / len(topics)
    biggest_change = 0.0
    biggest_change_id = ""

    for topic in topics:
        old_wt = topic["scoring"]["weighted_total"]
        text = f"{topic.get('title', '')} {topic.get('description', '')}"
        is_competitor = topic.get("source", {}).get("platform") == "competitor_analysis"

        if is_competitor:
            # Re-run full scoring for competitor topics
            views_str = topic.get("source", {}).get("engagement_signals", "0")
            # Extract numeric view count from engagement string
            views = _extract_views(views_str)

            scores = {
                "icp_relevance": score_icp_relevance(text, brain_ctx),
                "timeliness": topic["scoring"].get("timeliness", 6),
                "content_gap": score_content_gap(text, brain_ctx),
                "proof_potential": score_proof_potential(text),
            }
            scores = apply_competitor_bonuses(scores, views)
            scores["total"] = sum(scores[k] for k in ["icp_relevance", "timeliness", "content_gap", "proof_potential"])
            scores["weighted_total"] = calculate_weighted_total(scores, weights)
            topic["scoring"] = scores
        else:
            # For non-competitor topics, just recalculate weighted_total with new weights
            new_wt = calculate_weighted_total(topic["scoring"], weights)
            topic["scoring"]["weighted_total"] = new_wt

        change = abs(topic["scoring"]["weighted_total"] - old_wt)
        if change > biggest_change:
            biggest_change = change
            biggest_change_id = topic.get("id", "unknown")

    new_avg = sum(t["scoring"]["weighted_total"] for t in topics) / len(topics)

    # Write back in-place
    with open(filepath, "w", encoding="utf-8") as f:
        for topic in topics:
            f.write(json.dumps(topic, ensure_ascii=False) + "\n")

    # Print summary
    print(f"Re-scored {len(topics)} topics.")
    print(f"Avg weighted_total: {old_avg:.1f} → {new_avg:.1f}")
    if biggest_change_id:
        sign = "+" if biggest_change > 0 else ""
        print(f"Biggest change: {biggest_change_id} ({sign}{biggest_change:.1f})")


def _extract_views(engagement_str: str) -> int:
    """Extract numeric view count from engagement signals string."""
    import re
    # Match patterns like "504,167 views" or "100K views"
    match = re.search(r"([\d,]+)\s*views", engagement_str)
    if match:
        return int(match.group(1).replace(",", ""))

    match = re.search(r"(\d+)K\s*views", engagement_str, re.IGNORECASE)
    if match:
        return int(match.group(1)) * 1000

    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = Path(sys.argv[1])
        # Resolve relative paths from project root
        if not filepath.is_absolute():
            filepath = PROJECT_ROOT / filepath
    else:
        filepath = find_latest_topics_file()

    print(f"Re-scoring: {filepath.name}")
    rescore_topics(filepath)
