# Contributing to Viral Command

Thanks for your interest in contributing. This project is a Claude Code command system — contributions are typically `.md` command files, Python scripts, or bash scripts.

---

## Reporting Bugs

Open a [GitHub Issue](https://github.com/charlieautomates/viral-command/issues) with:

- Which command you ran (e.g., `/viral:discover --deep`)
- What you expected to happen
- What actually happened
- Your OS (macOS, Linux, Windows/WSL)
- Python and Node.js versions

---

## Suggesting Features

Open a GitHub Issue with the `enhancement` label. Describe:

- What problem you're solving
- How you'd expect it to work
- Which command(s) it would affect

---

## Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test your changes by running the affected command(s)
5. Commit with a clear message describing what changed and why
6. Push to your fork and open a PR against `main`

### Code Style

- **Bash scripts**: Use `set -euo pipefail` at the top. Quote variables. Use `#!/usr/bin/env bash`.
- **Python**: Follow PEP 8. Use type hints where practical.
- **Claude Code commands** (`.md` files): Follow the existing phase-based structure. Include rules, validation, and persistence sections.
- **Schemas**: JSON Schema draft-07. Include `description` fields on properties.

### What to Avoid

- Don't add external database dependencies (data stays in local JSON/JSONL files)
- Don't add browser automation (API/CLI only)
- Don't modify `data/cta-templates.json` structure without updating dependent commands
- Don't commit `.env` files or API keys

---

## Project Structure

See [README.md](README.md#architecture) for the full directory layout. Key areas:

- `.claude/commands/viral-*.md` — Pipeline commands (the core product)
- `schemas/` — Data contracts (changes here affect all commands)
- `scripts/` — Automation and utility scripts
- `recon/` — Competitor analysis module (Python)
- `scoring/` — Topic scoring engine (Python)

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
