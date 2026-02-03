# Archive Directory

This directory contains historical documentation and release notes that are no longer actively maintained but are kept for reference purposes.

## Structure

- `releases/` - Archived release notes for older versions

## Archival Policy

### When to Archive

Documents and release notes should be moved to this archive when:

1. **Release Notes:**
   - A newer stable version has been released (archive the previous stable version)
   - Beta/pre-release versions are superseded by stable releases
   - Generally, keep only the latest stable release in `docs/releases/`

2. **Documentation:**
   - Content is outdated but has historical value
   - Document is superseded by newer documentation
   - Content is no longer relevant to current implementation but may be useful for understanding past decisions

### What NOT to Archive

- Do NOT archive:
  - The latest stable release notes
  - Active beta/pre-release notes (until superseded by stable)
  - Documentation that is still referenced or relevant

### Deletion vs Archival

- **Archive (don't delete):** Release notes, architectural decisions, audit reports, incident postmortems
- **Can delete after review:** Temporary notes, duplicate files, clearly obsolete content with no historical value

## Contents

### Releases (`releases/`)

Archived release notes for historical reference:

- `RELEASE_NOTES_v0.5.4.3.md` - Patch release (archived 2026-02-03)
- `RELEASE_NOTES_v0.6.0.md` - Superseded by v0.6.1 (archived 2026-02-03)
- `RELEASE_NOTES_v0.6.0-beta.1.md` - Beta version (archived 2026-02-03)

## Maintenance

This archive is maintained as part of the regular release process. See `docs/RELEASE_OPERATIONS.md` for details on the archival workflow.
