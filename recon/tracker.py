"""
Competitor content tracker — tracks which content has already been processed
to avoid duplicate topic creation across discovery runs.

State persisted in data/recon/tracker-state.json.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

PIPELINE_DIR = Path(__file__).parent.parent
STATE_FILE = PIPELINE_DIR / "data" / "recon" / "tracker-state.json"
BRAIN_FILE = PIPELINE_DIR / "data" / "agent-brain.json"


def load_state() -> Dict:
    """
    Load tracker state from JSON file.
    Returns empty dict if file doesn't exist.

    Structure: {competitor_handle: {content_id: timestamp_first_seen}}
    """
    if not STATE_FILE.exists():
        return {}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: Dict) -> None:
    """Write state to JSON file. Creates parent dirs if needed."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def filter_new_content(handle: str, content_items: List[Dict], state: Dict) -> List[Dict]:
    """
    Filter content items to only those not yet seen.

    Each content_item needs a unique key — uses 'url' or 'shortcode' field.
    Returns only items whose key is NOT in state[handle].
    Adds newly seen items to state[handle] with current timestamp.

    Args:
        handle: Competitor handle (e.g., "cooper.simson")
        content_items: List of content dicts with 'url' or 'shortcode' field
        state: Mutable state dict (will be modified in-place)

    Returns:
        List of new (unseen) content items
    """
    if handle not in state:
        state[handle] = {}

    seen = state[handle]
    now = datetime.utcnow().isoformat() + "Z"
    new_items = []

    for item in content_items:
        # Use url as primary key, fallback to shortcode
        content_id = item.get("url") or item.get("shortcode") or ""
        if not content_id:
            # Skip items without identifiable key
            continue

        if content_id not in seen:
            seen[content_id] = now
            new_items.append(item)

    return new_items


def get_stale_competitors(max_age_hours: int = 24) -> List[str]:
    """
    Check which competitors need fresh scraping.

    A competitor is stale if:
    - No state entry exists for them
    - Their latest tracked entry is older than max_age_hours

    Returns list of stale competitor handles.
    """
    if not BRAIN_FILE.exists():
        return []

    with open(BRAIN_FILE, "r", encoding="utf-8") as f:
        brain = json.load(f)

    competitors = brain.get("competitors", [])
    state = load_state()
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    stale = []

    for comp in competitors:
        handle = comp.get("handle", "").lstrip("@").lower()
        if not handle:
            continue

        entries = state.get(handle, {})
        if not entries:
            stale.append(handle)
            continue

        # Find the most recent entry
        latest = max(entries.values())
        try:
            latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00")).replace(tzinfo=None)
            if latest_dt < cutoff:
                stale.append(handle)
        except (ValueError, AttributeError):
            stale.append(handle)

    return stale


def cleanup_old_entries(state: Dict, max_age_days: int = 30) -> Dict:
    """
    Remove entries older than max_age_days to prevent unbounded growth.

    Returns cleaned state dict.
    """
    cutoff = datetime.utcnow() - timedelta(days=max_age_days)
    cleaned = {}

    for handle, entries in state.items():
        kept = {}
        for content_id, timestamp in entries.items():
            try:
                entry_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
                if entry_dt >= cutoff:
                    kept[content_id] = timestamp
            except (ValueError, AttributeError):
                # Keep entries we can't parse (don't lose data)
                kept[content_id] = timestamp
        if kept:
            cleaned[handle] = kept

    return cleaned
