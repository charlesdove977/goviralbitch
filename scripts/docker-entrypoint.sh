#!/usr/bin/env bash
# Viral Command — Container Bootstrap
# Docker equivalent of scripts/init-viral-command.sh: matches the container user
# to the owner of the mounted repo, prepares the data tree, seeds .env, and wires
# the /viral:* commands + last30days skill into Claude Code.
# Idempotent — runs on every container start.

set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
APP_USER="viral"
APP_HOME="/home/viral"

# ──────────────────────────────────────
# Step 0: Match the container user to the host
# ──────────────────────────────────────
# The repo is bind-mounted, so anything written to data/ must come out owned by
# the host user. PUID/PGID override the auto-detected owner of the mount.
# VIRAL_DROPPED_PRIVS guards against re-entry when the target user *is* root.
if [[ "$(id -u)" == "0" ]] && [[ -z "${VIRAL_DROPPED_PRIVS:-}" ]]; then
    TARGET_UID="${PUID:-$(stat -c %u "$APP_DIR")}"
    TARGET_GID="${PGID:-$(stat -c %g "$APP_DIR")}"

    if [[ "$(id -g "$APP_USER")" != "$TARGET_GID" ]]; then
        groupmod -o -g "$TARGET_GID" "$APP_USER"
    fi
    if [[ "$(id -u "$APP_USER")" != "$TARGET_UID" ]]; then
        usermod -o -u "$TARGET_UID" "$APP_USER"
    fi

    for dir in "$APP_HOME" "$APP_HOME/.claude" "$APP_HOME/.config"; do
        [[ -d "$dir" ]] || continue
        if [[ "$(stat -c %u "$dir")" != "$TARGET_UID" ]] || [[ "$(stat -c %g "$dir")" != "$TARGET_GID" ]]; then
            chown -R "$TARGET_UID:$TARGET_GID" "$dir"
        fi
    done

    export VIRAL_DROPPED_PRIVS=1
    exec gosu "$APP_USER" "$0" "$@"
fi

cd "$APP_DIR"

if ! touch "$APP_DIR/.viral-write-test" 2>/dev/null; then
    echo "ERROR: $APP_DIR is not writable as uid $(id -u):$(id -g)." >&2
    echo "Set PUID/PGID to a user that can write the repo, e.g.:" >&2
    echo "  PUID=\$(id -u) PGID=\$(id -g) docker compose up -d" >&2
    exit 1
fi
rm -f "$APP_DIR/.viral-write-test"

# ──────────────────────────────────────
# Step 1: Data directories
# ──────────────────────────────────────
for dir in \
    data \
    data/analytics \
    data/analytics/raw \
    data/insights \
    data/hooks \
    data/topics \
    data/scripts \
    data/angles \
    data/recon \
    data/recon/competitors \
    data/recon/reports \
    data/recon/cache \
    data/recon/logs \
    logs; do
    mkdir -p "$APP_DIR/$dir"
done

# ──────────────────────────────────────
# Step 2: Data files
# ──────────────────────────────────────
for file in \
    data/hooks.jsonl \
    data/scripts.jsonl \
    data/angles.jsonl \
    data/analytics/analytics.jsonl; do
    [[ -f "$APP_DIR/$file" ]] || : > "$APP_DIR/$file"
done

# ──────────────────────────────────────
# Step 3: API key configuration
# ──────────────────────────────────────
if [[ ! -f "$APP_DIR/.env" ]] && [[ -f "$APP_DIR/.env.example" ]]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "Created .env from .env.example — add your API keys, then restart:"
    echo "  docker compose up -d --force-recreate"
fi

# ──────────────────────────────────────
# Step 4: Command + skill accessibility
# ──────────────────────────────────────
mkdir -p "$APP_HOME/.claude/commands" "$APP_HOME/.claude/skills"

for cmd in "$APP_DIR"/.claude/commands/viral-*.md; do
    [[ -e "$cmd" ]] || continue
    ln -sfn "$cmd" "$APP_HOME/.claude/commands/$(basename "$cmd")"
done

if [[ -d "$APP_DIR/skills/last30days" ]]; then
    ln -sfn "$APP_DIR/skills/last30days" "$APP_HOME/.claude/skills/last30days"
fi

# last30days reads ~/.config/last30days/.env — point it at the project .env
mkdir -p "$APP_HOME/.config/last30days"
ln -sfn "$APP_DIR/.env" "$APP_HOME/.config/last30days/.env"

exec "$@"
