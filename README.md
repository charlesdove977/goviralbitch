# Viral Command

**Trainable social media coaching system for Claude Code.**

Find winning topics across 9+ platforms, develop proven angles, generate battle-tested hooks and scripts, analyze performance, and automatically learn what works for YOUR audience. Clone the repo, onboard your brain, and start creating content that compounds.

---

## What Is This?

Viral Command is an open-source content pipeline built as a set of Claude Code commands. Four core modules — Discover, Angle, Script, and Analyze — work independently and compose into a self-improving loop. An agent brain learns your audience preferences over time, scoring topics higher when they match your ICP and deprioritizing what doesn't perform.

Every output includes monetization coaching: CTA strategy, funnel direction, and lead magnet suggestions baked into every script and angle.

---

## Features

- **8 pipeline commands** covering the full content lifecycle
- **Agent brain** that evolves from your performance data (topics, hooks, thumbnails, posting times)
- **9+ platform discovery** — YouTube, Instagram, TikTok, LinkedIn, Reddit, X, Hacker News, GitHub, Web
- **HookGenie engine** built in — 6 hook patterns with composite scoring
- **Competitor tracking** — scrape, transcribe, and extract content skeletons from competitors
- **PDF lead magnet generation** from any script (longform or shortform)
- **Content calendar** with configurable cadence engine
- **Automated cron** — daily discovery + weekly analysis, unattended
- **Idea board** with pipeline funnel tracking and content repurposing
- **Insight aggregation** — top topics, hook performance, thumbnail patterns, posting times
- **Cross-platform** — macOS native, Windows via WSL, Linux via crontab

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/charlieautomates/viral-command.git
cd viral-command

# 2. Run the bootstrap script
bash scripts/init-viral-command.sh

# 3. Copy env template and add your API keys
cp .env.example .env
# Edit .env with your keys (see SETUP.md for details)

# 4. Verify platform connections
/viral:setup --check

# 5. Create your agent brain
/viral:onboard
```

See [SETUP.md](SETUP.md) for detailed installation instructions, platform connection guides, and troubleshooting.

---

## The Pipeline

```
 DISCOVER ──> ANGLE ──> SCRIPT ──> PUBLISH ──> ANALYZE
    ^                                             |
    |                                             |
    └─── feedback loop (brain evolves) ───────────┘
```

| Stage | What Happens |
|-------|-------------|
| **Discover** | Scan 9+ platforms for trending topics, score against your ICP, track competitors |
| **Angle** | Apply Contrast Formula to turn raw topics into platform-specific angles with CTA direction |
| **Script** | Generate hooks (6 patterns), full scripts (longform/shortform), filming cards, PDF lead magnets |
| **Publish** | Schedule content via calendar, track ideas through pipeline stages |
| **Analyze** | Pull analytics, extract winners, identify patterns, auto-update brain and hook repository |

---

## Command Reference

| Command | What It Does | Key Flags |
|---------|-------------|-----------|
| `/viral:onboard` | Interactive agent brain setup — ICP, pillars, platforms, competitors, monetization | — |
| `/viral:discover` | Multi-platform topic discovery scored against your ICP | `--quick`, `--deep`, `--dry-run`, `--emit` |
| `/viral:angle` | Contrast Formula angle development with platform templates | `--competitors`, `--pick` |
| `/viral:script` | HookGenie hooks + script generation (longform/shortform/PDF) | `--longform`, `--shortform`, `--pdf`, `--pick` |
| `/viral:analyze` | Multi-platform analytics collection + winner extraction + feedback loop | `--manual`, `--youtube`, `--instagram`, `--tiktok`, `--linkedin`, `--extract-winners` |
| `/viral:ideas` | Idea board CRUD + pipeline funnel + content repurposing + scheduling | `--add`, `--list`, `--advance`, `--repurpose`, `--schedule`, `--link` |
| `/viral:status` | Pipeline dashboard — funnel, calendar, brain health, platform status | `--calendar`, `--generate`, `--brain` |
| `/viral:setup` | Platform connection wizard — dependency check, API config, verification | `--check`, `--reconfig`, `--version` |
| `/viral:update-brain` | Brain evolution protocol + insight aggregation | `--insights` |

---

## Architecture

```
viral-command/
├── .claude/commands/       # 9 pipeline commands (viral-*.md)
├── data/                   # JSONL data stores + agent brain
│   ├── agent-brain.json    # Evolving system memory
│   ├── topics/             # Discovered topics
│   ├── angles.jsonl        # Developed angles
│   ├── hooks.jsonl         # Hook repository
│   ├── scripts.jsonl       # Generated scripts
│   ├── analytics/          # Performance data
│   ├── insights/           # Aggregated patterns
│   ├── idea-board.jsonl    # Content pipeline tracker
│   ├── calendar.jsonl      # Content calendar slots
│   └── cta-templates.json  # CTA template library
├── schemas/                # JSON Schema draft-07 contracts (10 schemas)
├── scripts/                # Bash + Python utilities
│   ├── init-viral-command.sh   # Bootstrap script
│   ├── daily-discover.sh       # Daily cron orchestrator
│   ├── weekly-analyze.sh       # Weekly cron orchestrator
│   ├── install-crons.sh        # One-command cron installer
│   ├── generate-pdf.py         # PDF lead magnet generator
│   └── run-recon-ui.sh         # Flask recon UI launcher
├── recon/                  # Competitor analysis module
│   ├── scraper/            # Instagram + YouTube scrapers
│   ├── skeleton_ripper/    # Content skeleton extraction
│   ├── web/                # Flask UI (competitor dashboard)
│   └── storage/            # SQLite persistence
├── scoring/                # Topic scoring engine
├── skills/last30days/      # Bundled discovery skill
├── cron/                   # macOS launchd plist files
├── docs/                   # Cross-platform documentation
└── logs/                   # Runtime logs
```

---

## Data Contracts

All data flows through JSON Schema draft-07 validated contracts:

| Schema | Purpose |
|--------|---------|
| `agent-brain.schema.json` | System memory — ICP, pillars, weights, hooks, patterns |
| `topic.schema.json` | Discovered topic with scores and metadata |
| `angle.schema.json` | Contrast Formula angle with platform template |
| `hook.schema.json` | Hook with pattern, scores, and performance data |
| `script.schema.json` | Full script with structure, filming cards, lifecycle |
| `analytics-entry.schema.json` | Platform metrics with winner extraction |
| `insight.schema.json` | Aggregated performance patterns |
| `idea-board-entry.schema.json` | Pipeline idea with stage tracking |
| `calendar-entry.schema.json` | Content calendar slot |
| `competitor-reel.schema.json` | Scraped competitor content metadata |

---

## Cron Automation

Viral Command includes automated daily discovery and weekly analysis via cron:

- **Daily** (6 AM UTC): Scrape competitors, discover topics, score and save
- **Weekly** (Friday 6 AM UTC): Pull analytics, extract winners, update brain

Supports macOS launchd (native), Linux crontab/systemd, and Windows Task Scheduler.

See [docs/CRON-SETUP.md](docs/CRON-SETUP.md) for setup instructions across all platforms.

---

## Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Claude Code | Latest | CLI runtime for all commands |
| Python | 3.10+ | Recon module, PDF generation, scoring |
| Node.js | 18+ | Bundled last30days skill |
| OpenAI API key | — | Whisper transcription + LLM scoring |
| YouTube Data API v3 key | — | Analytics collection + thumbnail fetch |

Optional: Instaloader (Instagram scraping, no API key needed), yt-dlp (YouTube transcripts).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting bugs, suggesting features, and submitting pull requests.

---

## License

MIT License. See [LICENSE](LICENSE) for full text.

---

Built by [Charles Dove](https://ccstrategic.io) | [YouTube](https://youtube.com/@charlieautomates) | [Skool Community](https://start.ccstrategic.io/skool)
