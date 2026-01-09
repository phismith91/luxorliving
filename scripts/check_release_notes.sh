#!/usr/bin/env bash
set -euo pipefail

# check_release_notes.sh
# Verify that a RELEASE_NOTES_v<version>.md file exists and contains the version heading

MANIFEST="custom_components/luxor_living/manifest.json"
if [ ! -f "$MANIFEST" ]; then
  echo "Manifest not found: $MANIFEST" >&2
  exit 2
fi

VERSION=$(python3 -c "import json,sys;print(json.load(open('$MANIFEST'))['version'])")
# Check root first, then docs/releases
RELEASE_FILE_ROOT="RELEASE_NOTES_v${VERSION}.md"
RELEASE_FILE_DOCS="docs/releases/RELEASE_NOTES_v${VERSION}.md"

if [ -f "$RELEASE_FILE_ROOT" ]; then
  RELEASE_FILE="$RELEASE_FILE_ROOT"
elif [ -f "$RELEASE_FILE_DOCS" ]; then
  RELEASE_FILE="$RELEASE_FILE_DOCS"
else
  echo "Missing release notes file: looked for $RELEASE_FILE_ROOT or $RELEASE_FILE_DOCS" >&2
  exit 1
fi

# Check file contains the version heading
if ! grep -q "v${VERSION}" "$RELEASE_FILE"; then
  echo "Release notes file $RELEASE_FILE does not reference version $VERSION" >&2
  exit 1
fi

# Simple non-empty check
if [ ! -s "$RELEASE_FILE" ]; then
  echo "Release notes file $RELEASE_FILE is empty" >&2
  exit 1
fi

echo "OK: Release notes $RELEASE_FILE present and valid for version $VERSION"