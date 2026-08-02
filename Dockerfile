# syntax=docker/dockerfile:1

# ──────────────────────────────────────
# Node stage — Node.js 22 for the last30days
# X client (vendored Twitter GraphQL, needs 22+)
# ──────────────────────────────────────
FROM node:22-bookworm-slim AS node

# ──────────────────────────────────────
# Runtime image
# ──────────────────────────────────────
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ffmpeg      — audio extraction for transcription
# gosu        — drop from root to the repo owner's UID at startup
# git/curl/jq — used by the pipeline commands
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        ffmpeg \
        git \
        gosu \
        jq \
        less \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# Claude Code — the runtime the /viral:* commands execute in
RUN npm install -g @anthropic-ai/claude-code \
    && npm cache clean --force

# Python dependencies (instaloader is commented out in requirements.txt because
# it is optional natively — in the image it is always available)
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt \
    && pip install instaloader \
    && rm /tmp/requirements.txt

# Unprivileged default user. The entrypoint re-maps this UID/GID to whoever owns
# the mounted repo, so bind-mounted data/ stays writable from the host.
RUN groupadd -g 1000 viral \
    && useradd -m -u 1000 -g 1000 -s /bin/bash viral \
    && mkdir -p /home/viral/.claude /home/viral/.config \
    && chown -R viral:viral /home/viral

COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /app
COPY --chown=viral:viral . /app

ENV HOME=/home/viral \
    PATH="/home/viral/.local/bin:$PATH" \
    PYTHONPATH=/app \
    GOVIRALBRO_DOCKER=1

# Recon Intelligence UI
EXPOSE 5001

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["claude"]
