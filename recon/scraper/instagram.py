"""
Recon — Instaloader-based Instagram scraper.
Replaces ReelRecon's cookie-based session approach with Instaloader login.

Usage:
    client = InstaClient()
    client.login("username", "password")
    reels = client.get_competitor_reels("cooper.simson", max_reels=50)
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Callable

import instaloader

from recon.utils.logger import get_logger

logger = get_logger()

# Data directory for session files and competitor data
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "recon"


class InstaClient:
    """Instaloader-based Instagram client with session persistence."""

    def __init__(self, session_dir: Optional[Path] = None):
        self.session_dir = session_dir or DATA_DIR
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,
        )
        self._logged_in = False
        self._username = None

    def login(self, username: str, password: str) -> bool:
        """
        Login to Instagram. Tries loading saved session first, falls back to fresh login.

        Args:
            username: Instagram username
            password: Instagram password

        Returns:
            True if login successful
        """
        session_file = self.session_dir / f".session_{username}"

        # Try loading existing session
        if session_file.exists():
            try:
                self.loader.load_session_from_file(username, str(session_file))
                # Verify session is still valid
                self.loader.test_login()
                self._logged_in = True
                self._username = username
                logger.info("INSTA", f"Session loaded for @{username}")
                return True
            except Exception as e:
                logger.warning("INSTA", f"Saved session invalid for @{username}, re-logging in", {
                    "error": str(e)
                })

        # Fresh login
        try:
            self.loader.login(username, password)
            self.loader.save_session_to_file(str(session_file))
            self._logged_in = True
            self._username = username
            logger.info("INSTA", f"Fresh login successful for @{username}")
            return True
        except instaloader.exceptions.BadCredentialsException:
            logger.error("INSTA", f"Bad credentials for @{username}")
            return False
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            logger.error("INSTA", f"2FA required for @{username} — not supported in headless mode")
            return False
        except Exception as e:
            logger.error("INSTA", f"Login failed for @{username}", exception=e)
            return False

    def get_competitor_reels(
        self,
        handle: str,
        max_reels: int = 50,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Dict]:
        """
        Fetch reel metadata from a competitor's profile.

        Args:
            handle: Instagram handle (without @)
            max_reels: Maximum reels to fetch
            progress_callback: Optional callback for progress updates

        Returns:
            List of reel dicts sorted by views (descending)
        """
        if not self._logged_in:
            raise RuntimeError("Not logged in. Call login() first.")

        reels = []
        handle = handle.lstrip("@")

        try:
            profile = instaloader.Profile.from_username(self.loader.context, handle)
        except instaloader.exceptions.ProfileNotExistsException:
            logger.error("INSTA", f"Profile @{handle} does not exist")
            return []
        except Exception as e:
            logger.error("INSTA", f"Failed to load profile @{handle}", exception=e)
            return []

        if profile.is_private and not profile.followed_by_viewer:
            logger.warning("INSTA", f"@{handle} is private and not followed")
            return []

        profile_info = {
            "full_name": profile.full_name,
            "followers": profile.followers,
            "username": handle,
        }

        logger.info("INSTA", f"Fetching reels from @{handle}", {
            "followers": profile.followers,
            "full_name": profile.full_name
        })

        if progress_callback:
            progress_callback(f"Scanning @{handle} ({profile.followers:,} followers)...")

        count = 0
        for post in profile.get_posts():
            if count >= max_reels:
                break

            # Only interested in video/reel posts
            if not post.is_video:
                continue

            reel = {
                "shortcode": post.shortcode,
                "url": f"https://www.instagram.com/reel/{post.shortcode}/",
                "video_url": post.video_url,
                "views": post.video_view_count or 0,
                "likes": post.likes,
                "comments": post.comments,
                "caption": (post.caption or "")[:200],
                "timestamp": post.date_utc.isoformat(),
                "profile": profile_info,
            }
            reels.append(reel)
            count += 1

            if progress_callback and count % 5 == 0:
                progress_callback(f"Found {count} reels from @{handle}...")

            # Rate limiting
            if count % 12 == 0:
                time.sleep(1)

        # Sort by views descending
        reels.sort(key=lambda x: x.get("views", 0), reverse=True)

        logger.info("INSTA", f"Fetched {len(reels)} reels from @{handle}", {
            "top_views": reels[0]["views"] if reels else 0
        })

        return reels

    def download_reel(self, shortcode: str, output_path: Path) -> bool:
        """
        Download a single reel video file.

        Args:
            shortcode: Instagram reel shortcode
            output_path: Path to save the video file

        Returns:
            True if download successful
        """
        if not self._logged_in:
            raise RuntimeError("Not logged in. Call login() first.")

        try:
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

            if not post.is_video or not post.video_url:
                logger.warning("INSTA", f"Post {shortcode} is not a video or has no video URL")
                return False

            # Download using requests (Instaloader's context has authenticated session)
            import requests
            output_path.parent.mkdir(parents=True, exist_ok=True)

            response = requests.get(post.video_url, stream=True, timeout=120)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info("INSTA", f"Downloaded reel {shortcode}", {
                        "file_size": output_path.stat().st_size
                    })
                    return True

            logger.warning("INSTA", f"Download failed for {shortcode}: HTTP {response.status_code}")
            return False

        except Exception as e:
            logger.error("INSTA", f"Download error for {shortcode}", exception=e)
            return False

    def save_competitor_data(self, handle: str, reels: List[Dict]):
        """Save scraped reel data to the competitor's data directory."""
        handle = handle.lstrip("@")
        competitor_dir = DATA_DIR / "competitors" / handle
        competitor_dir.mkdir(parents=True, exist_ok=True)

        output = {
            "handle": handle,
            "scraped_at": datetime.utcnow().isoformat(),
            "total_reels": len(reels),
            "reels": reels,
        }

        reels_file = competitor_dir / "reels.json"
        with open(reels_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        logger.info("INSTA", f"Saved {len(reels)} reels for @{handle} to {reels_file}")
