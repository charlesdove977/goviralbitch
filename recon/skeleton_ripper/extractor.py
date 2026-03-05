"""
Batched content skeleton extractor with smart retry logic.
Ported from ReelRecon — imports adjusted.
"""

import json
import re
import traceback
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from .llm_client import LLMClient
from .prompts import get_extraction_prompt, validate_skeleton
from recon.utils.logger import get_logger

logger = get_logger()


@dataclass
class ExtractionResult:
    video_id: str
    success: bool
    skeleton: Optional[dict] = None
    error: Optional[str] = None


@dataclass
class BatchExtractionResult:
    successful: list[dict] = field(default_factory=list)
    failed_video_ids: list[str] = field(default_factory=list)
    total_attempts: int = 0


class BatchedExtractor:
    DEFAULT_BATCH_SIZE = 4
    MAX_RETRIES = 2

    def __init__(self, llm_client: LLMClient, batch_size: int = DEFAULT_BATCH_SIZE, max_retries: int = MAX_RETRIES):
        self.llm_client = llm_client
        self.batch_size = min(max(batch_size, 1), 5)
        self.max_retries = max_retries

    def extract_all(self, transcripts: list[dict], on_progress: Optional[callable] = None) -> BatchExtractionResult:
        result = BatchExtractionResult()
        total = len(transcripts)
        batches = [transcripts[i:i + self.batch_size] for i in range(0, len(transcripts), self.batch_size)]

        for batch_idx, batch in enumerate(batches):
            batch_result = self._extract_batch_with_retry(batch)
            result.successful.extend(batch_result.successful)
            result.failed_video_ids.extend(batch_result.failed_video_ids)
            result.total_attempts += batch_result.total_attempts
            if on_progress:
                on_progress(len(result.successful), total, batch_idx + 1, len(batches))

        return result

    def _extract_batch_with_retry(self, batch: list[dict], attempt: int = 0) -> BatchExtractionResult:
        result = BatchExtractionResult()
        result.total_attempts = 1

        if not batch:
            return result

        try:
            prompt = get_extraction_prompt(batch)
            response = self.llm_client.complete(prompt, temperature=0)
            parsed = self._parse_response(response)

            if parsed is None:
                raise json.JSONDecodeError("Failed to parse response", response, 0)

            for skeleton in parsed:
                is_valid, error = validate_skeleton(skeleton)
                if is_valid:
                    video_id = skeleton.get('video_id')
                    original = next((t for t in batch if t.get('video_id') == video_id), None)
                    if original:
                        skeleton['creator_username'] = original.get('username', 'unknown')
                        skeleton['platform'] = original.get('platform', 'unknown')
                        skeleton['views'] = original.get('views', 0)
                        skeleton['likes'] = original.get('likes', 0)
                        skeleton['url'] = original.get('url', '')
                        skeleton['video_url'] = original.get('video_url', '')
                        skeleton['transcript'] = original.get('transcript', '')
                        skeleton['extracted_at'] = datetime.utcnow().isoformat()
                        skeleton['extraction_model'] = f"{self.llm_client.provider}/{self.llm_client.model}"
                    result.successful.append(skeleton)
                else:
                    result.failed_video_ids.append(skeleton.get('video_id', 'unknown'))

            return result

        except json.JSONDecodeError:
            return self._handle_parse_failure(batch, attempt)
        except Exception as e:
            logger.error("EXTRACT", f"Batch extraction error: {e}")
            result.failed_video_ids = [t.get('video_id', 'unknown') for t in batch]
            return result

    def _handle_parse_failure(self, batch: list[dict], attempt: int) -> BatchExtractionResult:
        result = BatchExtractionResult()
        if attempt >= self.max_retries:
            result.failed_video_ids = [t.get('video_id', 'unknown') for t in batch]
            return result

        if len(batch) > 1:
            mid = len(batch) // 2
            first_result = self._extract_batch_with_retry(batch[:mid], attempt + 1)
            second_result = self._extract_batch_with_retry(batch[mid:], attempt + 1)
            result.successful = first_result.successful + second_result.successful
            result.failed_video_ids = first_result.failed_video_ids + second_result.failed_video_ids
            result.total_attempts = first_result.total_attempts + second_result.total_attempts
        else:
            result.failed_video_ids.append(batch[0].get('video_id', 'unknown'))

        return result

    def _parse_response(self, response: str) -> Optional[list[dict]]:
        text = response.strip()
        if '```' in text:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if match:
                text = match.group(1).strip()
        text = text.strip()
        if not text.startswith('[') and not text.startswith('{'):
            array_start = text.find('[')
            obj_start = text.find('{')
            if array_start >= 0 and (obj_start < 0 or array_start < obj_start):
                text = text[array_start:]
            elif obj_start >= 0:
                text = text[obj_start:]
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                parsed = [parsed]
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return None
