# LUXORliving v1.1.2 — Security Policy & CI Hardening

## Highlights

Corrects the security policy and adds automated version-reference
validation to CI so outdated docs are caught before every release.

## Fixed

- **SECURITY.md**: replaced stale `0.4.x / 0.5.x` supported-versions
  table with "latest only" policy; contact email updated to
  software@withphil.de
- **CI**: new `scripts/check_version_refs.sh` runs on every PR —
  validates SECURITY.md, README release link, CHANGELOG entry, stale
  roadmap strings in docs/, and release notes file against
  `manifest.json`

## Upgrade Notes

- No breaking changes — drop-in replacement for v1.1.1
