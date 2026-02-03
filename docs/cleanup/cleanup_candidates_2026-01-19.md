# Cleanup candidates — scan 2026-01-19

This is an initial, conservative list of files that appear to be unreferenced or
low-value and could be considered for archiving or deletion after review.

## Status: Actions Completed (2026-02-03)

### ✅ Release Notes Archived

Created `docs/archive/releases/` directory and moved old release notes:

- ✅ Moved `RELEASE_NOTES_v0.6.0.md` (root) → `docs/archive/releases/` (superseded by v0.6.1)
- ✅ Moved `docs/releases/RELEASE_NOTES_v0.6.0-beta.1.md` → `docs/archive/releases/` (beta version)
- ✅ Moved `docs/releases/RELEASE_NOTES_v0.5.4.3.md` → `docs/archive/releases/` (old patch version)

**Current state:**
- Active: `docs/releases/RELEASE_NOTES_v0.6.1.md` (latest stable release)
- Archived: 3 old release notes in `docs/archive/releases/`

### ✅ Scripts Review Completed

**Scripts to KEEP (actively used in CI/workflows):**
- `scripts/deploy_release.sh` — Used in automated deployments, beta releases
- `scripts/release_automation.sh` — Used in QA Matrix workflow (qa_matrix.yml) and Release Checks workflow (release_checks.yml)
- `scripts/delppy` — Wrapper script for deploy_release.sh, provides shorter command alias

**Finding:** All three scripts are actively referenced in:
- `.github/workflows/qa_matrix.yml`
- `.github/workflows/release_checks.yml`
- Multiple documentation files (RELEASE_OPERATIONS.md, CONTRIBUTOR_WORKFLOW.md, etc.)

**Recommendation:** No script removal needed at this time.

---

## Original Candidate List (For Reference)

### Unreferenced docs (candidates) - NOT FOUND

**Note:** The following files listed in the original scan do not exist in the repository:

- docs/archive/ION_TEMPERATURE_HA_LOGGING.md
- docs/archive/AUDIT_REPORT_v0.5.2.md
- docs/archive/RELEASE_NOTES_v0.5.1.md
- docs/archive/RELEASE_NOTES_v0.3.6.md
- docs/archive/RELEASE_NOTES_v0.5.3.md
- docs/archive/RELEASE_NOTES_v0.3.3.md
- docs/archive/RELEASE_NOTES_v0.3.5.md
- docs/archive/RELEASE_NOTES_v0.3.4.md
- docs/archive/RELEASE_NOTES_v0.5.4-beta.1.md
- docs/archive/ARCHITECTURE_REVIEW_AUTO_DISCOVERY.md

**Analysis:** These files may have been removed in previous cleanup efforts or never existed in the current repository state.

### PDF/Binary Files - KEPT

Large binary documentation files are actively referenced and kept:
- `docs/LUXORliving_API_Documentation_EN.pdf` — Referenced in documentation
- `docs/weinzierl-777-knx-ip-baos-5193-manual-de.pdf` — KNX hardware reference

---

## Archival Policy (Recommendations)

Based on this cleanup effort, recommend adding to `RELEASE_OPERATIONS.md`:

1. **Release Notes Archival:**
   - Keep only the latest stable release notes in `docs/releases/`
   - Move superseded versions to `docs/archive/releases/`
   - Archive beta/pre-release versions after stable release
   - Never delete release notes (historical value)

2. **Review Frequency:**
   - Review `docs/releases/` after each stable release
   - Archive previous stable versions older than 2 minor versions
   - Keep beta versions until superseded by stable release

3. **Script Maintenance:**
   - Before removing scripts, check references in:
     - `.github/workflows/*.yml`
     - `docs/*.md` files
     - `AGENTS.md` and copilot instructions
   - Scripts referenced in CI/CD should be clearly marked in documentation
