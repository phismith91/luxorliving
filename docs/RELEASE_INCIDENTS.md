# Release Incidents

## 2026-01-08 — v0.6.0-beta.2 asset blocked
- **Impact:** HACS download installed asset with stale version metadata; integration produced no logs and HACS failed to load properly.
- **Root cause:** GitHub release marked immutable prevented replacing incorrect asset (beta.1 manifest). Release asset size differed (69 KB) vs rebuilt (139 KB).
- **Fix:** Incremented version to v0.6.0-beta.3, rebuilt zip from current tree, created new prerelease with correct asset.
- **Prevention:**
  - Always regenerate asset after version bump and before creating release.
  - Verify manifest and health endpoint versions match tag before packaging.
  - Avoid creating immutable releases until asset upload succeeds; otherwise create a new tag if immutable.
