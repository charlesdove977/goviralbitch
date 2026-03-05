"""
Scoring engine for Viral Command topic scoring.

Scores topics against agent brain (ICP keywords, pillar matching,
learning weights) with competitor validation bonuses.
"""

from scoring.engine import (
    load_brain_context,
    score_topic,
    score_icp_relevance,
    score_content_gap,
    score_proof_potential,
    apply_competitor_bonuses,
    calculate_weighted_total,
)

__all__ = [
    "load_brain_context",
    "score_topic",
    "score_icp_relevance",
    "score_content_gap",
    "score_proof_potential",
    "apply_competitor_bonuses",
    "calculate_weighted_total",
]
