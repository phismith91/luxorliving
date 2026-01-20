# TDD Workflow (pytest/HA)

- Tests first: write failing pytest covering happy, edge, and error paths; use HA fixtures and mock external I/O.
- Run tests to confirm failure, then implement minimal code; keep async/await correct and avoid blocking calls.
- Re-run tests, refactor with green bar; add regression tests for bugs.
- Coverage goal: ≥ 80% overall; no silent skips; keep tests deterministic (no real time.sleep/network).
- Command set: `python -m pytest tests/ -v`, `black custom_components/luxor_living tests`, `isort custom_components/luxor_living tests`.
