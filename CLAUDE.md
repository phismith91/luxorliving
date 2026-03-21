# CLAUDE.md - LUXORliving Integration

Fast orientation for Claude Code. Detailed project context lives in
`.github/copilot/CONTEXT.md` (Single Source of Truth). Setup commands, test
instructions, and quality gates are in `AGENTS.md`.

## Project Summary

Home Assistant custom integration for Theben LUXORliving KNX systems via the
IP1 interface (BAOS REST API). HACS-ready, Python 3.13, pytest, HA 2026.1.x.
Current stable version: v0.6.3.

## Dual-AI Setup

This repo uses **GitHub Copilot** (primary agent system) and **Claude Code**
(you) interchangeably. The `.github/copilot/` folder contains Copilot agent
definitions — treat them as domain-expert documentation and project conventions.

## Critical: SSH Rule

Local `~/.ssh/config` has invalid entries. Always use `-F /dev/null`:

```bash
ssh -F /dev/null phil@100.97.159.88 "command"
GIT_SSH_COMMAND='ssh -F /dev/null' git push
```

## One-Time Setup (new machine / fresh clone)

```bash
pip install pre-commit
pre-commit install   # installs .git/hooks/pre-commit — runs automatically on every commit
```

## Before Every Commit

```bash
pre-commit run --all-files          # black, isort, flake8, bandit, prettier, file checks
python -m pytest tests/ -v -m "not enable_socket"
```

Never skip these — CI runs the exact same checks and will fail if you do not.

## Key Files

| File                              | Purpose                                                 |
| --------------------------------- | ------------------------------------------------------- |
| `AGENTS.md`                       | Setup, testing, release process, quality gates          |
| `.github/copilot/CONTEXT.md`      | Architecture, current status, agent coordination (SSoT) |
| `.github/copilot-instructions.md` | SSH deployment & release workflow                       |
| `custom_components/luxor_living/` | Integration source                                      |
| `tests/`                          | pytest test suite (301 tests)                           |
| `docs/`                           | Architecture, KNX implementation, installation          |

## Domain Reference (Copilot Agents)

Defined in `.github/copilot/agent_*.md` — read these when working in their area:

| Agent                      | Domain                                                |
| -------------------------- | ----------------------------------------------------- |
| `agent_architect.md`       | Architecture & code quality (primary authority)       |
| `agent_knx_protocol.md`    | KNX specs, DPT, group addresses                       |
| `agent_luxor_expert.md`    | Theben IP1 hardware & LXP file format                 |
| `agent_testing.md`         | Test strategy, CI/CD, coverage                        |
| `agent_release_manager.md` | Releases & merges (exclusive merge authority to main) |
| `agent_hacs_compliance.md` | HACS & HA core standards                              |
| `agent_defect_tracker.md`  | Bug triage & regression tracking                      |

## Key Conventions

- Async patterns only — no `asyncio.run()` in integration code
- `_attr_*` attributes for HA entity properties
- Type hints on all public functions
- Never push directly to `main` — PR-only workflow, Release Manager merges
- GitHub token: `~/.github-token` (see `.github/copilot/GITHUB_TOKEN_SETUP.md`)
