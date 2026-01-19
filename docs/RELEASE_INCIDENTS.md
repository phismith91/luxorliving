# Release Incidents

## 2026-01-08 — v0.6.0-beta.1-4: HACS zip structure incorrect

- **Impact:** HACS extracted zip incorrectly creating nested
  `/config/custom_components/luxor_living/custom_components/luxor_living/`
  instead of `/config/custom_components/luxor_living/`. Integration files not
  found, silent load failure.
- **Root cause:** Zip created from repo root with
  `zip -r /tmp/luxor_living.zip custom_components/luxor_living` instead of from
  within the integration directory with `zip -r /tmp/luxor_living.zip .`.
- **Fix:** Rebuild zip from `custom_components/luxor_living/` directory so files
  are at zip root.
- **Version:** v0.6.0-beta.5 (correct, deployed).
- **Prevention:**
  - Always build release zips from within the integration directory
    (`cd custom_components/luxor_living && zip -r ...`).
  - Test HACS installation in a clean environment before releasing.
  - Verify extracted structure on remote HA:
    `/config/custom_components/luxor_living/manifest.json` must exist (not
    nested).

### CI Enforcement: Release Checks

- **Action taken:** Added `scripts/check_release_notes.sh` and a GitHub Actions
  workflow `.github/workflows/release_checks.yml` which runs on `pull_request`
  and `push` to `main` and performs:
  - `./scripts/validate_readme.sh` (README/CHANGELOG quality gates)
  - `./scripts/check_release_notes.sh` (ensures `RELEASE_NOTES_v<version>.md`
    exists for the manifest version)
  - `./scripts/release_automation.sh --dry-run` (validates zip build and
    packaging steps)
- **Benefit:** Prevents missing README/changelog updates and zip-building
  mistakes from reaching `main` or being merged without validation.
- **Recommendation:** Configure branch protection to require this workflow to
  pass on `main` merges and optionally fail CI if `RELEASE_NOTES_v<version>.md`
  is missing.

### Branch protection enforced (2026-01-09)

- **Action taken:** Branch protection for `main` now requires the GitHub Actions
  workflow **"Release Checks"** to pass (strict mode) and enforces the rule for
  administrators.
- **Benefit:** Prevents merges to `main` unless release validation
  (README/CHANGELOG checks, release notes presence, and dry-run validation)
  passes.

### Policy: Release Notes Location

- **Policy:** Keep the current release notes (the release being published) at
  repository root as `RELEASE_NOTES_v<version>.md`. Move only older release
  notes into `docs/releases/` to retain a clean root while keeping the active
  release accessible.
- **Script behavior:** Release scripts (`update_readme_release.sh`,
  `check_release_notes.sh`, `release_automation.sh`) now prefer the root file
  and fall back to `docs/releases/`.

## 2026-01-09 — Missing `RELEASE_NOTES_v<version>.md` caused README to omit changelog details

- **Impact:** The README's "Current Release" block lacked the detailed changelog
  highlights because no `RELEASE_NOTES_v0.6.0.md` existed. This caused a
  disparity between `CHANGELOG.md` (complete release details) and README
  (summary missing), confusing users and tooling.
- **Root cause:** Release process did not ensure a `RELEASE_NOTES_v<version>.md`
  file was created or updated from the `CHANGELOG.md` before running the README
  update script.
- **Fix:** Added `RELEASE_NOTES_v0.6.0.md` and ran
  `./scripts/update_readme_release.sh` to populate the README. Also extended
  `scripts/release_automation.sh` and `docs/RELEASE_OPERATIONS.md` to require a
  `RELEASE_NOTES_v<version>.md` or `--update-readme` to auto-generate/update it.
- **Prevention:**
  - Add `RELEASE_NOTES_v<version>.md` creation into the release checklist and
    automation script (done)
  - Ensure `scripts/update_readme_release.sh` is part of the automated release
    (release script calls it with `--update-readme` if needed)
  - Add a CI check to fail the release if README release block does not contain
    the expected version and highlights## 2026-01-09 — README release block
    outdated after release
- **Impact:** `README.md` still displayed the previous release (`v0.5.4.3`) even
  after `v0.6.0` was published. This can confuse users and automated validation
  checks.
- **Root cause:** The release notes block inside `README.md` (between
  `<!-- RELEASE_NOTES_START -->` and `<!-- RELEASE_NOTES_END -->`) was not
  updated during the release process.
- **Fix:** Updated `README.md` release block to reflect `v0.6.0` and release
  date. Added a validation step to the release checklist to compare the manifest
  and README release block before publishing.
- **Prevention:**
  - Add an automated pre-release check to ensure `README` release block matches
    `custom_components/luxor_living/manifest.json` version (see
    `RELEASE_OPERATIONS.md` step 0.1.5).
  - Include `README` release block update in the release script or CI job that
    assembles the release notes.

## 2026-01-08 — v0.6.0-beta.1-3: Silent startup failure (no logs, all entities error)

- **Impact:** Integration silently failed to load; no log entries; all
  configured entities showed "unavailable" error state; users had no way to
  diagnose the failure.
- **Root cause (after root-cause analysis):** Silver compliance coordinator
  refactoring added `config_entry` parameter to `__init__` and passed it
  correctly in `__init__.py`, but **forgot to pass `config_entry` to
  `super().__init__()` call in `DataUpdateCoordinator`**. Modern Home Assistant
  (2026.8+) requires this parameter. Missing parameter caused RuntimeError
  ("Frame helper not set up") on coordinator instantiation, which happened early
  in `async_setup_entry` and was silently swallowed, preventing any setup logs.
- **Fix:** Pass `config_entry=entry` to `super().__init__()` in
  [custom_components/luxor_living/coordinator.py](custom_components/luxor_living/coordinator.py).
- **Version:** v0.6.0-beta.4+ (correct, deployed).
- **Prevention:**
  - Test coordinator instantiation against actual Home Assistant code during
    Silver compliance changes.
  - Check Home Assistant DataUpdateCoordinator signature when refactoring
    coordinators.
  - Early-stage testing in HA (not just unit tests) catches silent runtime
    failures.

## 2026-01-08 — v0.6.0-beta.2 asset blocked

- **Impact:** HACS download installed asset with stale version metadata;
  integration produced no logs and HACS failed to load properly.
- **Root cause:** GitHub release marked immutable prevented replacing incorrect
  asset (beta.1 manifest). Release asset size differed (69 KB) vs rebuilt (139
  KB).
- **Fix:** Incremented version to v0.6.0-beta.3, rebuilt zip from current tree,
  created new prerelease with correct asset.
- **Prevention:**
  - Always regenerate asset after version bump and before creating release.
  - Verify manifest and health endpoint versions match tag before packaging.
  - Avoid creating immutable releases until asset upload succeeds; otherwise
    create a new tag if immutable.
