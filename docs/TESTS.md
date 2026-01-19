# TESTS - LUXORliving

This document explains the test strategies and how we run tests for the project.

## Test Tiers
- Smoke tests (`pytest -m smoke`) — quick, critical checks used in early CI steps
- Integration subset (`pytest -m integration`) — medium-length tests that run in the QA matrix for PR feedback
- Full tests (`pytest`) — full suite run in CI matrix per axis
- E2E tests (`pytest -m e2e`) — manual / on-demand end-to-end style tests (trigger via GitHub Actions workflow)

## Running tests locally
- Quick smoke: `./venv/bin/python -m pytest tests/ -q -m "smoke and not enable_socket"`
- Integration subset: `./venv/bin/python -m pytest tests/ -q -m "integration and not enable_socket"`
- Full suite: `./venv/bin/python -m pytest tests/ -q -m "not enable_socket"`
- E2E (on-demand): `./venv/bin/python -m pytest tests/ -q -m "e2e and not enable_socket"`

## CI jobs
- `qa_matrix` job: runs Smoke → Integration subset → Full tests for each Python/HA axis
- `hacs-validation` job: validates `hacs.json` and `manifest.json` and runs HACS-related tests
- `render-plantuml` job: renders diagrams for PR previews
- `e2e-consent` job: on-demand workflow job to run E2E consent tests and upload logs

## Adding tests
- Mark small/focused tests as `@pytest.mark.smoke` to get fast PR feedback
- Mark medium-length tests as `@pytest.mark.integration` to run in the QA matrix
- Use `@pytest.mark.e2e` sparingly for manual/integration tests (may require environment setup)

## Guidelines
- Never skip failing tests; add a failing test & fix code if needed
- Keep test data in `tests/` and add fixtures in `tests/conftest.py` when re-used across files
- Keep runtime-sensitive tests behind markers and skip them in CI where appropriate
