"""
Recon — Lightweight state manager for tracking scrape/analysis jobs.
Simplified from ReelRecon's state_manager — stores state as JSON files.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class JobPhase(Enum):
    IDLE = "idle"
    SCRAPING = "scraping"
    TRANSCRIBING = "transcribing"
    EXTRACTING = "extracting"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"


class StateManager:
    """Manages persistent job state for recon operations."""

    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or Path(__file__).parent.parent.parent / "data" / "recon" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_job_state(self, job_id: str, state: Dict[str, Any]):
        path = self.state_dir / f"{job_id}.json"
        state["updated_at"] = datetime.utcnow().isoformat()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, default=str)

    def load_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        path = self.state_dir / f"{job_id}.json"
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_jobs(self) -> list:
        jobs = []
        for f in self.state_dir.glob("*.json"):
            try:
                with open(f, 'r') as fh:
                    data = json.load(fh)
                    jobs.append({
                        "job_id": f.stem,
                        "phase": data.get("phase", "unknown"),
                        "updated_at": data.get("updated_at")
                    })
            except Exception:
                pass
        return sorted(jobs, key=lambda x: x.get("updated_at", ""), reverse=True)
