"""
Recon — Configuration module.
Reads competitor list from agent-brain.json, manages credentials and API keys.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass


PIPELINE_DIR = Path(__file__).parent.parent
DATA_DIR = PIPELINE_DIR / "data"
RECON_DATA_DIR = DATA_DIR / "recon"
CREDENTIALS_FILE = RECON_DATA_DIR / ".credentials"
BRAIN_FILE = DATA_DIR / "agent-brain.json"


@dataclass
class Competitor:
    """A competitor from the agent brain."""
    name: str
    platform: str
    handle: str
    why_watch: str


@dataclass
class ReconConfig:
    """Full configuration for a recon session."""
    competitors: List[Competitor]
    ig_username: Optional[str] = None
    ig_password: Optional[str] = None
    openai_api_key: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    transcribe_provider: str = "openai"
    whisper_model: str = "small.en"


def load_competitors() -> List[Competitor]:
    """Load competitor list from agent-brain.json."""
    if not BRAIN_FILE.exists():
        return []

    with open(BRAIN_FILE, 'r', encoding='utf-8') as f:
        brain = json.load(f)

    raw = brain.get("competitors", [])
    competitors = []
    for c in raw:
        competitors.append(Competitor(
            name=c.get("name", ""),
            platform=c.get("platform", "").lower(),
            handle=c.get("handle", ""),
            why_watch=c.get("why_watch", ""),
        ))

    return competitors


def load_credentials() -> Dict[str, str]:
    """
    Load credentials from environment variables or .credentials file.
    Priority: env vars > .credentials file.
    """
    creds = {}

    # Try .credentials file first
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    creds[key.strip()] = value.strip()

    # Environment variables override
    env_map = {
        "IG_USERNAME": "ig_username",
        "IG_PASSWORD": "ig_password",
        "OPENAI_API_KEY": "openai_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "GOOGLE_API_KEY": "google_api_key",
    }

    for env_var, cred_key in env_map.items():
        val = os.environ.get(env_var)
        if val:
            creds[cred_key] = val

    return creds


def save_credentials(creds: Dict[str, str]):
    """Save credentials to .credentials file."""
    RECON_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, 'w') as f:
        f.write("# Recon credentials — DO NOT COMMIT\n")
        for key, value in creds.items():
            f.write(f"{key}={value}\n")


def load_config() -> ReconConfig:
    """Load full recon configuration."""
    competitors = load_competitors()
    creds = load_credentials()

    return ReconConfig(
        competitors=competitors,
        ig_username=creds.get("ig_username") or creds.get("IG_USERNAME"),
        ig_password=creds.get("ig_password") or creds.get("IG_PASSWORD"),
        openai_api_key=creds.get("openai_api_key") or creds.get("OPENAI_API_KEY"),
        llm_provider=creds.get("llm_provider", "openai"),
        llm_model=creds.get("llm_model", "gpt-4o-mini"),
        transcribe_provider=creds.get("transcribe_provider", "openai"),
        whisper_model=creds.get("whisper_model", "small.en"),
    )


def get_ig_competitors() -> List[Competitor]:
    """Get only Instagram competitors."""
    return [c for c in load_competitors() if c.platform == "instagram"]


def get_yt_competitors() -> List[Competitor]:
    """Get only YouTube competitors."""
    return [c for c in load_competitors() if c.platform == "youtube"]
