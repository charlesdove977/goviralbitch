"""
Recon — Video download + transcription module.
Extracted from ReelRecon's scraper/core.py.
Supports OpenAI Whisper API (default) and local Whisper (fallback).
"""

import os
import time
import threading
from pathlib import Path
from typing import Optional, Callable

import requests

from recon.utils.logger import get_logger

logger = get_logger()

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "recon"

# Optional: local Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


def transcribe_video_openai(
    video_path: str,
    api_key: str,
    output_path: Optional[str] = None,
    max_retries: int = 3,
) -> Optional[str]:
    """
    Transcribe video using OpenAI Whisper API.

    Args:
        video_path: Path to the video/audio file
        api_key: OpenAI API key
        output_path: Optional path to save transcript text
        max_retries: Max retry attempts

    Returns:
        Transcript text, or None on failure
    """
    video_name = os.path.basename(str(video_path))
    url = "https://api.openai.com/v1/audio/transcriptions"

    logger.debug("TRANSCRIBE", f"Starting OpenAI transcription: {video_name}")

    for attempt in range(max_retries):
        try:
            with open(video_path, 'rb') as audio_file:
                files = {'file': (os.path.basename(video_path), audio_file, 'video/mp4')}
                data = {'model': 'whisper-1', 'language': 'en', 'response_format': 'text'}
                headers = {'Authorization': f'Bearer {api_key}'}

                response = requests.post(url, headers=headers, files=files, data=data, timeout=300)

                if response.status_code == 200:
                    transcript = response.text.strip()
                    logger.info("TRANSCRIBE", f"OpenAI transcription complete: {video_name}", {
                        "transcript_length": len(transcript),
                        "attempts": attempt + 1
                    })
                    if output_path and transcript:
                        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(transcript)
                    return transcript

                elif response.status_code == 429:
                    logger.warning("TRANSCRIBE", f"Rate limited for {video_name}, waiting...")
                    time.sleep(5 * (attempt + 1))
                elif response.status_code >= 500:
                    logger.warning("TRANSCRIBE", f"Server error {response.status_code}")
                    time.sleep(2 ** attempt)
                else:
                    logger.error("TRANSCRIBE", f"API error for {video_name}", {
                        "status_code": response.status_code,
                        "response": response.text[:200] if response.text else None
                    })
                    return None

        except requests.exceptions.Timeout:
            logger.warning("TRANSCRIBE", f"Timeout for {video_name} (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.error("TRANSCRIBE", f"Exception for {video_name}", exception=e)
            if attempt < max_retries - 1:
                time.sleep(2)

    logger.error("TRANSCRIBE", f"Failed after {max_retries} attempts: {video_name}")
    return None


def transcribe_video_local(
    video_path: str,
    model,
    output_path: Optional[str] = None,
    progress_callback: Optional[Callable] = None,
    video_index: Optional[int] = None,
    total_videos: Optional[int] = None,
) -> Optional[str]:
    """
    Transcribe video using local Whisper model with heartbeat updates.

    Args:
        video_path: Path to the video/audio file
        model: Loaded Whisper model
        output_path: Optional path to save transcript text
        progress_callback: Optional progress callback
        video_index: Current video index (for progress)
        total_videos: Total videos (for progress)

    Returns:
        Transcript text, or None on failure
    """
    video_name = os.path.basename(str(video_path))
    logger.debug("TRANSCRIBE", f"Starting local transcription: {video_name}")

    stop_heartbeat = threading.Event()
    start_time = time.time()

    def heartbeat():
        tick = 0
        while not stop_heartbeat.is_set():
            stop_heartbeat.wait(5)
            if not stop_heartbeat.is_set():
                tick += 1
                elapsed = int(time.time() - start_time)
                prefix = f"{video_index}/{total_videos}" if video_index and total_videos else ""
                if progress_callback:
                    progress_callback(f"Transcribing {prefix} - {elapsed}s elapsed...")

    heartbeat_thread = None
    if progress_callback:
        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()

    try:
        result = model.transcribe(str(video_path), language="en")
        transcript = result["text"].strip()

        if output_path and transcript:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcript)

        elapsed = int(time.time() - start_time)
        logger.info("TRANSCRIBE", f"Local transcription complete: {video_name}", {
            "transcript_length": len(transcript) if transcript else 0,
            "elapsed_seconds": elapsed
        })
        return transcript

    except Exception as e:
        logger.error("TRANSCRIBE", f"Local transcription failed: {video_name}", exception=e)
        return None
    finally:
        stop_heartbeat.set()
        if heartbeat_thread:
            heartbeat_thread.join(timeout=1)


def load_whisper_model(model_name: str = 'small.en', max_retries: int = 3) -> Optional[object]:
    """Load local Whisper model with retry logic."""
    if not WHISPER_AVAILABLE:
        logger.warning("WHISPER", "whisper not available — install with: pip install openai-whisper")
        return None

    import torch

    device = "cpu"
    cache_dir = str(Path.home() / '.cache' / 'whisper')

    logger.info("WHISPER", f"Loading model '{model_name}'", {
        "cache_dir": cache_dir, "device": device
    })

    for attempt in range(max_retries):
        try:
            model = whisper.load_model(model_name, device=device, download_root=cache_dir)
            if model is not None:
                logger.info("WHISPER", f"Model '{model_name}' loaded successfully")
                return model
        except Exception as e:
            logger.warning("WHISPER", f"Load attempt {attempt + 1} failed", {
                "error": str(e)[:200]
            })
            if attempt < max_retries - 1:
                time.sleep(1)

    logger.error("WHISPER", f"All {max_retries} attempts to load model failed")
    return None


def download_direct(url: str, output_path: Path, max_retries: int = 3) -> bool:
    """Download a file directly from URL with retries."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, stream=True, timeout=120)
            if resp.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info("DOWNLOAD", f"Direct download successful", {
                        "file_size": output_path.stat().st_size
                    })
                    return True
        except requests.exceptions.Timeout:
            logger.warning("DOWNLOAD", f"Timeout (attempt {attempt + 1})")
        except Exception as e:
            logger.warning("DOWNLOAD", f"Error (attempt {attempt + 1}): {e}")

        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)

    return False
