# Tests

## How to run

- `python -m pytest tests/ -v`
- `python -m pytest --cov=custom_components.luxor_living tests/` (coverage optional)

## Current status

- Total tests: 287 (unit + integration-style)
- Key suites: push client/webhook, integration_state, platform detector, override handler, coordinator auth, circuit breaker, platform entities.
- Quality gates: black/isort, README/CHANGELOG validation, HACS structure check.

## CI expectations

- All tests must pass on the supported HA/Python matrix.
- Release checks validate version consistency (manifest, README, CHANGELOG) and documentation links.
