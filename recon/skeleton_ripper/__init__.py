"""
Content Skeleton Ripper — Multi-creator content pattern analysis.
Ported from ReelRecon with imports adjusted for content-pipeline.

Usage:
    from recon.skeleton_ripper import SkeletonRipperPipeline, create_job_config

    config = create_job_config(
        usernames=['creator1', 'creator2'],
        videos_per_creator=3,
        llm_provider='openai',
        llm_model='gpt-4o-mini'
    )

    pipeline = SkeletonRipperPipeline()
    result = pipeline.run(config)
"""

from .pipeline import (
    SkeletonRipperPipeline,
    JobConfig,
    JobProgress,
    JobResult,
    JobStatus,
    create_job_config,
    run_skeleton_ripper,
)
from .extractor import BatchedExtractor
from .synthesizer import PatternSynthesizer
from .aggregator import SkeletonAggregator
from .cache import TranscriptCache
from .llm_client import LLMClient, get_available_providers

__all__ = [
    'SkeletonRipperPipeline',
    'JobConfig', 'JobProgress', 'JobResult', 'JobStatus',
    'create_job_config', 'run_skeleton_ripper',
    'BatchedExtractor', 'PatternSynthesizer', 'SkeletonAggregator',
    'TranscriptCache', 'LLMClient', 'get_available_providers',
]
