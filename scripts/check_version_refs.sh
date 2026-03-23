#!/bin/bash
# Version Reference Consistency Check
# Scans docs and key files for stale version numbers that don't match manifest.json.
# Exit code: 0 = pass, 1 = fail

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

ERRORS=0
WARNINGS=0

# Read current version from manifest
MANIFEST_VERSION=$(python3 -c "import json; print(json.load(open('custom_components/luxor_living/manifest.json'))['version'])")
MAJOR_MINOR=$(echo "$MANIFEST_VERSION" | cut -d. -f1-2)  # e.g. 1.1

echo "Version Reference Consistency Check"
echo "===================================="
echo "Manifest version: $MANIFEST_VERSION"
echo ""

# ── 1. SECURITY.md ────────────────────────────────────────────────────────────
echo "1. Checking SECURITY.md..."

# Detect any concrete old version numbers (0.x.y pattern) in the supported table
if grep -qE "^\| 0\.[0-9]" SECURITY.md; then
    echo "   ERROR: SECURITY.md still references old 0.x versions in supported table"
    ERRORS=$((ERRORS + 1))
else
    echo "   OK"
fi

# ── 2. README.md current release ──────────────────────────────────────────────
echo "2. Checking README.md current release link..."

if grep -q "releases/tag/v$MANIFEST_VERSION" README.md; then
    echo "   OK"
else
    FOUND=$(grep -oE "releases/tag/v[0-9]+\.[0-9]+\.[0-9]+" README.md | head -1 || echo "none")
    echo "   ERROR: README.md current release link is '$FOUND', expected 'releases/tag/v$MANIFEST_VERSION'"
    ERRORS=$((ERRORS + 1))
fi

# ── 3. CHANGELOG.md has entry for current version ─────────────────────────────
echo "3. Checking CHANGELOG.md..."

if grep -q "\[$MANIFEST_VERSION\]" CHANGELOG.md; then
    echo "   OK"
else
    echo "   ERROR: CHANGELOG.md has no entry for [$MANIFEST_VERSION]"
    ERRORS=$((ERRORS + 1))
fi

# ── 4. SECURITY.md does not reference a specific old minor version ─────────────
echo "4. Checking SECURITY.md for stale minor version in header..."

# Warn if the "latest (X.Y.x)" line doesn't match current major.minor
if grep -qE "latest \([0-9]+\.[0-9]+\.x\)" SECURITY.md; then
    SECURITY_MINOR=$(grep -oE "latest \([0-9]+\.[0-9]+\.x\)" SECURITY.md | grep -oE "[0-9]+\.[0-9]+" | head -1)
    if [ "$SECURITY_MINOR" != "$MAJOR_MINOR" ]; then
        echo "   WARNING: SECURITY.md shows 'latest ($SECURITY_MINOR.x)' but manifest is $MANIFEST_VERSION"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "   OK"
    fi
else
    echo "   OK (no pinned minor version found)"
fi

# ── 5. docs/ — scan for obvious stale version patterns ────────────────────────
echo "5. Scanning docs/ for stale 'Planned for v0.x' or 'Future v0.x' strings..."

STALE=$(grep -rn --include="*.md" \
    -E "(Planned for v0\.[0-9]|Future.*v0\.[0-9]|v0\.[0-9]+\+ *$)" \
    docs/ 2>/dev/null | grep -v "archive/" || true)

if [ -n "$STALE" ]; then
    echo "   ERROR: Found stale roadmap version references:"
    echo "$STALE" | sed 's/^/     /'
    ERRORS=$((ERRORS + 1))
else
    echo "   OK"
fi

# ── 6. Release notes file exists for current version ──────────────────────────
echo "6. Checking docs/releases/RELEASE_NOTES_v$MANIFEST_VERSION.md..."

if [ -f "docs/releases/RELEASE_NOTES_v$MANIFEST_VERSION.md" ]; then
    echo "   OK"
else
    echo "   ERROR: docs/releases/RELEASE_NOTES_v$MANIFEST_VERSION.md missing"
    ERRORS=$((ERRORS + 1))
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "===================================="
if [ "$ERRORS" -gt 0 ]; then
    echo "FAILED: $ERRORS error(s), $WARNINGS warning(s)"
    echo ""
    echo "Fix these before releasing:"
    echo "  - Run scripts/bump_version.sh <new_version> to update all references at once"
    exit 1
else
    echo "PASSED: All version references consistent ($WARNINGS warning(s))"
fi
