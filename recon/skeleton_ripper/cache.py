"""
Transcript caching for Content Skeleton Ripper.
Ported from ReelRecon — cache dir adjusted to data/recon/cache/.
"""

import os
from pathlib import Path
from typing import Optional
from recon.utils.logger import get_logger

logger = get_logger()

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "recon" / "cache"

MIN_TRANSCRIPT_WORDS = 10
MIN_VALID_RATIO = 0.6


class TranscriptCache:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            self.cache_dir = CACHE_DIR
        else:
            self.cache_dir = Path(base_dir) / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("CACHE", f"Transcript cache at: {self.cache_dir}")

    def _get_cache_path(self, platform: str, username: str, video_id: str) -> Path:
        safe_platform = platform.lower().replace('/', '_').replace('\\', '_')
        safe_username = username.lower().replace('/', '_').replace('\\', '_')
        safe_video_id = video_id.replace('/', '_').replace('\\', '_')
        return self.cache_dir / f"{safe_platform}_{safe_username}_{safe_video_id}.txt"

    def get(self, platform: str, username: str, video_id: str) -> Optional[str]:
        cache_path = self._get_cache_path(platform, username, video_id)
        if cache_path.exists():
            try:
                transcript = cache_path.read_text(encoding='utf-8')
                if transcript.strip():
                    logger.debug("CACHE", f"HIT: {platform}/{username}/{video_id}")
                    return transcript
            except Exception as e:
                logger.warning("CACHE", f"Read error for {video_id}: {e}")
        return None

    def set(self, platform: str, username: str, video_id: str,
            transcript: str, validate: bool = True) -> bool:
        if validate and not is_valid_transcript(transcript):
            return False
        cache_path = self._get_cache_path(platform, username, video_id)
        try:
            cache_path.write_text(transcript, encoding='utf-8')
            return True
        except Exception as e:
            logger.warning("CACHE", f"Write error for {video_id}: {e}")
            return False

    def exists(self, platform: str, username: str, video_id: str) -> bool:
        cache_path = self._get_cache_path(platform, username, video_id)
        return cache_path.exists() and cache_path.stat().st_size > 0

    def clear_all(self) -> int:
        files = list(self.cache_dir.glob('*.txt'))
        for f in files:
            f.unlink()
        return len(files)

    def clear_for_username(self, platform: str, username: str) -> int:
        pattern = f"{platform.lower()}_{username.lower()}_*.txt"
        files = list(self.cache_dir.glob(pattern))
        for f in files:
            f.unlink()
        return len(files)

    def get_stats(self) -> dict:
        if not self.cache_dir.exists():
            return {'total_files': 0, 'total_size_mb': 0}
        files = list(self.cache_dir.glob('*.txt'))
        total_size = sum(f.stat().st_size for f in files)
        return {
            'total_files': len(files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }


def is_valid_transcript(transcript: str) -> bool:
    if not transcript or not transcript.strip():
        return False
    word_count = len(transcript.split())
    return word_count >= MIN_TRANSCRIPT_WORDS


def check_transcript_validity(transcripts: list[dict]) -> tuple[int, int, bool]:
    total = len(transcripts)
    valid = sum(1 for t in transcripts if is_valid_transcript(t.get('transcript', '')))
    ratio = valid / total if total > 0 else 0
    return valid, total, ratio >= MIN_VALID_RATIO
