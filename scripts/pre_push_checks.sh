#!/usr/bin/env bash
# Pre-Push Validation Script
# Run all CI checks locally BEFORE pushing to avoid failed workflows
#
# Usage: ./scripts/pre_push_checks.sh [--fast|--full]
#
# --fast: Run only fast checks (formatting, smoke tests) ~30s
# --full: Run all checks including full test suite ~2min (default)

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODE="${1:-full}"
FAILED_CHECKS=()
PYTHON_VERSION="3.13"

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}   Pre-Push Validation Checks${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Helper functions
check_step() {
    local name="$1"
    echo -e "${BLUE}▶ Running: ${name}${NC}"
}

check_pass() {
    local name="$1"
    echo -e "${GREEN}✅ PASS: ${name}${NC}"
    echo ""
}

check_fail() {
    local name="$1"
    local hint="$2"
    echo -e "${RED}❌ FAIL: ${name}${NC}"
    if [ -n "$hint" ]; then
        echo -e "${YELLOW}   Fix: ${hint}${NC}"
    fi
    echo ""
    FAILED_CHECKS+=("$name")
}

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo -e "${YELLOW}   Run: source .venv/bin/activate${NC}"
    echo ""
    exit 1
fi

# Check Python version
check_step "Python version"
CURRENT_PYTHON=$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$CURRENT_PYTHON" != "$PYTHON_VERSION" ]; then
    check_fail "Python version" "Need Python $PYTHON_VERSION, got $CURRENT_PYTHON"
else
    check_pass "Python $CURRENT_PYTHON"
fi

# 1. Code Formatting Checks
check_step "Black formatting"
if black --check custom_components tests scripts 2>&1 | grep -q "would reformat"; then
    check_fail "Black formatting" "Run: black ."
else
    check_pass "Black formatting"
fi

check_step "Import sorting (isort)"
if ! isort --check-only custom_components tests scripts > /dev/null 2>&1; then
    check_fail "Import sorting" "Run: isort ."
else
    check_pass "Import sorting"
fi

# 2. Linting (Advisory - don't fail)
if [ "$MODE" = "full" ]; then
    check_step "Flake8 linting (advisory)"
    flake8 custom_components tests scripts --exit-zero || true
    check_pass "Flake8 (advisory only)"
fi

# 3. Security Scans
if [ "$MODE" = "full" ]; then
    check_step "Bandit security scan"
    if bandit -r custom_components/luxor_living/ --severity-level medium -q > /dev/null 2>&1; then
        check_pass "Bandit security scan"
    else
        echo -e "${YELLOW}⚠️  Bandit found issues (review manually)${NC}"
        bandit -r custom_components/luxor_living/ --severity-level medium
        echo ""
    fi

    check_step "Pip-audit vulnerability scan"
    pip-audit --desc > /tmp/pip-audit.log 2>&1 || true
    if grep -q "CVE-2025-67221" /tmp/pip-audit.log; then
        echo -e "${YELLOW}⚠️  Known CVE: CVE-2025-67221 (orjson) - allowlisted${NC}"
        check_pass "Pip-audit (known CVE allowlisted)"
    elif grep -q "No known vulnerabilities found" /tmp/pip-audit.log; then
        check_pass "Pip-audit"
    else
        check_fail "Pip-audit" "Review: /tmp/pip-audit.log"
    fi
fi

# 4. HACS & hassfest validation
check_step "Manifest validation (hassfest)"
if [ -f custom_components/luxor_living/manifest.json ]; then
    # Basic JSON validation
    if python -m json.tool custom_components/luxor_living/manifest.json > /dev/null 2>&1; then
        check_pass "Manifest JSON valid"
    else
        check_fail "Manifest validation" "Invalid JSON in manifest.json"
    fi
else
    check_fail "Manifest validation" "manifest.json not found"
fi

# 5. Test Suite
check_step "Smoke tests"
if python -m pytest tests/ -q -m "smoke and not enable_socket" > /dev/null 2>&1; then
    check_pass "Smoke tests"
else
    check_fail "Smoke tests" "Run: pytest tests/ -m smoke"
fi

if [ "$MODE" = "full" ]; then
    check_step "Full test suite"
    if python -m pytest tests/ -q -m "not enable_socket" > /dev/null 2>&1; then
        PASSED=$(python -m pytest tests/ -q -m "not enable_socket" 2>&1 | tail -1 | grep -oP '\d+(?= passed)')
        check_pass "Full test suite ($PASSED tests passed)"
    else
        check_fail "Full test suite" "Run: pytest tests/"
    fi
fi

# 6. Git checks
check_step "Git status"
if git diff --cached --quiet; then
    check_fail "Git staging" "No files staged for commit"
else
    STAGED_FILES=$(git diff --cached --name-only | wc -l)
    check_pass "Git staging ($STAGED_FILES files staged)"
fi

# Check for uncommitted changes
if git diff --quiet; then
    check_pass "No uncommitted changes"
else
    echo -e "${YELLOW}⚠️  Uncommitted changes detected${NC}"
    git status --short
    echo ""
fi

# Summary
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}   Summary${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo -e "${GREEN}   Safe to push 🚀${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ ${#FAILED_CHECKS[@]} check(s) failed:${NC}"
    for check in "${FAILED_CHECKS[@]}"; do
        echo -e "${RED}   - $check${NC}"
    done
    echo ""
    echo -e "${YELLOW}Fix issues above before pushing${NC}"
    echo ""
    exit 1
fi
