# Cleanup candidates — scan 2026-01-19

This is an initial, conservative list of files that appear to be unreferenced or low-value and could be considered for archiving or deletion after review.

## Unreferenced docs (candidates)
- docs/archive/ION_TEMPERATURE_HA_LOGGING.md  — old note, not referenced
- docs/archive/AUDIT_REPORT_v0.5.2.md
- docs/archive/RELEASE_NOTES_v0.5.1.md
- docs/archive/RELEASE_NOTES_v0.3.6.md
- docs/archive/RELEASE_NOTES_v0.5.3.md
- docs/archive/RELEASE_NOTES_v0.3.3.md
- docs/archive/RELEASE_NOTES_v0.3.5.md
- docs/archive/RELEASE_NOTES_v0.3.4.md
- docs/archive/RELEASE_NOTES_v0.5.4-beta.1.md
- docs/archive/ARCHITECTURE_REVIEW_AUTO_DISCOVERY.md
- docs/releases/RELEASE_NOTES_v0.6.0-beta.1.md
- docs/releases/RELEASE_NOTES_v0.5.4.3.md

Notes:
- Release notes under `docs/archive/` are historical — prefer moving to `docs/releases/` or marking `archive/` as archival content. Deleting release notes is usually not desired.
- Some PDF/manual files (LUXORliving API docs, Weinzierl BAOS manual) are large binaries; keep if actively referenced.

## Candidate scripts to review
- `scripts/delppy` — check usage (might be a one-off tool).
- `scripts/deploy_release.sh`, `scripts/release_automation.sh` — confirm whether still used in deployment workflow.

## Next actions
1. Review the above list with maintainers and confirm which items can be archived (move to `docs/archive/old/`) or removed.
2. For deletions: open a PR per logical group (e.g., archive-release-notes, remove-unused-scripts) with clear rationale and a 7-day hold before merge.
3. Add a checklist to `RELEASE_OPERATIONS.md` describing archival vs deletion policy.

