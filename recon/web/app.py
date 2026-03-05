"""
Recon UI — Flask-based competitor intelligence dashboard for Viral Command.
Stripped from ReelRecon: removed TikTok, cookies, updater.
Added: competitor-first workflow, agent-brain integration, bridge to discover.
"""

import os
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Optional

from flask import Flask, render_template, request, jsonify

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from recon.config import load_config, load_competitors, save_credentials, load_credentials
from recon.scraper.instagram import InstaClient
from recon.scraper.youtube import get_channel_videos, save_channel_data
from recon.scraper.downloader import transcribe_video_openai, WHISPER_AVAILABLE
from recon.skeleton_ripper import (
    SkeletonRipperPipeline, create_job_config, JobProgress, JobStatus,
    get_available_providers
)
from recon.bridge import generate_topics_from_skeletons, save_topics_jsonl, load_latest_skeletons
from recon.storage.database import init_db
from recon.utils.logger import get_logger

logger = get_logger()

# Paths
BASE_DIR = Path(__file__).parent
PIPELINE_DIR = BASE_DIR.parent.parent
DATA_DIR = PIPELINE_DIR / "data"
RECON_DATA_DIR = DATA_DIR / "recon"

# Initialize Flask
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / 'static'),
    template_folder=str(BASE_DIR / 'templates')
)
app.secret_key = os.urandom(24)

# Initialize database
init_db()

# Active jobs tracking
active_jobs = {}


# =============================================================================
# ROUTES — Pages
# =============================================================================

@app.route('/')
def index():
    """Main competitor dashboard."""
    competitors = load_competitors()
    return render_template('competitors.html', competitors=competitors)


@app.route('/skeleton-ripper')
def skeleton_ripper():
    """Skeleton ripper page."""
    competitors = load_competitors()
    providers = get_available_providers()
    return render_template('skeleton_ripper.html', competitors=competitors, providers=providers)


@app.route('/settings')
def settings():
    """Settings page for credentials and API keys."""
    creds = load_credentials()
    providers = get_available_providers()
    return render_template('settings.html', creds=creds, providers=providers)


# =============================================================================
# API — Competitors
# =============================================================================

@app.route('/api/competitors')
def api_list_competitors():
    """List all competitors from agent brain with last scrape info."""
    competitors = load_competitors()
    result = []
    for c in competitors:
        handle_clean = c.handle.lstrip("@")
        competitor_dir = RECON_DATA_DIR / "competitors" / handle_clean

        last_scraped = None
        reel_count = 0
        top_views = 0

        reels_file = competitor_dir / "reels.json"
        videos_file = competitor_dir / "videos.json"

        data_file = reels_file if reels_file.exists() else (videos_file if videos_file.exists() else None)
        if data_file and data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                last_scraped = data.get("scraped_at")
                items = data.get("reels", data.get("videos", []))
                reel_count = len(items)
                if items:
                    top_views = max(r.get("views", 0) for r in items)
            except Exception:
                pass

        result.append({
            "name": c.name,
            "platform": c.platform,
            "handle": c.handle,
            "why_watch": c.why_watch,
            "last_scraped": last_scraped,
            "reel_count": reel_count,
            "top_views": top_views,
        })

    return jsonify(result)


@app.route('/api/competitors/<handle>/scrape', methods=['POST'])
def api_scrape_competitor(handle):
    """Scrape a single competitor."""
    config = load_config()
    handle_clean = handle.lstrip("@")

    # Find competitor config
    competitor = next((c for c in config.competitors if c.handle.lstrip("@") == handle_clean), None)
    if not competitor:
        return jsonify({"error": f"Competitor @{handle_clean} not found in agent brain"}), 404

    max_reels = request.json.get("max_reels", 50) if request.is_json else 50
    job_id = str(uuid.uuid4())[:8]

    active_jobs[job_id] = {
        "status": "running",
        "handle": handle_clean,
        "platform": competitor.platform,
        "message": f"Starting scrape of @{handle_clean}...",
        "progress": 0,
        "reels": [],
    }

    def run_scrape():
        try:
            if competitor.platform == "instagram":
                if not config.ig_username or not config.ig_password:
                    active_jobs[job_id]["status"] = "error"
                    active_jobs[job_id]["message"] = "IG credentials not configured. Go to Settings."
                    return

                client = InstaClient()
                if not client.login(config.ig_username, config.ig_password):
                    active_jobs[job_id]["status"] = "error"
                    active_jobs[job_id]["message"] = "Instagram login failed."
                    return

                def progress_cb(msg):
                    active_jobs[job_id]["message"] = msg

                reels = client.get_competitor_reels(handle_clean, max_reels=max_reels, progress_callback=progress_cb)
                client.save_competitor_data(handle_clean, reels)

                active_jobs[job_id]["reels"] = reels[:10]  # Top 10 for display
                active_jobs[job_id]["total"] = len(reels)
                active_jobs[job_id]["status"] = "complete"
                active_jobs[job_id]["message"] = f"Scraped {len(reels)} reels from @{handle_clean}"

            elif competitor.platform == "youtube":
                def progress_cb(msg):
                    active_jobs[job_id]["message"] = msg

                videos = get_channel_videos(handle_clean, max_videos=max_reels, progress_callback=progress_cb)
                save_channel_data(handle_clean, videos)

                active_jobs[job_id]["reels"] = videos[:10]
                active_jobs[job_id]["total"] = len(videos)
                active_jobs[job_id]["status"] = "complete"
                active_jobs[job_id]["message"] = f"Scraped {len(videos)} videos from {handle_clean}"

            else:
                active_jobs[job_id]["status"] = "error"
                active_jobs[job_id]["message"] = f"Platform {competitor.platform} not yet supported"

        except Exception as e:
            active_jobs[job_id]["status"] = "error"
            active_jobs[job_id]["message"] = f"Error: {str(e)}"
            logger.error("UI", f"Scrape error for @{handle_clean}", exception=e)

    Thread(target=run_scrape, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "started"})


@app.route('/api/competitors/scrape-all', methods=['POST'])
def api_scrape_all():
    """Scrape all competitors from agent brain."""
    competitors = load_competitors()
    job_ids = []

    for c in competitors:
        handle_clean = c.handle.lstrip("@")
        # Trigger individual scrape via internal call
        with app.test_request_context(
            f'/api/competitors/{handle_clean}/scrape',
            method='POST',
            content_type='application/json',
            data=json.dumps({"max_reels": 50})
        ):
            response = api_scrape_competitor(handle_clean)
            if hasattr(response, 'json'):
                data = response.get_json()
                if data and "job_id" in data:
                    job_ids.append(data["job_id"])

    return jsonify({"job_ids": job_ids, "count": len(job_ids)})


@app.route('/api/jobs/<job_id>/status')
def api_job_status(job_id):
    """Poll job progress."""
    job = active_jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


# =============================================================================
# API — Skeleton Ripper
# =============================================================================

@app.route('/api/recon/analyze', methods=['POST'])
def api_run_analysis():
    """Run skeleton ripper on selected competitors."""
    data = request.get_json()
    usernames = data.get("usernames", [])
    videos_per_creator = data.get("videos_per_creator", 3)
    llm_provider = data.get("llm_provider", "openai")
    llm_model = data.get("llm_model", "gpt-4o-mini")

    if not usernames:
        return jsonify({"error": "No usernames provided"}), 400

    job_id = f"sr_{uuid.uuid4().hex[:8]}"
    active_jobs[job_id] = {
        "type": "skeleton_ripper",
        "status": "running",
        "message": "Starting skeleton analysis...",
        "progress": {},
    }

    def run_analysis():
        try:
            config = create_job_config(
                usernames=usernames,
                videos_per_creator=videos_per_creator,
                llm_provider=llm_provider,
                llm_model=llm_model,
            )

            pipeline = SkeletonRipperPipeline()

            def on_progress(progress: JobProgress):
                active_jobs[job_id]["message"] = progress.message
                active_jobs[job_id]["progress"] = {
                    "status": progress.status.value,
                    "phase": progress.phase,
                    "videos_scraped": progress.videos_scraped,
                    "videos_transcribed": progress.videos_transcribed,
                    "skeletons_extracted": progress.skeletons_extracted,
                    "total_target": progress.total_target,
                    "errors": progress.errors,
                }

            result = pipeline.run(config, on_progress=on_progress)

            active_jobs[job_id]["status"] = "complete" if result.success else "error"
            active_jobs[job_id]["message"] = (
                f"Done: {len(result.skeletons)} skeletons extracted"
                if result.success else f"Failed: {', '.join(result.progress.errors)}"
            )
            active_jobs[job_id]["result"] = {
                "report_path": result.report_path,
                "skeletons_path": result.skeletons_path,
                "skeleton_count": len(result.skeletons),
            }

        except Exception as e:
            active_jobs[job_id]["status"] = "error"
            active_jobs[job_id]["message"] = f"Error: {str(e)}"
            logger.error("UI", f"Skeleton analysis error", exception=e)

    Thread(target=run_analysis, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "started"})


@app.route('/api/recon/push-to-discover', methods=['POST'])
def api_push_to_discover():
    """Bridge: convert latest skeletons → JSONL topics for /viral:discover."""
    try:
        skeletons = load_latest_skeletons()
        if not skeletons:
            return jsonify({"error": "No skeleton reports found. Run analysis first."}), 404

        topics = generate_topics_from_skeletons(skeletons)
        output_file = save_topics_jsonl(topics)

        return jsonify({
            "success": True,
            "topics_count": len(topics),
            "output_file": str(output_file),
            "message": f"Pushed {len(topics)} competitor-sourced topics to discovery pipeline"
        })

    except Exception as e:
        logger.error("UI", f"Push to discover failed", exception=e)
        return jsonify({"error": str(e)}), 500


# =============================================================================
# API — Settings
# =============================================================================

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """Get current settings (masked)."""
    creds = load_credentials()
    return jsonify({
        "ig_username": creds.get("ig_username", ""),
        "ig_password_set": bool(creds.get("ig_password")),
        "openai_api_key_set": bool(creds.get("openai_api_key")),
        "anthropic_api_key_set": bool(creds.get("anthropic_api_key")),
        "llm_provider": creds.get("llm_provider", "openai"),
        "llm_model": creds.get("llm_model", "gpt-4o-mini"),
    })


@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    """Save credentials and settings."""
    data = request.get_json()
    creds = load_credentials()

    # Update only provided fields
    for key in ["ig_username", "ig_password", "openai_api_key", "anthropic_api_key",
                "google_api_key", "llm_provider", "llm_model", "transcribe_provider"]:
        if key in data and data[key]:
            creds[key] = data[key]

    save_credentials(creds)
    return jsonify({"success": True, "message": "Settings saved"})


@app.route('/api/providers')
def api_get_providers():
    """Get available LLM providers."""
    return jsonify(get_available_providers())


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Launch the Recon UI."""
    print("\n" + "=" * 50)
    print("  VIRAL COMMAND — Recon Intelligence")
    print("  http://localhost:5001")
    print("=" * 50 + "\n")

    app.run(host='0.0.0.0', port=5001, debug=True)


if __name__ == '__main__':
    main()
