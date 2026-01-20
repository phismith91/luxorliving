# Testing Rules (HA/Python)

- Use pytest (`python -m pytest tests/ -v`); no skipped/xfail without justification; keep coverage ≥ 80% (unit + integration). 
- Follow TDD: write failing test first, minimal code to pass, refactor with tests green; add regressions for every bug fix.
- Prefer async tests for HA code; use Home Assistant test helpers and fixtures; avoid real network/KNX/HTTP calls—mock clients and clock.
- Keep tests deterministic: freeze time where needed, avoid sleeps; assert logs/messages explicitly.
- Ensure entities use stable unique_id and config entry unload/reload paths have tests.
- Run formatting (black, isort) and static checks locally before PRs; fail fast on warnings treated as errors.
