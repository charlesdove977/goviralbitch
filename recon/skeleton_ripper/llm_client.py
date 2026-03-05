"""
Multi-provider LLM client for Content Skeleton Ripper.
Ported from ReelRecon — imports adjusted.
"""

import os
import json
import time
import traceback
import requests
from dataclasses import dataclass
from typing import Optional
from recon.utils.logger import get_logger

logger = get_logger()


@dataclass
class ModelInfo:
    id: str
    name: str
    cost_tier: str


@dataclass
class ProviderConfig:
    id: str
    name: str
    api_key_env: str
    base_url: str
    models: list[ModelInfo]


PROVIDERS = {
    'openai': ProviderConfig(
        id='openai', name='OpenAI', api_key_env='OPENAI_API_KEY',
        base_url='https://api.openai.com/v1',
        models=[
            ModelInfo('gpt-4o-mini', 'GPT-4o Mini (Recommended)', 'low'),
            ModelInfo('gpt-4o', 'GPT-4o', 'medium'),
        ]
    ),
    'anthropic': ProviderConfig(
        id='anthropic', name='Anthropic', api_key_env='ANTHROPIC_API_KEY',
        base_url='https://api.anthropic.com/v1',
        models=[
            ModelInfo('claude-3-haiku-20240307', 'Claude 3 Haiku', 'low'),
            ModelInfo('claude-3-sonnet-20240229', 'Claude 3 Sonnet', 'medium'),
        ]
    ),
    'google': ProviderConfig(
        id='google', name='Google', api_key_env='GOOGLE_API_KEY',
        base_url='https://generativelanguage.googleapis.com/v1beta',
        models=[
            ModelInfo('gemini-1.5-flash', 'Gemini 1.5 Flash', 'low'),
            ModelInfo('gemini-1.5-pro', 'Gemini 1.5 Pro', 'medium'),
        ]
    ),
    'local': ProviderConfig(
        id='local', name='Local (Ollama)', api_key_env='',
        base_url='http://localhost:11434/api',
        models=[
            ModelInfo('qwen3', 'Qwen 3 (Recommended)', 'free'),
            ModelInfo('llama3', 'Llama 3', 'free'),
            ModelInfo('mistral', 'Mistral', 'free'),
        ]
    ),
}


class LLMClient:
    DEFAULT_MAX_RETRIES = 3
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self, provider: str, model: str, timeout: int = 120, max_retries: int = 3):
        if provider not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}. Valid: {list(PROVIDERS.keys())}")

        self.provider = provider
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.config = PROVIDERS[provider]

        self.api_key = None
        if self.config.api_key_env:
            self.api_key = os.getenv(self.config.api_key_env)
            if not self.api_key:
                raise ValueError(f"Missing API key. Set {self.config.api_key_env} env var.")

        logger.info("LLM", f"Client initialized: {provider}/{model}")

    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        return self.chat(system_prompt=None, user_prompt=prompt, temperature=temperature)

    def chat(self, user_prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                if self.provider == 'openai':
                    return self._call_openai(system_prompt, user_prompt, temperature)
                elif self.provider == 'anthropic':
                    return self._call_anthropic(system_prompt, user_prompt, temperature)
                elif self.provider == 'google':
                    return self._call_google(system_prompt, user_prompt, temperature)
                elif self.provider == 'local':
                    return self._call_ollama(system_prompt, user_prompt, temperature)
            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code if e.response is not None else 0
                if status_code in self.RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    delay = min(1.0 * (2 ** attempt), 30.0)
                    logger.warning("LLM", f"HTTP {status_code}, retrying in {delay:.1f}s")
                    time.sleep(delay)
                    continue
                raise
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(1.0 * (2 ** attempt), 30.0)
                    logger.warning("LLM", f"Connection error, retrying in {delay:.1f}s")
                    time.sleep(delay)
                    continue
                raise
            except Exception:
                raise

        raise last_exception or Exception("Max retries exceeded")

    def _call_openai(self, system_prompt, user_prompt, temperature):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        response = requests.post(
            f"{self.config.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages, "temperature": temperature},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    def _call_anthropic(self, system_prompt, user_prompt, temperature):
        payload = {
            "model": self.model, "max_tokens": 4096, "temperature": temperature,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt
        response = requests.post(
            f"{self.config.base_url}/messages",
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json=payload, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()['content'][0]['text']

    def _call_google(self, system_prompt, user_prompt, temperature):
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}" if system_prompt else user_prompt
        response = requests.post(
            f"{self.config.base_url}/models/{self.model}:generateContent?key={self.api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": full_prompt}]}], "generationConfig": {"temperature": temperature}},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']

    def _call_ollama(self, system_prompt, user_prompt, temperature):
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}" if system_prompt else user_prompt
        response = requests.post(
            f"{self.config.base_url}/generate",
            json={"model": self.model, "prompt": full_prompt, "stream": False, "options": {"temperature": temperature}},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()['response']


def get_available_providers() -> list[dict]:
    result = []
    for provider_id, config in PROVIDERS.items():
        available = False
        models = []
        if provider_id == 'local':
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=2)
                if response.status_code == 200:
                    available = True
                    data = response.json()
                    installed = {m['name'].split(':')[0] for m in data.get('models', [])}
                    models = [{'id': m.id, 'name': m.name, 'cost_tier': m.cost_tier}
                              for m in config.models if m.id in installed]
            except requests.exceptions.RequestException:
                pass
        else:
            api_key = os.getenv(config.api_key_env)
            if api_key:
                available = True
                models = [{'id': m.id, 'name': m.name, 'cost_tier': m.cost_tier} for m in config.models]
        result.append({'id': config.id, 'name': config.name, 'available': available, 'models': models})
    return result
