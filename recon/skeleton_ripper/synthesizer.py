"""
Pattern synthesizer for Content Skeleton Ripper.
Ported from ReelRecon — imports adjusted.
"""

import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .llm_client import LLMClient
from .prompts import get_synthesis_prompts
from .aggregator import AggregatedData
from recon.utils.logger import get_logger

logger = get_logger()


@dataclass
class SynthesisResult:
    success: bool
    analysis: str = ""
    templates: list[dict] = field(default_factory=list)
    quick_wins: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    model_used: str = ""
    tokens_used: int = 0
    synthesized_at: str = ""


class PatternSynthesizer:
    def __init__(self, llm_client: LLMClient, timeout: int = 180):
        self.llm_client = llm_client
        self.timeout = timeout

    def synthesize(self, data: AggregatedData, retry_on_failure: bool = True) -> SynthesisResult:
        if not data.skeletons:
            return SynthesisResult(success=False, error="No skeleton data to synthesize")

        try:
            system_prompt, user_prompt = get_synthesis_prompts(data.skeletons)
            response = self.llm_client.chat(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.7)
            result = self._parse_response(response)
            result.model_used = f"{self.llm_client.provider}/{self.llm_client.model}"
            result.synthesized_at = datetime.utcnow().isoformat()
            return result

        except Exception as e:
            logger.error("SYNTH", f"Synthesis failed: {e}")
            if retry_on_failure:
                try:
                    system_prompt, user_prompt = get_synthesis_prompts(data.skeletons)
                    response = self.llm_client.chat(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.7)
                    result = self._parse_response(response)
                    result.model_used = f"{self.llm_client.provider}/{self.llm_client.model}"
                    result.synthesized_at = datetime.utcnow().isoformat()
                    return result
                except Exception as retry_error:
                    logger.error("SYNTH", f"Retry failed: {retry_error}")

            return SynthesisResult(success=False, error=str(e))

    def _parse_response(self, response: str) -> SynthesisResult:
        result = SynthesisResult(success=True, analysis=response.strip())
        result.templates = self._extract_templates(response)
        result.quick_wins = self._extract_section_items(response, "Quick Wins")
        result.warnings = self._extract_section_items(response, "Warnings")
        return result

    def _extract_templates(self, text: str) -> list[dict]:
        templates = []
        current_template = None
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('## Template') or line.startswith('### Template'):
                if current_template:
                    templates.append(current_template)
                name = line.split(':', 1)[-1].strip() if ':' in line else line
                current_template = {'name': name, 'components': {}}
            elif current_template and line.startswith('**') and ':**' in line:
                parts = line.split(':**', 1)
                key = parts[0].replace('**', '').strip().lower()
                value = parts[1].strip() if len(parts) > 1 else ''
                current_template['components'][key] = value
        if current_template:
            templates.append(current_template)
        return templates

    def _extract_section_items(self, text: str, section_name: str) -> list[str]:
        items = []
        in_section = False
        for line in text.split('\n'):
            stripped = line.strip()
            if section_name.lower() in stripped.lower() and stripped.startswith('#'):
                in_section = True
                continue
            if in_section and stripped.startswith('#'):
                break
            if in_section and (stripped.startswith('-') or stripped.startswith('*')):
                item = stripped[1:].strip()
                if item:
                    items.append(item)
        return items


def generate_report(data: AggregatedData, synthesis: SynthesisResult, job_config: Optional[dict] = None) -> str:
    lines = [
        "# Content Skeleton Analysis Report", "",
        f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*", "",
    ]
    if job_config:
        lines.extend([
            "## Analysis Configuration",
            f"- **Creators analyzed:** {', '.join(job_config.get('usernames', []))}",
            f"- **Platform:** {job_config.get('platform', 'N/A')}",
            f"- **Videos per creator:** {job_config.get('videos_per_creator', 'N/A')}",
            f"- **LLM:** {synthesis.model_used}", "",
        ])
    lines.extend([
        "## Summary",
        f"- **Total videos analyzed:** {data.total_videos}",
        f"- **Total views:** {data.total_views:,}",
        f"- **Average hook length:** {data.avg_hook_word_count:.1f} words",
        f"- **Average video length:** {data.avg_duration_seconds:.0f} seconds", "",
        "---", "", synthesis.analysis, "",
        "---", "", "## Raw Skeletons Data", "",
        "See `skeletons.json` for full extracted skeleton data.", "",
    ])
    return "\n".join(lines)
