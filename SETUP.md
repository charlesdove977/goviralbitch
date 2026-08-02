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

Running with Docker? You only need Docker itself — skip to [Docker](#docker) below.

---

## Docker

The image bundles Claude Code, Python 3.12, Node 22, yt-dlp, Instaloader, ffmpeg and every Python
dependency, so nothing but Docker Engine 20.10+ with Compose v2 has to exist on your machine.

Usage mirrors the native install: one command opens the same Claude Code session you would get
by running `claude` in the repo, and the Recon UI is available in your browser while you work.
The commands below are identical on macOS, Linux and Windows (Docker Desktop — no WSL needed).

### 1. Install Docker

Skip this step if `docker compose version` already works on your machine.

```bash
# macOS — Docker Desktop via Homebrew, then launch Docker.app once
brew install --cask docker

# Windows — Docker Desktop via winget (PowerShell), then launch it once
winget install -e --id Docker.DockerDesktop

# Linux — Docker's official install script (Engine + Compose)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # log out and back in to run docker without sudo
```

These are Docker's officially maintained channels, so they stay current on their own. If none of
them fits your machine, download from [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) —
it always points at the current installers. On Windows, Docker Desktop sets up its WSL 2 backend
automatically (it may ask for a reboot).

### 2. Open Claude Code

```bash
git clone https://github.com/charlesdove977/goviralbro.git
cd goviralbro
docker compose run --rm goviralbro
```

The first run builds the image (a few minutes), then drops you into Claude Code inside the
container with all seven `/viral:*` commands and the bundled `last30days` skill already
registered. Run `/viral:onboard` to create your agent brain.

The Recon Intelligence UI is started alongside the session — open
[localhost:5001](http://localhost:5001) in your browser. The container bootstrap also creates
the `data/` tree, initializes empty data files, and copies `.env.example` to `.env` if you
don't have one yet.

Use `docker compose run --rm goviralbro bash` if you want a shell instead, or add `--no-deps`
to skip starting the Recon UI.

### 3. Add Your API Keys

Edit `.env` (same keys as a native install — see [Configure API Keys](#3-configure-api-keys)),
then start your next session — containers pick up `.env` when they start:

```bash
docker compose up -d --force-recreate    # restart the Recon UI with the new keys
```

### Everyday Commands

| Command | What It Does |
|---------|-------------|
| `docker compose run --rm goviralbro` | Claude Code session with `/viral:*` loaded + Recon UI |
| `./scripts/run-recon-ui.sh` | Recon UI only — same script as the native install |
| `docker compose up -d` | Recon UI only, kept running in the background |
| `docker compose run --rm goviralbro bash` | Shell in the container |
| `docker compose logs -f recon` | Follow the Recon UI logs |
| `docker compose down` | Stop everything |
| `docker compose build --no-cache` | Rebuild from scratch |

### How It Is Wired

- **Your repo is mounted at `/app`.** `data/`, `logs/` and `.env` live on the host, so nothing is
  lost when a container is removed, and edits to `.claude/commands/*.md` apply on the next run.
- **`.env` is loaded into both services.** Any key you add is visible to the pipeline scripts.
  The bundled `last30days` skill reads it too — `~/.config/last30days/.env` is symlinked to it.
- **Claude Code's login lives in the `claude-home` volume**, so you authenticate once. Alternatively
  set `ANTHROPIC_API_KEY` in `.env` — note that this also switches Claude Code to API billing.
- **The container runs as the user that owns the repo**, detected at startup, so files written to
  `data/` come out owned by you. Override with `PUID` / `PGID` if the detection is wrong:

  ```bash
  PUID=$(id -u) PGID=$(id -g) docker compose up -d
  ```

- **The Recon UI binds to `127.0.0.1` only.** Change the host port with `RECON_HOST_PORT` in `.env`.

### Docker Notes

- YouTube OAuth (`scripts/setup-yt-oauth.py`) opens a browser on the host — run it there, or paste
  the URL it prints. The resulting token is written into the mounted repo either way.
- X/Twitter search reads browser cookies, which a container doesn't have. The other discovery
  sources (Reddit, YouTube, web) work normally; set `XAI_API_KEY` in `.env` to restore X.
- Local Whisper (`openai-whisper`) is not preinstalled — it pulls in PyTorch. The OpenAI Whisper API
  is used instead and needs only `OPENAI_API_KEY`.

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

The Docker setup works on Windows as-is — Docker Desktop handles the Linux side for you.

For a native install, use WSL (Windows Subsystem for Linux):

1. Install WSL: `wsl --install` in PowerShell (admin)
2. Open WSL terminal
3. Follow the Linux/macOS instructions above
4. For cron, see the Windows section in [docs/CRON-SETUP.md](docs/CRON-SETUP.md)

---

## Troubleshooting

### "command not found" for yt-dlp or instaloader

Your shell PATH may not include pip's bin directory. Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# macOS with Python.org installer
export PATH="/Library/Frameworks/Python.framework/Versions/3.14/bin:$PATH"

# macOS with Homebrew
export PATH="/opt/homebrew/bin:$PATH"

# Linux / WSL
export PATH="$HOME/.local/bin:$PATH"
```

Then reload: `source ~/.zshrc`

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

### Docker: container exits with "not writable"

The startup script could not determine which user owns the mounted repo. Pass it explicitly:

```bash
PUID=$(id -u) PGID=$(id -g) docker compose up -d
```

### Docker: port 5001 already in use

Another process holds the port. Pick a different one in `.env`:

```bash
RECON_HOST_PORT=5002
```

Then `docker compose up -d --force-recreate`.

### Docker: changed .env but keys aren't picked up

Environment variables are read when the container starts. Recreate it:

```bash
docker compose up -d --force-recreate
```

---

## First Run Checklist

After setup, run through the pipeline once to verify everything works:

1. `/viral:onboard` — Create your agent brain
2. `/viral:discover --quick` — Run a quick discovery scan
3. `/viral:angle --pick` — Develop an angle from a discovered topic
4. `/viral:script --pick --shortform` — Generate a shortform script

---

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Skool Community**: [start.ccstrategic.io/skool](https://start.ccstrategic.io/skool)
- **YouTube**: [youtube.com/@charlieautomates](https://youtube.com/@charlieautomates)
