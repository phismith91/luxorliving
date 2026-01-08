# Release Incidents

## 2026-01-08 — v0.6.0-beta.1-3: Silent startup failure (no logs, all entities error)
- **Impact:** Integration silently failed to load; no log entries; all configured entities showed "unavailable" error state; users had no way to diagnose the failure.
- **Root cause (after root-cause analysis):** Silver compliance coordinator refactoring added `config_entry` parameter to `__init__` and passed it correctly in `__init__.py`, but **forgot to pass `config_entry` to `super().__init__()` call in `DataUpdateCoordinator`**. Modern Home Assistant (2026.8+) requires this parameter. Missing parameter caused RuntimeError ("Frame helper not set up") on coordinator instantiation, which happened early in `async_setup_entry` and was silently swallowed, preventing any setup logs.
- **Fix:** Pass `config_entry=entry` to `super().__init__()` in [custom_components/luxor_living/coordinator.py](custom_components/luxor_living/coordinator.py).
- **Version:** v0.6.0-beta.4 (correct, deployed).
- **Prevention:**
  - Test coordinator instantiation against actual Home Assistant code during Silver compliance changes.
  - Check Home Assistant DataUpdateCoordinator signature when refactoring coordinators.
  - Early-stage testing in HA (not just unit tests) catches silent runtime failures.

## 2026-01-08 — v0.6.0-beta.2 asset blocked
- **Impact:** HACS download installed asset with stale version metadata; integration produced no logs and HACS failed to load properly.
- **Root cause:** GitHub release marked immutable prevented replacing incorrect asset (beta.1 manifest). Release asset size differed (69 KB) vs rebuilt (139 KB).
- **Fix:** Incremented version to v0.6.0-beta.3, rebuilt zip from current tree, created new prerelease with correct asset.
- **Prevention:**
  - Always regenerate asset after version bump and before creating release.
  - Verify manifest and health endpoint versions match tag before packaging.
  - Avoid creating immutable releases until asset upload succeeds; otherwise create a new tag if immutable.
