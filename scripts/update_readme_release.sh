#!/usr/bin/env bash
# Update README.md "Current Release" section from RELEASE_NOTES_v<version>.md
# Usage: ./scripts/update_readme_release.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

MANIFEST_VERSION=$(grep '"version"' custom_components/luxor_living/manifest.json | head -1 | sed 's/.*"version": "\(.*\)".*/\1/')
# Prefer release notes in repo root; fallback to docs/releases
RELEASE_FILE="RELEASE_NOTES_v${MANIFEST_VERSION}.md"
if [ -f "$RELEASE_FILE" ]; then
    echo "Using $RELEASE_FILE (root)"
else
    RELEASE_FILE="docs/releases/RELEASE_NOTES_v${MANIFEST_VERSION}.md"
    if [ -f "$RELEASE_FILE" ]; then
        echo "Using $RELEASE_FILE (docs/releases)"
    else
        echo "Release notes file not found in root or docs/releases (expected RELEASE_NOTES_v${MANIFEST_VERSION}.md)" >&2
        # Try to find any candidate in docs/releases
        CANDIDATE=$(find docs/releases -maxdepth 1 -type f -name "RELEASE_NOTES_v${MANIFEST_VERSION}*" | head -n 1 || true)
        if [ -n "$CANDIDATE" ]; then
            RELEASE_FILE="$CANDIDATE"
            echo "Using candidate $RELEASE_FILE"
        else
            echo "No matching release notes found for v$MANIFEST_VERSION. Aborting." >&2
            exit 1
        fi
    fi
fi

# Read release notes content (keep headings so version is present)
RELEASE_CONTENT=$(sed -e 's/^/\n/' "$RELEASE_FILE" )

# Build the replacement block
REPLACEMENT="## Current Release\n\n<!-- RELEASE_NOTES_START -->\n\n${RELEASE_CONTENT}\n<!-- RELEASE_NOTES_END -->\n\nFor full release history see [CHANGELOG.md](./CHANGELOG.md).\n"

# Replace the current release block in README.md
# We look for the block between the first '## 🚀 v' and the '## Quick Start' header OR existing markers
README=README.md
TMP=$(mktemp)

if grep -q "<!-- RELEASE_NOTES_START -->" "$README"; then
    # Marker-based replacement
    awk -v repl="$REPLACEMENT" '
        BEGIN{p=1}
        /<!-- RELEASE_NOTES_START -->/{print repl; p=0; inside=1; next}
        /<!-- RELEASE_NOTES_END -->/{inside=0; p=1; next}
        {if(p && !inside) print}
    ' "$README" > "$TMP"
else
    # Fallback: replace from first '## 🚀 v' until the '## Quick Start' header
    awk -v repl="$REPLACEMENT" '
        BEGIN{skip=0}
        /## 🚀 v/ && !skip{print repl; skip=1; next}
        /## Quick Start/ && skip{print; skip=0; next}
        {if(!skip) print}
    ' "$README" > "$TMP"
fi

mv "$TMP" "$README"

echo "README.md updated with release notes from $RELEASE_FILE"

git add "$README"
git commit -m "chore(release): update README current release v$MANIFEST_VERSION" || true

echo "Done."