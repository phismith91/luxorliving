#!/bin/bash
# README.md Quality Gate Validation Script
# Usage: ./scripts/validate_readme.sh
# Exit code: 0 = pass, 1 = fail

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔍 README.md Quality Gate Validation"
echo "====================================="
echo ""

ERRORS=0

# 1. Check manifest.json version
echo "1️⃣  Checking version consistency..."
MANIFEST_VERSION=$(grep '"version"' custom_components/luxor_living/manifest.json | head -1 | sed 's/.*"version": "\(.*\)".*/\1/')
echo "   Manifest version: v$MANIFEST_VERSION"

# Check if version appears in README
if grep -q "v$MANIFEST_VERSION" README.md; then
    echo "   ✅ Version v$MANIFEST_VERSION found in README.md"
else
    echo "   ❌ Version v$MANIFEST_VERSION NOT found in README.md"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 2. Check test count accuracy
echo "2️⃣  Checking test count accuracy..."
if [ -d "venv" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate 2>/dev/null || true
fi

TEST_COUNT=$(python -m pytest tests/ --collect-only -q 2>&1 | grep "tests collected" | awk '{print $1}')
echo "   Actual tests: $TEST_COUNT"

if grep -q "$TEST_COUNT tests" README.md; then
    echo "   ✅ Test count $TEST_COUNT found in README.md"
else
    echo "   ⚠️  Test count $TEST_COUNT NOT mentioned in README.md"
    echo "      (Search for older count and update)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. Validate documentation links
echo "3️⃣  Validating documentation links..."
LINK_ERRORS=0

# Extract all markdown links from README.md
LINKS=$(grep -o '\[.*\](.*.md)' README.md | sed 's/.*(\(.*\))/\1/' | sort -u)

for LINK in $LINKS; do
    # Skip external URLs
    if [[ "$LINK" =~ ^http ]]; then
        continue
    fi
    
    if [ -f "$LINK" ]; then
        echo "   ✅ $LINK"
    else
        echo "   ❌ MISSING: $LINK"
        LINK_ERRORS=$((LINK_ERRORS + 1))
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $LINK_ERRORS -eq 0 ]; then
    echo "   ✅ All documentation links valid"
fi
echo ""

# 4. Check for outdated patterns
echo "4️⃣  Checking for outdated patterns..."
OUTDATED_PATTERNS=(
    "v0.3.0"
    "v0.3.1"
    "v0.3.2"
    "v0.3.3"
    "v0.4.0"
    "v0.5.0"
    "v0.5.1"
    "58 tests"
    "74 tests"
    "85 tests"
    "86 tests"
)

for PATTERN in "${OUTDATED_PATTERNS[@]}"; do
    # Skip current version
    if [ "$PATTERN" == "v$MANIFEST_VERSION" ]; then
        continue
    fi
    
    if grep -q "$PATTERN" README.md 2>/dev/null; then
        echo "   ⚠️  Found potentially outdated: $PATTERN"
        # Not counting as error, just warning
    fi
done
echo ""

# 5. CHANGELOG.md Consistency Check
echo "5️⃣  Checking CHANGELOG.md consistency..."

if [ ! -f "CHANGELOG.md" ]; then
    echo "   ❌ CHANGELOG.md not found!"
    ERRORS=$((ERRORS + 1))
else
    # Check if current version has a release entry
    if grep -q "## \[$MANIFEST_VERSION\]" CHANGELOG.md; then
        echo "   ✅ Version $MANIFEST_VERSION found in CHANGELOG.md"
    else
        echo "   ❌ Version $MANIFEST_VERSION NOT found in CHANGELOG.md"
        echo "      (Expected: ## [$MANIFEST_VERSION] - YYYY-MM-DD)"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check for [Unreleased] section with version number (common mistake)
    if grep -q "## \[Unreleased\] - v[0-9]" CHANGELOG.md; then
        echo "   ❌ Found versioned [Unreleased] section (should be released!)"
        ERRORS=$((ERRORS + 1))
    else
        echo "   ✅ No versioned [Unreleased] sections"
    fi
    
    # Check if there's an [Unreleased] section at all
    if grep -q "## \[Unreleased\]" CHANGELOG.md; then
        echo "   ✅ [Unreleased] section exists"
    else
        echo "   ⚠️  No [Unreleased] section (recommended for ongoing work)"
    fi
fi

echo "6️⃣  Checking README release section..."
# Check for release markers and that content matches manifest version
if grep -q "<!-- RELEASE_NOTES_START -->" README.md; then
    if ! grep -q "<!-- RELEASE_NOTES_END -->" README.md; then
        echo "   ❌ README release markers incomplete"
        ERRORS=$((ERRORS + 1))
    else
        SECTION=$(awk '/<!-- RELEASE_NOTES_START -->/{flag=1;next}/<!-- RELEASE_NOTES_END -->/{flag=0}flag' README.md)
        if echo "$SECTION" | grep -q "v$MANIFEST_VERSION"; then
            echo "   ✅ README current release matches v$MANIFEST_VERSION"
        else
            echo "   ❌ README current release does not contain v$MANIFEST_VERSION"
            ERRORS=$((ERRORS + 1))
        fi
    fi
else
    echo "   ⚠️  No release markers found in README.md (recommended to add)"
fi

# Ensure no historical release sections remain in README
if grep -q "## 🚀 v" README.md; then
    echo "   ⚠️  Found '## 🚀 v' headers in README.md; move full history to CHANGELOG.md"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No legacy release headers found in README.md"
fi

echo ""

# 6. Summary
echo "====================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ README.md Quality Gate: PASSED"
    exit 0
else
    echo "❌ README.md Quality Gate: FAILED ($ERRORS errors)"
    echo ""
    echo "Fix these issues before release!"
    exit 1
fi
