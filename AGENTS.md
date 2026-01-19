# AGENTS.md - LUXORliving Home Assistant Integration

## Project Overview

LUXORliving Home Assistant Integration for controlling LUXOR Living KNX/BAOS
devices via REST API.

**Tech Stack:**

- Python 3.11+
- Home Assistant Custom Component
- KNX/BAOS REST API
- pytest for testing

## Setup Commands

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements_dev.txt
pip install -r requirements_style.txt

# Run tests
python -m pytest tests/ -v

# Code formatting
black custom_components/luxor_living/ tests/
isort custom_components/luxor_living/ tests/

# Type checking (optional)
mypy custom_components/luxor_living/
```

## Testing Instructions

- **Run all tests:** `python -m pytest tests/ -v`
- **Run specific test:** `python -m pytest tests/test_config_flow.py -v`
- **Coverage report:**
  `python -m pytest --cov=custom_components.luxor_living tests/`
- **All tests must pass before commits**
- Tests are located in `tests/` directory

## Code Style Guidelines

- **Formatting:** Use `black` (line length 100, Python 3.13+)
- **Import sorting:** Use `isort` (black compatible, profile=black)
- **Type hints:** Required for all functions (checked with `mypy`)
- **Docstrings:** Use Google style for classes and public methods
- **No emojis** in code comments or user-facing messages
- **Pre-commit:** Use `pre-commit` hooks to enforce formatting, sorting and
  basic checks. Run once in your checkout:

```bash
pip install -r requirements_style.txt
pre-commit install
# Optional: run all hooks locally
pre-commit run --all-files
```

CI also runs `pre-commit run --all-files` as a fast, fail-fast gate on pushes
and PRs.

## CI workflow behavior

- **Pushes (feature branches):** A lightweight preflight workflow runs automatic
  checks (black/isort + quick smoke tests). This provides a fast fail‑fast
  feedback loop for common issues.
- **Pull requests:** A fast PR checks workflow runs on each PR update (lint +
  smoke). To run the full QA matrix (Python × HA) you can either add the label
  `run-qa-matrix` to the PR or use the Actions tab to manually dispatch the QA
  Matrix workflow.
- **E2E / long tests:** These are intentionally run on demand (via
  workflow_dispatch) or on scheduled runs to save CI time.

Guidelines:

- Add `run-qa-matrix` label to request the full QA matrix only after the PR is
  review-ready or heavy changes are made.
- You can also trigger the QA Matrix by commenting `/run-qa-matrix` on the PR —
  the CI will add the label and start the matrix.
- Use pre-commit locally before pushing to avoid trivial pipeline failures.

## Branch protection

See `docs/BRANCH_PROTECTION.md` for recommended `main` branch protection
settings and an example `gh api` payload an admin can use to apply them.

Admins can apply the recommended settings automatically using
`scripts/apply_branch_protection.sh` (requires GH CLI and repo admin
permissions):

```bash
# Requires gh cli and admin rights
./scripts/apply_branch_protection.sh
# Quick check
./scripts/check_branch_protection.sh
```

## File Structure

```
custom_components/luxor_living/
├── __init__.py          # Main integration setup
├── config_flow.py       # Configuration UI
├── const.py             # Constants
├── lxp_parser.py        # LXP file parser
├── rest_client.py       # BAOS REST API client
├── knx_gateway.py       # KNX gateway abstraction
├── entity_mapper.py     # Entity mapping logic
├── light.py             # Light platform
├── switch.py            # Switch platform
├── cover.py             # Cover platform
├── climate.py           # Climate platform
├── sensor.py            # Sensor platform
└── binary_sensor.py     # Binary sensor platform
```

## Build & Deploy

### Local Development

No build step required - Python source files are used directly.

### Pre-Release Testing (SSH to Remote HA)

**IMPORTANT:** Remote HA uses s6-overlay (not systemd) and SSH key
authentication.

```bash
# Deploy to remote HA (100.97.159.88 via Tailscale)
# Step 1: Sync to temp directory
ssh -F /dev/null phil@100.97.159.88 "mkdir -p /tmp/luxor_deploy"
rsync -avz --exclude="__pycache__" \
  -e "ssh -F /dev/null" \
  custom_components/luxor_living/ \
  phil@100.97.159.88:/tmp/luxor_deploy/

# Step 2: Copy with sudo to final location
ssh -F /dev/null phil@100.97.159.88 \
  "sudo cp -r /tmp/luxor_deploy/* /config/custom_components/luxor_living/ && \
   rm -rf /tmp/luxor_deploy"

# Step 3: Restart HA manually via UI (http://100.97.159.88:8123)
# Settings → System → Restart
```

**SSH Configuration:**

- Host: `100.97.159.88` (Tailscale VPN)
- User: `phil`
- Auth: SSH key (`~/.ssh/id_rsa`)
- Always use `-F /dev/null` to bypass invalid local SSH config
- Files owned by root → use `sudo` for file operations

## Release Process

### Before Release

1. **Run all tests:** `python -m pytest tests/ -v` (all must pass)
2. **Optional:** Deploy to remote HA for pre-release testing
3. **Update version and release notes:**
   - `custom_components/luxor_living/manifest.json` → "version" field
   - `CHANGELOG.md` with release summary
   - **IMPORTANT:** Create `docs/releases/RELEASE_NOTES_v<VERSION>.md` with
     detailed release notes (Release Checks verifies this)
4. **Commit and tag:**
   ```bash
   git add -A
   git commit -m "Release vX.Y.Z"
   git tag -a vX.Y.Z -m "Release notes..."
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin main
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin vX.Y.Z
   ```
5. **Create GitHub release:**
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z - Title" \
     --notes-file docs/releases/RELEASE_NOTES_v<VERSION>.md --latest
   ```

### Release Notes Standard

- **Location:** `docs/releases/RELEASE_NOTES_v<VERSION>.md` (mandatory)
- **Content:** Must include version tag (e.g., `v0.6.1`) and release description
- **Validation:** Release Checks workflow validates file exists and contains
  version

### Git Operations

**CRITICAL:** Always use `GIT_SSH_COMMAND='ssh -F /dev/null'` for git
operations:

- Local `~/.ssh/config` has invalid entries
- Example: `GIT_SSH_COMMAND='ssh -F /dev/null' git push origin main`

## Security Guidelines

- **NEVER commit credentials** (passwords, tokens, API keys)
- SSH uses key authentication (no passwords in code)
- Deployment scripts can be committed (use SSH keys)
- If credentials accidentally committed:
  1. Reset git history: `git reset --hard HEAD~N`
  2. Force push: `GIT_SSH_COMMAND='ssh -F /dev/null' git push -f origin main`
  3. Delete tags if needed
  4. **Immediately change the compromised credential**

## Quality Gates

Before any commit/release:

- ✅ All tests passing (`pytest`)
- ✅ Code formatted (`black`, `isort`)
- ✅ Type checking passes (`mypy`) - optional
- ✅ Documentation updated
- ✅ Optional: Pre-release testing on remote HA

## Important Documentation

- `docs/ARCHITECTURE_DECISION.md` - Architecture decisions
- `docs/INSTALLATION.md` - Installation guide
- `docs/KNX_IMPLEMENTATION.md` - KNX implementation details
- `docs/TESTS.md` - Testing documentation
- `docs/RELEASE_OPERATIONS.md` - Release procedures
- `.github/copilot-instructions.md` - GitHub Copilot deployment workflows
- `.github/copilot/CONTEXT.md` - Project status & agent coordination
- `.github/copilot/skills/` - Context engineering skills for multi-agent
  optimization

## Common Commands

```bash
# Analyze LXP file
python scripts/analyze_lxp.py docs/Hauptwohnung.lxp

# Validate LXP file
python scripts/validate_lxp.py docs/Hauptwohnung.lxp

# Monitor KNX telegrams
python scripts/monitor_knx_telegrams.py

# Setup integration for testing
python scripts/setup_integration.sh
```

## Home Assistant Specifics

- Custom integration installed in `config/custom_components/luxor_living/`
- Configuration via UI (Configuration → Integrations)
- Diagnostic data can be downloaded via UI
- Services registered under `luxor_living` domain
- Logs in HA UI: Settings → System → Logs

## Conventions

- Use Home Assistant's `async` patterns (not `asyncio.run()` in integration
  code)
- Follow HA integration quality checklist
- Use `_attr_*` attributes for entity properties
- Implement `async_setup_entry` and `async_unload_entry`
- Entity unique_id must be stable across restarts
