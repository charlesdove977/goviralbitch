"""
Main pipeline orchestration for Content Skeleton Ripper.
Ported from ReelRecon — uses InstaClient instead of cookie-based session.
"""

import os
import json
import uuid
import time
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from enum import Enum

from .cache import TranscriptCache, is_valid_transcript
from .llm_client import LLMClient
from .extractor import BatchedExtractor
from .aggregator import SkeletonAggregator, AggregatedData
from .synthesizer import PatternSynthesizer, SynthesisResult, generate_report
from recon.utils.logger import get_logger

# Import recon scrapers (replaces ReelRecon's cookie-based scraper)
from recon.scraper.instagram import InstaClient
from recon.scraper.downloader import (
    transcribe_video_openai,
    transcribe_video_local,
    load_whisper_model,
    download_direct,
    WHISPER_AVAILABLE,
)
from recon.config import load_config

logger = get_logger()

RECON_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "recon"


class JobStatus(Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    TRANSCRIBING = "transcribing"
    EXTRACTING = "extracting"
    AGGREGATING = "aggregating"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class JobProgress:
    status: JobStatus = JobStatus.PENDING
    phase: str = ""
    message: str = ""
    videos_scraped: int = 0
    videos_downloaded: int = 0
    videos_transcribed: int = 0
    transcripts_from_cache: int = 0
    valid_transcripts: int = 0
    skeletons_extracted: int = 0
    total_target: int = 0
    current_creator: str = ""
    current_creator_index: int = 0
    total_creators: int = 0
    reels_fetched: int = 0
    current_video_index: int = 0
    extraction_batch: int = 0
    extraction_total_batches: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    errors: list[str] = field(default_factory=list)


@dataclass
class JobConfig:
    usernames: list[str]
    videos_per_creator: int = 3
    platform: str = "instagram"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    min_valid_ratio: float = 0.6
    transcribe_provider: str = "openai"
    whisper_model: str = "small.en"
    openai_api_key: Optional[str] = None


@dataclass
class JobResult:
    job_id: str
    success: bool
    config: JobConfig
    progress: JobProgress
    skeletons: list[dict] = field(default_factory=list)
    aggregated: Optional[AggregatedData] = None
    synthesis: Optional[SynthesisResult] = None
    report_path: Optional[str] = None
    skeletons_path: Optional[str] = None
    synthesis_path: Optional[str] = None


class SkeletonRipperPipeline:
    """
    Main pipeline — uses InstaClient (Instaloader) for IG scraping.
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = str(RECON_DATA_DIR)
        self.base_dir = Path(base_dir)
        self.output_dir = RECON_DATA_DIR / 'reports'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache = TranscriptCache()
        logger.info("PIPELINE", f"SkeletonRipperPipeline initialized")

    def run(self, config: JobConfig, on_progress: Optional[Callable[[JobProgress], None]] = None) -> JobResult:
        job_id = f"sr_{uuid.uuid4().hex[:8]}"
        progress = JobProgress(
            status=JobStatus.PENDING,
            started_at=datetime.utcnow().isoformat(),
            total_target=len(config.usernames) * config.videos_per_creator,
            total_creators=len(config.usernames)
        )
        result = JobResult(job_id=job_id, success=False, config=config, progress=progress)

        try:
            llm_client = LLMClient(provider=config.llm_provider, model=config.llm_model)

            # Stage 1: Scrape and transcribe
            progress.status = JobStatus.SCRAPING
            progress.phase = "Scraping videos..."
            self._notify(on_progress, progress)

            transcripts = self._scrape_and_transcribe(config=config, progress=progress, on_progress=on_progress)

            valid_count = sum(1 for t in transcripts if is_valid_transcript(t.get('transcript', '')))
            progress.valid_transcripts = valid_count

            if valid_count == 0:
                raise ValueError("No valid transcripts to process")

            valid_transcripts = [t for t in transcripts if is_valid_transcript(t.get('transcript', ''))]

            # Stage 2: Extraction
            progress.status = JobStatus.EXTRACTING
            progress.phase = "Extracting content skeletons..."
            self._notify(on_progress, progress)

            extractor = BatchedExtractor(llm_client)
            extraction_result = extractor.extract_all(
                valid_transcripts,
                on_progress=lambda done, total, batch, total_batches: self._update_extraction_progress(
                    progress, done, total, batch, total_batches, on_progress
                )
            )
            result.skeletons = extraction_result.successful
            progress.skeletons_extracted = len(extraction_result.successful)

            if not result.skeletons:
                raise ValueError("No skeletons extracted successfully")

            # Stage 3: Aggregation
            progress.status = JobStatus.AGGREGATING
            progress.phase = "Aggregating patterns..."
            self._notify(on_progress, progress)

            aggregator = SkeletonAggregator()
            result.aggregated = aggregator.aggregate(result.skeletons)

            # Stage 4: Synthesis
            progress.status = JobStatus.SYNTHESIZING
            progress.phase = "Synthesizing content strategy..."
            self._notify(on_progress, progress)

            synthesizer = PatternSynthesizer(llm_client)
            result.synthesis = synthesizer.synthesize(result.aggregated)

            # Stage 5: Output
            output_paths = self._save_outputs(job_id, config, result)
            result.report_path = output_paths.get('report')
            result.skeletons_path = output_paths.get('skeletons')
            result.synthesis_path = output_paths.get('synthesis')

            progress.status = JobStatus.COMPLETE
            progress.phase = "Analysis Complete"
            progress.message = f"Done: {len(result.skeletons)} skeletons from {len(config.usernames)} creator(s)"
            progress.completed_at = datetime.utcnow().isoformat()
            result.success = True

        except Exception as e:
            logger.error("SKELETON", f"Pipeline failed: {e}")
            progress.status = JobStatus.FAILED
            progress.phase = "Failed"
            progress.errors.append(str(e))
            progress.completed_at = datetime.utcnow().isoformat()

        self._notify(on_progress, progress)
        return result

    def _scrape_and_transcribe(self, config: JobConfig, progress: JobProgress, on_progress: Optional[Callable]) -> list[dict]:
        """Scrape videos and get transcripts using Instaloader for IG."""
        transcripts = []
        openai_key = config.openai_api_key or os.getenv('OPENAI_API_KEY')

        # Load local Whisper if needed
        whisper_model = None
        if config.transcribe_provider == 'local' and WHISPER_AVAILABLE:
            progress.message = f"Loading Whisper model ({config.whisper_model})..."
            self._notify(on_progress, progress)
            whisper_model = load_whisper_model(config.whisper_model)
            if not whisper_model:
                config.transcribe_provider = 'openai'

        # Setup InstaClient for IG competitors
        insta_client = None
        if config.platform == 'instagram':
            recon_config = load_config()
            if recon_config.ig_username and recon_config.ig_password:
                insta_client = InstaClient()
                if not insta_client.login(recon_config.ig_username, recon_config.ig_password):
                    raise RuntimeError("Instagram login failed. Check IG_USERNAME/IG_PASSWORD.")
            else:
                raise RuntimeError("IG credentials not configured. Set IG_USERNAME and IG_PASSWORD env vars or run settings.")

        temp_dir = RECON_DATA_DIR / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)

        for idx, username in enumerate(config.usernames):
            progress.current_creator = username
            progress.current_creator_index = idx + 1
            progress.current_video_index = 0
            progress.phase = f"Processing @{username} ({idx + 1}/{len(config.usernames)})"
            progress.message = "Checking cache..."
            self._notify(on_progress, progress)

            # Check cache first
            cached = self._get_cached_transcripts(config.platform, username, config.videos_per_creator)
            if cached and len(cached) >= config.videos_per_creator:
                progress.transcripts_from_cache += len(cached[:config.videos_per_creator])
                transcripts.extend(cached[:config.videos_per_creator])
                continue

            # Fetch reel metadata
            progress.message = f"Fetching reels from @{username}..."
            self._notify(on_progress, progress)

            if config.platform == 'instagram' and insta_client:
                reels = insta_client.get_competitor_reels(username, max_reels=100)
                if not reels:
                    progress.errors.append(f"@{username}: No reels found")
                    continue
                progress.videos_scraped += len(reels)
                progress.reels_fetched = len(reels)
            else:
                progress.errors.append(f"@{username}: Platform {config.platform} not yet supported in pipeline")
                continue

            # Iterate through reels until we have enough valid transcripts
            valid_count = 0
            for reel in reels:
                if valid_count >= config.videos_per_creator:
                    break

                video_id = reel.get('shortcode', 'unknown')
                views_display = f"{reel.get('views', 0):,}"

                # Check cache
                cached_text = self.cache.get(config.platform, username, video_id)
                if cached_text and is_valid_transcript(cached_text):
                    valid_count += 1
                    transcripts.append({
                        'video_id': video_id, 'username': username,
                        'platform': config.platform, 'views': reel.get('views', 0),
                        'likes': reel.get('likes', 0), 'url': reel.get('url', ''),
                        'video_url': reel.get('video_url', ''),
                        'transcript': cached_text, 'from_cache': True
                    })
                    progress.transcripts_from_cache += 1
                    progress.videos_transcribed += 1
                    continue

                # Download and transcribe
                progress.message = f"Video {valid_count + 1}/{config.videos_per_creator}: Downloading ({views_display} views)"
                self._notify(on_progress, progress)

                video_path = temp_dir / f"{username}_{video_id}.mp4"
                video_url = reel.get('video_url', '')

                downloaded = False
                if video_url:
                    downloaded = download_direct(video_url, video_path)
                if not downloaded and insta_client:
                    downloaded = insta_client.download_reel(video_id, video_path)

                if not downloaded or not video_path.exists():
                    continue

                progress.videos_downloaded += 1
                progress.message = f"Video {valid_count + 1}/{config.videos_per_creator}: Transcribing ({views_display} views)"
                self._notify(on_progress, progress)

                # Transcribe
                transcript_text = None
                if config.transcribe_provider == 'openai' and openai_key:
                    transcript_text = transcribe_video_openai(str(video_path), openai_key)
                elif whisper_model:
                    transcript_text = transcribe_video_local(str(video_path), whisper_model)

                # Cleanup video
                try:
                    if video_path.exists():
                        video_path.unlink()
                except OSError:
                    pass

                if transcript_text and is_valid_transcript(transcript_text):
                    self.cache.set(config.platform, username, video_id, transcript_text)
                    transcripts.append({
                        'video_id': video_id, 'username': username,
                        'platform': config.platform, 'views': reel.get('views', 0),
                        'likes': reel.get('likes', 0), 'url': reel.get('url', ''),
                        'video_url': reel.get('video_url', ''),
                        'transcript': transcript_text, 'from_cache': False
                    })
                    valid_count += 1
                    progress.videos_transcribed += 1

            if valid_count < config.videos_per_creator:
                progress.errors.append(f"@{username}: Only {valid_count}/{config.videos_per_creator} valid transcripts")

        return transcripts

    def _get_cached_transcripts(self, platform: str, username: str, count: int) -> list[dict]:
        cached = []
        cache_pattern = f"{platform.lower()}_{username.lower()}_*.txt"
        cache_files = list(self.cache.cache_dir.glob(cache_pattern))
        for cache_file in cache_files[:count]:
            try:
                transcript_text = cache_file.read_text(encoding='utf-8')
                if is_valid_transcript(transcript_text):
                    parts = cache_file.stem.split('_')
                    video_id = parts[-1] if len(parts) >= 3 else cache_file.stem
                    cached.append({
                        'video_id': video_id, 'username': username,
                        'platform': platform, 'views': 0, 'likes': 0,
                        'url': '', 'transcript': transcript_text, 'from_cache': True
                    })
            except Exception:
                pass
        return cached

    def _update_extraction_progress(self, progress, done, total, batch, total_batches, on_progress):
        progress.skeletons_extracted = done
        progress.extraction_batch = batch
        progress.extraction_total_batches = total_batches
        progress.message = f"Extracting: batch {batch}/{total_batches} ({done}/{total} done)"
        self._notify(on_progress, progress)

    def _notify(self, callback, progress):
        if callback:
            try:
                callback(progress)
            except Exception:
                pass

    def _save_outputs(self, job_id: str, config: JobConfig, result: JobResult) -> dict[str, str]:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        job_dir = self.output_dir / f"{timestamp}_{job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        paths = {}

        skeletons_path = job_dir / 'skeletons.json'
        with open(skeletons_path, 'w', encoding='utf-8') as f:
            json.dump(result.skeletons, f, indent=2, default=str)
        paths['skeletons'] = str(skeletons_path)

        if result.synthesis:
            synthesis_path = job_dir / 'synthesis.json'
            with open(synthesis_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'success': result.synthesis.success,
                    'analysis': result.synthesis.analysis,
                    'templates': result.synthesis.templates,
                    'quick_wins': result.synthesis.quick_wins,
                    'warnings': result.synthesis.warnings,
                    'model_used': result.synthesis.model_used,
                    'synthesized_at': result.synthesis.synthesized_at
                }, f, indent=2)
            paths['synthesis'] = str(synthesis_path)

        if result.aggregated and result.synthesis:
            report_path = job_dir / 'report.md'
            report_content = generate_report(
                data=result.aggregated, synthesis=result.synthesis,
                job_config=asdict(config)
            )
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            paths['report'] = str(report_path)

        return paths


def create_job_config(
    usernames: list[str], videos_per_creator: int = 3, platform: str = "instagram",
    llm_provider: str = "openai", llm_model: str = "gpt-4o-mini",
    transcribe_provider: str = "openai", whisper_model: str = "small.en",
    openai_api_key: Optional[str] = None
) -> JobConfig:
    return JobConfig(
        usernames=usernames, videos_per_creator=videos_per_creator,
        platform=platform, llm_provider=llm_provider, llm_model=llm_model,
        transcribe_provider=transcribe_provider, whisper_model=whisper_model,
        openai_api_key=openai_api_key
    )


def run_skeleton_ripper(
    usernames: list[str], videos_per_creator: int = 3, platform: str = "instagram",
    llm_provider: str = "openai", llm_model: str = "gpt-4o-mini",
    transcribe_provider: str = "openai", whisper_model: str = "small.en",
    openai_api_key: Optional[str] = None, on_progress: Optional[Callable] = None
) -> JobResult:
    config = create_job_config(
        usernames=usernames, videos_per_creator=videos_per_creator,
        platform=platform, llm_provider=llm_provider, llm_model=llm_model,
        transcribe_provider=transcribe_provider, whisper_model=whisper_model,
        openai_api_key=openai_api_key
    )
    pipeline = SkeletonRipperPipeline()
    return pipeline.run(config, on_progress=on_progress)
