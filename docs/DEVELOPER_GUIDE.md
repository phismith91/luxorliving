# Developer Guide — LUXORliving KNX Integration

**Audience:** Contributors who want to develop, test, or extend the integration. Assumes familiarity with Python, Home Assistant custom integrations, and basic KNX concepts.

---

## Architecture Overview

The integration follows the HA coordinator pattern. Key components:

| File / Module | Responsibility |
| --- | --- |
| `config_flow.py` | Setup wizard, reconfigure, options flow (sections: standard + push webhook) |
| `coordinator.py` | HA DataUpdateCoordinator — polls BAOS REST every `scan_interval` |
| `knx_gateway.py` | KNX/IP tunneling/routing connection, telegram send/receive, circuit breaker |
| `entity_mapper.py` | Parses LXP file → maps datapoints → creates HA entity definitions |
| `lxp_parser.py` | XML parser for `.lxp` project files (uses defusedxml) |
| `push_view.py` | HA HTTP view for `/api/luxor_living/push` webhook |
| `push_client.py` | WebSocket client connecting to external forwarder |
| `diagnostics.py` | HA diagnostics API handler |
| `__init__.py` | Integration setup/teardown, runtime_data wiring |
| `platform/*.py` | Platform modules: `light.py`, `cover.py`, `climate.py`, `sensor.py`, `binary_sensor.py`, `switch.py` |

For the full architecture diagram and design decisions see:

- [Architecture Overview](ARCHITECTURE_OVERVIEW.md) — component diagram, data flows, design rationale
- [Architecture Decisions](ARCHITECTURE_DECISION.md) — why REST over tunneling for state reads, coordinator pattern choice, etc.

---

## Development Environment Setup

```bash
# Clone the repo
git clone git@github.com:phismith91/luxorliving.git
cd luxorliving

# Create virtual environment
python3.14 -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install -e ".[dev]"
# Optional: install mutation testing tooling
pip install -e ".[mutation]"

# Install pre-commit hooks
pre-commit install
```

---

## Branching Model

| Branch prefix | Purpose | Target |
| --- | --- | --- |
| `main` | Stable, release-ready | — |
| `feature/<name>` | New features | PR → main |
| `fix/<name>` | Bug fixes | PR → main |
| `hotfix/<name>` | Critical production fixes | PR → main |

**Rules:**
- Never push directly to `main`
- All merges go through a PR with CI green
- GitHub branch protection requires reviews + green required checks on `main`
- Pre-commit hooks must pass before every commit

See [Branch Protection](BRANCH_PROTECTION.md) for the enforced GitHub settings.

---

## Pre-commit Hooks

The following checks run on every commit:

| Hook | Tool | What it checks |
| --- | --- | --- |
| Code formatting | `black` | Consistent code style |
| Import order | `isort` | Sorted imports |
| Linting | `flake8` | PEP 8 violations, unused imports |
| Security | `bandit` | Common security anti-patterns |
| Markdown/YAML | `prettier` | Formatting of docs and workflow files |
| Whitespace | built-in | Trailing spaces, EOF newlines |
| Merge conflicts | built-in | Leftover conflict markers |

Run all hooks manually:

```bash
pre-commit run --all-files
```

---

## Running Tests

```bash
# Full test suite (excludes socket tests for local runs)
python -m pytest tests/ -m "not enable_socket" -v

# With coverage
python -m pytest tests/ --cov=custom_components/luxor_living --cov-report=xml -m "not enable_socket"

# Single test file
python -m pytest tests/test_config_flow.py -v

# Fast mode (pre-push check)
make pre-push

# Mutation testing (manual / on-demand)
make mutation
```

296 tests across these categories:

| Category | Files | What's tested |
| --- | --- | --- |
| Unit | `test_entity_mapper*.py`, `test_lxp_*.py` | Parser, mapper logic |
| Integration | `test_config_flow.py`, `test_options_flow.py` | Config/options flow |
| Platform | `test_light.py`, `test_cover.py`, etc. | Entity behavior per platform |
| Feature | `test_push_*.py`, `test_circuit_breaker.py`, `test_diagnostics.py` | Push webhook, breaker, diagnostics |
| E2E | `test_e2e_consent.py`, `test_integration.py` | Full integration lifecycle |

See [Testing Guide](TESTS.md) for test-writing guidelines and CI details.

---

## CI/CD

Two main workflows in `.github/workflows/`:

**`ci-cd.yml`** — runs on every PR and push to `main`:

1. Install dependencies
2. Run `pytest` with coverage (`--cov=custom_components/luxor_living`)
3. Upload coverage to Codecov (token: `CODECOV_TOKEN` secret)
4. On merge to `main`: auto-update the test count badge in `README.md`

**`release.yml`** — triggered by pushing a version tag:

1. Validate `manifest.json` version matches the tag base version
2. Build the integration ZIP
3. Validate ZIP structure (HACS-compatible)
4. Create GitHub release (pre-release if tag contains `-rc`, `-beta`, `-alpha`)

**`mutation.yml`** — runs scheduled or manual mutation testing with `mutmut` against the smoke test subset to catch weak assertions that coverage alone can miss.

---

## Release Process

```bash
# 1. Bump version (creates PR automatically)
gh workflow run bump-version.yml -f version=X.Y.Z -f push_tag=false

# 2. Review and merge the PR (CI must be green)

# 3. Tag and push (triggers release.yml)
git tag vX.Y.Z
git push origin vX.Y.Z
```

**Pre-release tags** (`v0.8.0-rc.1`, `v0.8.0-beta.1`, etc.) are published as GitHub pre-releases. Stable tags (`v0.8.0`) are published as the latest release.

For the full automated release protocol see `.github/copilot/agent_release_manager.md`.

---

## Adding a New Platform

1. Create `custom_components/luxor_living/<platform>.py` following the pattern of `light.py`
2. Register the platform in `__init__.py` via `PLATFORMS`
3. Add entity mapping logic in `entity_mapper.py` (new `EntityType` and DPT mapping)
4. Add LXP role detection in `lxp_parser.py` if needed
5. Write tests in `tests/test_<platform>.py`
6. Update `REFERENCE.md` with the new platform entry

---

## Key Design Decisions

- **REST for polling, KNX for commands:** State reads use the BAOS REST API (reliable, authenticated). Commands use KNX/IP tunneling for low latency.
- **Coordinator pattern:** All entities share one coordinator; no per-entity polling.
- **LXP over ETS:** The integration uses LXP project files (LUXORPlug export), not ETS project files — simpler structure, same group address data.
- **Circuit breaker:** Protects against gateway downtime without filling HA logs with timeouts.
- **No hardcoded versions:** HA version constraints are managed in `hacs.json` and CI matrix only.

For full rationale see [Architecture Decisions](ARCHITECTURE_DECISION.md).

---

## Security Guidelines

- **Never commit credentials** — passwords, tokens, or API keys
- If credentials are accidentally committed: `git reset --hard HEAD~N` + force push + rotate the credential immediately
- See [SECURITY.md](../SECURITY.md) for the vulnerability reporting process

---

## Further Reading

- [Architecture Overview](ARCHITECTURE_OVERVIEW.md)
- [Architecture Decisions](ARCHITECTURE_DECISION.md)
- [Testing Guide](TESTS.md)
- [Release Operations](RELEASE_OPERATIONS.md)
- [Full Reference](REFERENCE.md)
