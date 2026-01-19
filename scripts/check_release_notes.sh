#!/usr/bin/env bash
set -euo pipefail

# Prefer local virtualenv binaries if present
if [ -d "venv/bin" ]; then
  PATH="venv/bin:$PATH"
elif [ -d ".venv/bin" ]; then
  PATH=".venv/bin:$PATH"
fi

# check_release_notes.sh
# Verify that a RELEASE_NOTES_v<version>.md file exists and contains the version heading

# Formatting guards (prevent releasing unformatted code)
if ! command -v black >/dev/null 2>&1; then
  echo "Missing dependency: black" >&2
  exit 1
fi
if ! command -v isort >/dev/null 2>&1; then
  echo "Missing dependency: isort" >&2
  exit 1
fi

echo "Running black --check ..."
black --check custom_components tests scripts

echo "Running isort --check-only ..."
isort --check-only custom_components tests scripts

MANIFEST="custom_components/luxor_living/manifest.json"
if [ ! -f "$MANIFEST" ]; then
  echo "Manifest not found: $MANIFEST" >&2
  exit 2
fi

VERSION=$(python3 -c "import json,sys;print(json.load(open('$MANIFEST'))['version'])")
# Release notes MUST be in docs/releases/ (standardized location)
RELEASE_FILE="docs/releases/RELEASE_NOTES_v${VERSION}.md"

if [ ! -f "$RELEASE_FILE" ]; then
  echo "Missing release notes file: $RELEASE_FILE" >&2
  echo "Release notes must be placed in docs/releases/RELEASE_NOTES_v<version>.md" >&2
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
