# Cron Setup — Automated Discovery & Analysis

Viral Command runs two automated jobs to keep your content pipeline fresh:

| Job | Script | Frequency | Time (UTC) | What It Does |
|-----|--------|-----------|------------|--------------|
| Daily Discovery | `scripts/daily-discover.sh` | Every day | 6:00 AM | Scrapes competitors, scores new topics, saves to topics/ |
| Weekly Analysis | `scripts/weekly-analyze.sh` | Every Friday | 6:00 AM (1 AM EST) | Collects analytics, extracts winners, updates brain |

## Prerequisites

Before installing cron jobs:

1. Run `./scripts/init-viral-command.sh` to bootstrap the repo
2. Run `/viral:setup` to configure API keys
3. Run `/viral:onboard` to set up your creator profile
4. Test each script manually first (see [Testing](#testing) below)

---

## macOS (launchd) — Recommended

### Quick Install

```bash
./scripts/install-crons.sh
```

This copies the plist files to `~/Library/LaunchAgents/`, resolves paths, and loads them into launchd.

### Quick Uninstall

```bash
./scripts/uninstall-crons.sh
```

### Dry Run

Preview what will happen without making changes:

```bash
./scripts/install-crons.sh --dry-run
./scripts/uninstall-crons.sh --dry-run
```

### Manual Install

If you prefer to install manually:

```bash
# 1. Copy plists with path substitution
PIPELINE_DIR="$(pwd)"
sed "s|__PIPELINE_DIR__|$PIPELINE_DIR|g" cron/com.viralcommand.daily-discover.plist > ~/Library/LaunchAgents/com.viralcommand.daily-discover.plist
sed "s|__PIPELINE_DIR__|$PIPELINE_DIR|g" cron/com.viralcommand.weekly-analyze.plist > ~/Library/LaunchAgents/com.viralcommand.weekly-analyze.plist

# 2. Load into launchd
launchctl load ~/Library/LaunchAgents/com.viralcommand.daily-discover.plist
launchctl load ~/Library/LaunchAgents/com.viralcommand.weekly-analyze.plist
```

### Verify Running

```bash
launchctl list | grep viralcommand
```

You should see both jobs listed with a PID (or `-` if not currently running).

### Check Logs

```bash
# Live tail
tail -f logs/daily-discover.log
tail -f logs/weekly-analyze.log

# Last run
tail -50 logs/daily-discover.log
```

### Troubleshooting (macOS)

| Issue | Fix |
|-------|-----|
| "Operation not permitted" | System Settings → Privacy & Security → Full Disk Access → add Terminal |
| Scripts not running | Check: `launchctl list \| grep viralcommand` — if missing, re-run install |
| "No such file" in logs | Verify PIPELINE_DIR path is correct in the installed plist |
| Jobs not firing on schedule | Mac must be awake at scheduled time (launchd runs missed jobs on wake) |

---

## Windows (WSL + Task Scheduler)

### Option A: WSL + crontab (Recommended)

If you use WSL (Windows Subsystem for Linux), you can use standard crontab:

```bash
# Open crontab editor
crontab -e

# Add these two lines (replace /path/to/content-pipeline with your actual path):
0 6 * * * cd /path/to/content-pipeline && ./scripts/daily-discover.sh >> logs/daily-discover.log 2>&1
0 6 * * 5 cd /path/to/content-pipeline && ./scripts/weekly-analyze.sh >> logs/weekly-analyze.log 2>&1
```

**Important:** WSL must be running for crontab to fire. To auto-start WSL cron:

```powershell
# In PowerShell (admin), create a startup task:
schtasks /create /tn "WSL Cron" /tr "wsl -d Ubuntu -e sudo service cron start" /sc onlogon /rl highest
```

### Option B: Native Task Scheduler (schtasks)

If you prefer native Windows scheduling without WSL running:

```powershell
# Daily Discovery (6 AM UTC daily)
schtasks /create /tn "ViralCommand-DailyDiscover" /tr "wsl -d Ubuntu -e bash -c 'cd /path/to/content-pipeline && ./scripts/daily-discover.sh >> logs/daily-discover.log 2>&1'" /sc daily /st 06:00

# Weekly Analysis (Friday 6 AM UTC)
schtasks /create /tn "ViralCommand-WeeklyAnalyze" /tr "wsl -d Ubuntu -e bash -c 'cd /path/to/content-pipeline && ./scripts/weekly-analyze.sh >> logs/weekly-analyze.log 2>&1'" /sc weekly /d FRI /st 06:00
```

**To remove:**

```powershell
schtasks /delete /tn "ViralCommand-DailyDiscover" /f
schtasks /delete /tn "ViralCommand-WeeklyAnalyze" /f
```

### Troubleshooting (Windows)

| Issue | Fix |
|-------|-----|
| "wsl" not recognized | Install WSL: `wsl --install` in PowerShell (admin) |
| Scripts fail in schtasks | Ensure WSL distro name is correct (`wsl -l -v` to check) |
| Path issues | Use WSL paths (`/mnt/c/Users/...`), not Windows paths |
| Cron not firing in WSL | Run `sudo service cron status` — start with `sudo service cron start` |

---

## Linux

### crontab

```bash
crontab -e

# Add:
0 6 * * * cd /path/to/content-pipeline && ./scripts/daily-discover.sh >> logs/daily-discover.log 2>&1
0 6 * * 5 cd /path/to/content-pipeline && ./scripts/weekly-analyze.sh >> logs/weekly-analyze.log 2>&1
```

### systemd timer (alternative)

For systemd-based systems, create a timer unit. This is more robust than crontab for servers:

```bash
# /etc/systemd/system/viralcommand-daily.timer
[Unit]
Description=Viral Command Daily Discovery

[Timer]
OnCalendar=*-*-* 06:00:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
```

Pair with a matching `.service` file that runs the script. Enable with:

```bash
sudo systemctl enable --now viralcommand-daily.timer
```

---

## Testing

Always test scripts manually before enabling cron:

```bash
# Test daily discovery (dry run — no changes)
./scripts/daily-discover.sh --dry-run

# Test weekly analysis (dry run)
./scripts/weekly-analyze.sh --dry-run

# Run for real (once)
./scripts/daily-discover.sh
./scripts/weekly-analyze.sh
```

Check output in `logs/` directory after each run.

---

## Schedule Reference

| Job | Schedule | UTC | EST | Script | Log |
|-----|----------|-----|-----|--------|-----|
| Daily Discovery | Every day | 06:00 | 01:00 AM | `scripts/daily-discover.sh` | `logs/daily-discover.log` |
| Weekly Analysis | Friday | 06:00 | 01:00 AM | `scripts/weekly-analyze.sh` | `logs/weekly-analyze.log` |

Both jobs are designed to be idempotent — safe to run multiple times. Use `--dry-run` to preview without side effects.
