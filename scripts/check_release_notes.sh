#!/usr/bin/env bash
set -euo pipefail

# check_release_notes.sh
# Verify that CHANGELOG.md has a release entry for the current manifest version.
# Release notes are extracted from CHANGELOG.md by release.yml — no separate file needed.

MANIFEST="custom_components/luxor_living/manifest.json"
if [ ! -f "$MANIFEST" ]; then
  echo "Manifest not found: $MANIFEST" >&2
  exit 2
fi

VERSION=$(python3 -c "import json,sys;print(json.load(open('$MANIFEST'))['version'])")

if [ ! -f "CHANGELOG.md" ]; then
  echo "CHANGELOG.md not found" >&2
  exit 2
fi

if grep -q "## \[${VERSION}\]" CHANGELOG.md; then
  echo "OK: CHANGELOG.md has release entry for v${VERSION}"
else
  echo "Missing CHANGELOG.md entry: ## [${VERSION}]" >&2
  echo "Add a ## [${VERSION}] - YYYY-MM-DD section to CHANGELOG.md before release." >&2
  exit 1
fi
