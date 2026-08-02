<p align="center">
  <img src="assets/gvb-logo.svg" alt="GVB" width="320" />
</p>

<h1 align="center">GO VIRAL BRO</h1>

<p align="center">
  A trainable social media coaching system for Claude Code.<br/>
  Finds winning topics, develops angles, generates hooks, learns from performance.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-3b82f6?style=flat-square" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-3b82f6?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/platform-Claude_Code-3b82f6?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/docker-compose-3b82f6?style=flat-square" alt="Docker Compose" />
  <a href="https://start.ccstrategic.io/skool"><img src="https://img.shields.io/badge/community-Skool-3b82f6?style=flat-square" alt="Skool Community" /></a>
</p>

<br/>

```bash
git clone https://github.com/charlesdove977/goviralbro.git && cd goviralbro && bash scripts/init-viral-command.sh

# or with Docker — nothing to install but Docker itself
git clone https://github.com/charlesdove977/goviralbro.git && cd goviralbro && docker compose run --rm goviralbro
```

<p align="center">Works on Mac, Linux, and Windows (WSL or Docker).</p>

<br/>

<p align="center">
  <img src="assets/install-preview.svg" alt="Terminal" width="600" />
</p>

<br/>

---

## The Pipeline

```
 DISCOVER ──> ANGLE ──> SCRIPT ──> POST ──> ANALYZE
    ^                                             |
    |                                             |
    └─── feedback loop (brain evolves) ───────────┘
```

| Stage | What Happens |
|-------|-------------|
| **Discover** | Pull your competitors' winning content — see what got the most engagement, transcribe their videos, extract hook skeletons, and repurpose them in your voice. Currently supports YouTube + Instagram. More platforms coming. |
| **Angle** | Apply Contrast Formula to turn raw topics into format-specific angles (longform, shortform, LinkedIn) |
| **Script** | Generate hooks (6 patterns), full scripts (longform/shortform), filming cards, PDF lead magnets |
| **Post** | Post on your platforms after you've created your content |
| **Analyze** | Pull analytics, extract winners, identify patterns, auto-update brain and hook repository |

---

## Commands

| Command | What It Does |
|---------|-------------|
| `/viral:setup` | Platform connection wizard — dependency check, API config, verification |
| `/viral:onboard` | Interactive agent brain setup — ICP, pillars, platforms, competitors |
| `/viral:discover` | Topic discovery — competitor scrape, YouTube/Reddit/GitHub keyword search, or both |
| `/viral:angle` | Contrast Formula angle development — 5 angles per format (longform/shortform/LinkedIn) |
| `/viral:script` | Interactive script generator — pick format → pick angle → hooks + full script + PDF option |
| `/viral:analyze` | Multi-platform analytics + winner extraction + feedback loop |
| `/viral:update-brain` | Brain evolution protocol + insight aggregation |

---

## Docker

Everything preinstalled — Claude Code, Python, Node, yt-dlp, Instaloader, ffmpeg. Same usage as the native install, same commands on Mac, Linux and Windows.

```bash
docker compose run --rm goviralbro       # open Claude Code — /viral:* ready
docker compose down                      # stop everything
```

The Recon UI starts with your session — open [localhost:5001](http://localhost:5001) in your browser.

- **API keys** — edit `.env` (created on first start), then restart
- **Your data** — `data/`, `logs/` and `.env` stay on your machine
- **Claude login** — saved in a volume, you authenticate once

See [SETUP.md](SETUP.md#docker) for the full guide.

---

## Features

- **Agent brain** that evolves from your performance data
- **Competitor intelligence** — pull their winning content, see engagement rankings, transcribe videos, extract hook skeletons, repurpose in your voice
- **HookGenie engine** — 6 hook patterns with composite scoring
- **Format-based angles** — 5 angles per format (longform, shortform, LinkedIn) = 15 takes per topic
- **PDF lead magnet generation** from any script
- **Discovery**: Competitor scraping (YouTube + Instagram) + keyword search (YouTube, Reddit, GitHub) — uses your brain's pillar keywords
- **Recon Intelligence UI** — browser dashboard for scraping competitors and ripping hook skeletons
- **Monetization coaching** baked into every output
- **One-command Docker setup** — `docker compose run --rm goviralbro` brings the whole toolchain

---

## Architecture

```
goviralbro/
├── Dockerfile              # Claude Code + Python + Node toolchain
├── docker-compose.yml      # Pipeline container + Recon UI
├── .claude/commands/       # 7 pipeline commands (viral-*.md)
├── data/                   # JSONL data stores + agent brain
│   ├── agent-brain.json    # Evolving system memory
│   ├── topics/             # Discovered topics
│   ├── angles.jsonl        # Developed angles
│   ├── hooks.jsonl         # Hook repository
│   ├── scripts.jsonl       # Generated scripts
│   ├── analytics/          # Performance data
│   ├── insights/           # Aggregated patterns
│   └── cta-templates.json  # CTA template library
├── schemas/                # JSON Schema draft-07 contracts
├── scripts/                # Bash + Python utilities (incl. generate-pdf.py)
│   └── docker-entrypoint.sh # Container bootstrap (data tree, .env, commands)
├── recon/                  # Competitor analysis module
├── scoring/                # Topic scoring engine
├── skills/last30days/      # Bundled discovery skill
└── docs/                   # Cross-platform documentation
```

---

## Requirements

**With Docker** — just Docker, an OpenAI API key and a YouTube Data API v3 key. Nothing else.

```bash
# Mac
brew install --cask docker

# Windows (PowerShell)
winget install -e --id Docker.DockerDesktop

# Linux
curl -fsSL https://get.docker.com | sh
```

On Mac/Windows, start Docker Desktop once after installing. No brew or winget? Get [Docker](https://docs.docker.com/get-docker/) directly.

**Native install:**

| Requirement | Version |
|-------------|---------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Latest |
| Python | 3.10+ |
| Node.js | 18+ (22+ for X search) |
| OpenAI API key | — |
| YouTube Data API v3 key | — |

Optional: Instaloader (Instagram scraping), yt-dlp (YouTube transcripts). Both are preinstalled in the Docker image.

See [SETUP.md](SETUP.md) for detailed installation and platform connection guides.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  Built by <a href="https://ccstrategic.io">Charles Dove</a> · <a href="https://youtube.com/@charlieautomates">YouTube</a> · <a href="https://start.ccstrategic.io/skool">Skool Community</a>
</p>
