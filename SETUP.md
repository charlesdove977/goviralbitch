# Setup Guide

Detailed installation and configuration for Viral Command.

---

## Prerequisites

| Tool | Required | Install |
|------|----------|---------|
| Claude Code | Yes | [claude.ai/code](https://claude.ai/code) |
| Python 3.10+ | Yes | `brew install python` (macOS) or [python.org](https://python.org) |
| Node.js 18+ | Yes | `brew install node` (macOS) or [nodejs.org](https://nodejs.org) |
| pip | Yes | Included with Python |
| Git | Yes | `brew install git` (macOS) |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/charlieautomates/viral-command.git
cd viral-command
```

### 2. Run the Bootstrap Script

```bash
bash scripts/init-viral-command.sh
```

This script is idempotent (safe to run multiple times). It will:
- Create required data directories
- Initialize empty data files (topics, angles, hooks, scripts, etc.)
- Install Python dependencies from `requirements.txt`
- Install CLI tools (`yt-dlp`, `instaloader`) if missing
- Generate a `.env` template if one doesn't exist

Use `--force` to reset all data files to defaults:

```bash
bash scripts/init-viral-command.sh --force
```

### 3. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

**Required keys:**

| Key | Where to Get It | Used By |
|-----|----------------|---------|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | Whisper transcription, LLM scoring in recon |
| `YOUTUBE_DATA_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/apis/library/youtube.googleapis.com) | /viral:analyze (metrics), /viral:discover (search) |

**Optional keys:**

| Key | Where to Get It | Used By |
|-----|----------------|---------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | Recon skeleton ripper LLM calls |
| `GOOGLE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/) | Additional Google service access |

### 4. Verify Connections

Run the setup wizard to check everything is working:

```
/viral:setup --check
```

This verifies: Python version, Node.js version, pip packages, CLI tools, API key presence, and connectivity.

### 5. Create Your Agent Brain

```
/viral:onboard
```

The onboarding wizard asks about your:
- Ideal Customer Profile (ICP)
- Content pillars and topics
- Target platforms (research vs posting)
- Competitors to track
- Monetization strategy and funnel structure
- CTA preferences

This creates `data/agent-brain.json` — the persistent memory that all commands read from.

---

## Platform Connections

### YouTube

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable **YouTube Data API v3**
4. Create an API key under Credentials
5. Add to `.env` as `YOUTUBE_DATA_API_KEY`

Used by: `/viral:discover` (search), `/viral:analyze` (metrics + thumbnails)

### Instagram

No API key needed. Viral Command uses [Instaloader](https://instaloader.github.io/) for public profile scraping.

```bash
pip install instaloader
```

Note: Some engagement metrics may require an Instagram login. Instaloader will prompt if needed.

### TikTok

Analytics entered manually via `/viral:analyze` interactive prompts. No API connection required for v0.1.

### LinkedIn

Analytics entered manually via `/viral:analyze` interactive prompts. No API connection required for v0.1.

### OpenAI (Whisper)

1. Get an API key from [platform.openai.com](https://platform.openai.com/api-keys)
2. Add to `.env` as `OPENAI_API_KEY`

Used by: Recon module (transcribing competitor video/audio content via Whisper API)

---

## Cron Setup

For automated daily discovery and weekly analysis, see [docs/CRON-SETUP.md](docs/CRON-SETUP.md).

Quick install (macOS):

```bash
bash scripts/install-crons.sh
```

Quick uninstall:

```bash
bash scripts/uninstall-crons.sh
```

---

## Windows Setup

Windows users should use WSL (Windows Subsystem for Linux):

1. Install WSL: `wsl --install` in PowerShell (admin)
2. Open WSL terminal
3. Follow the Linux/macOS instructions above
4. For cron, see the Windows section in [docs/CRON-SETUP.md](docs/CRON-SETUP.md)

---

## Troubleshooting

### "command not found" for yt-dlp or instaloader

Your shell PATH may not include pip's bin directory. Add to your shell profile:

```bash
# ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
```

On macOS with Homebrew:

```bash
export PATH="/opt/homebrew/bin:$PATH"
```

### YouTube API quota exceeded

The YouTube Data API v3 has a daily quota of 10,000 units. Each search costs 100 units, each video details request costs 1 unit. If you hit limits:

- Reduce discovery frequency (skip a day)
- Use `--quick` flag on `/viral:discover` for fewer API calls
- Check quota usage at [Google Cloud Console](https://console.cloud.google.com/apis/dashboard)

### Python dependency conflicts

Use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Instaloader login issues

Instagram may rate-limit or block unauthenticated requests. If scraping fails:

1. Try logging in: `instaloader --login YOUR_USERNAME`
2. Instaloader stores session cookies locally
3. As a fallback, use `/viral:discover --quick` to skip Instagram sources

### Permission denied on scripts

```bash
chmod +x scripts/*.sh
```

---

## First Run Checklist

After setup, run through the pipeline once to verify everything works:

1. `/viral:onboard` — Create your agent brain
2. `/viral:discover --quick` — Run a quick discovery scan
3. `/viral:angle --pick` — Develop an angle from a discovered topic
4. `/viral:script --pick --shortform` — Generate a shortform script
5. `/viral:status` — View your pipeline dashboard

---

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Skool Community**: [start.ccstrategic.io/skool](https://start.ccstrategic.io/skool)
- **YouTube**: [youtube.com/@charlieautomates](https://youtube.com/@charlieautomates)
