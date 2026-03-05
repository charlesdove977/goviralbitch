"""
Aggregator for Content Skeleton Ripper.
Pure data transformation (no LLM calls). Ported from ReelRecon.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
from statistics import mean

from recon.utils.logger import get_logger

logger = get_logger()


@dataclass
class CreatorStats:
    username: str
    platform: str
    video_count: int
    total_views: int
    total_likes: int
    avg_views: float
    avg_likes: float
    avg_hook_word_count: float
    avg_total_word_count: float
    avg_duration_seconds: float
    hook_techniques: dict[str, int] = field(default_factory=dict)
    value_structures: dict[str, int] = field(default_factory=dict)
    cta_types: dict[str, int] = field(default_factory=dict)


@dataclass
class AggregatedData:
    skeletons: list[dict]
    creator_stats: list[CreatorStats]
    total_videos: int
    total_views: int
    valid_skeletons: int
    overall_hook_techniques: dict[str, int] = field(default_factory=dict)
    overall_value_structures: dict[str, int] = field(default_factory=dict)
    overall_cta_types: dict[str, int] = field(default_factory=dict)
    avg_hook_word_count: float = 0.0
    avg_total_word_count: float = 0.0
    avg_duration_seconds: float = 0.0


class SkeletonAggregator:
    def aggregate(self, skeletons: list[dict]) -> AggregatedData:
        if not skeletons:
            return AggregatedData(skeletons=[], creator_stats=[], total_videos=0, total_views=0, valid_skeletons=0)

        by_creator = defaultdict(list)
        for s in skeletons:
            by_creator[s.get('creator_username', 'unknown')].append(s)

        creator_stats = [self._calc_stats(u, sl) for u, sl in by_creator.items()]

        return AggregatedData(
            skeletons=skeletons,
            creator_stats=creator_stats,
            total_videos=len(skeletons),
            total_views=sum(s.get('views', 0) for s in skeletons),
            valid_skeletons=len(skeletons),
            overall_hook_techniques=self._count(skeletons, 'hook_technique'),
            overall_value_structures=self._count(skeletons, 'value_structure'),
            overall_cta_types=self._count(skeletons, 'cta_type'),
            avg_hook_word_count=self._safe_mean([s.get('hook_word_count', 0) for s in skeletons]),
            avg_total_word_count=self._safe_mean([s.get('total_word_count', 0) for s in skeletons]),
            avg_duration_seconds=self._safe_mean([s.get('estimated_duration_seconds', 0) for s in skeletons]),
        )

    def _calc_stats(self, username: str, skeletons: list[dict]) -> CreatorStats:
        platform = skeletons[0].get('platform', 'unknown')
        total_views = sum(s.get('views', 0) for s in skeletons)
        total_likes = sum(s.get('likes', 0) for s in skeletons)
        count = len(skeletons)
        return CreatorStats(
            username=username, platform=platform, video_count=count,
            total_views=total_views, total_likes=total_likes,
            avg_views=total_views / count if count else 0,
            avg_likes=total_likes / count if count else 0,
            avg_hook_word_count=self._safe_mean([s.get('hook_word_count', 0) for s in skeletons]),
            avg_total_word_count=self._safe_mean([s.get('total_word_count', 0) for s in skeletons]),
            avg_duration_seconds=self._safe_mean([s.get('estimated_duration_seconds', 0) for s in skeletons]),
            hook_techniques=self._count(skeletons, 'hook_technique'),
            value_structures=self._count(skeletons, 'value_structure'),
            cta_types=self._count(skeletons, 'cta_type'),
        )

    def _count(self, skeletons: list[dict], field: str) -> dict[str, int]:
        counts = defaultdict(int)
        for s in skeletons:
            counts[s.get(field, 'unknown')] += 1
        return dict(counts)

    def _safe_mean(self, values: list) -> float:
        filtered = [v for v in values if v and v > 0]
        return mean(filtered) if filtered else 0.0


def get_top_pattern(counts: dict[str, int]) -> Optional[str]:
    return max(counts, key=counts.get) if counts else None


def format_aggregation_summary(data: AggregatedData) -> str:
    lines = [
        f"# Aggregation Summary", "",
        f"**Total Videos:** {data.total_videos}",
        f"**Total Views:** {data.total_views:,}",
        f"**Creators:** {len(data.creator_stats)}", "",
        f"## Averages",
        f"- Hook word count: {data.avg_hook_word_count:.1f}",
        f"- Total word count: {data.avg_total_word_count:.1f}",
        f"- Duration: {data.avg_duration_seconds:.1f}s",
    ]
    return "\n".join(lines)
