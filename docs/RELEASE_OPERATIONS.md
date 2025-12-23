# 📋 Release & Tagging Operational Guide

**Author:** Release Manager Agent  
**Date:** 23. Dezember 2025  
**Purpose:** Step-by-step instructions for v0.3.0 release and future tagging

---

## Phase 0: Pre-Release Verification (Durchführen vor jedem Release)

### Step 0.1: Test Suite Verification

```bash
# ✅ Alle Tests müssen passing sein
cd /home/phil/gitlab_github/luxorliving
python -m pytest tests/ -q --tb=short
# EXPECTED: 74 passed in ~3s
```

**Aktueller Status:** ✅ 74/74 passing (100%)

### Step 0.2: Code Quality Checks

```bash
# ✅ Black formatting check
black --check custom_components/luxor_living tests
# EXPECTED: All done (no changes)

# ✅ isort check
isort --check-only custom_components/luxor_living tests
# EXPECTED: All done (no changes)

# ✅ flake8 linting (optional)
flake8 custom_components/luxor_living
# EXPECTED: 0 errors (unless acceptable warnings)

# ✅ Type checking
mypy custom_components/luxor_living --ignore-missing-imports
# EXPECTED: Success

# ✅ Security scanning
bandit -r custom_components/luxor_living -q
# EXPECTED: No issues or only info-level findings
```

### Step 0.3: Coverage Verification

```bash
# ✅ Test coverage report
python -m pytest tests/ --cov=custom_components/luxor_living --cov-report=term-missing
# EXPECTED: Coverage >= 55% (or higher if improved)

# Or from pre-configured:
python -m pytest tests/ --cov
# Uses pyproject.toml settings
```

### Step 0.4: Documentation Review

```bash
# ✅ Check that docs are up-to-date
- [ ] CHANGELOG.md: Has entry for unreleased version
- [ ] manifest.json: Version field correct
- [ ] README.md: No outdated version references
- [ ] docs/QUICKSTART.md: Current and accurate
```

### Step 0.5: Git Status Check

```bash
# ✅ Working directory must be clean
git status
# EXPECTED: nothing to commit, working tree clean

# ✅ Check current branch
git branch
# EXPECTED: * feature/core-integration (or release branch)

# ✅ Check recent commits
git log --oneline -5
# EXPECTED: Clean, descriptive commit messages
```

---

## Phase 1: Release Preparation for v0.3.0

### Step 1.1: Merge to main branch (if not already)

```bash
# Option A: If releasing from feature branch
git checkout main
git pull origin main
git merge feature/core-integration
git push origin main

# Option B: If already on main
git checkout main
git pull origin main
# Continue with next steps
```

### Step 1.2: Update manifest.json

**File:** `/custom_components/luxor_living/manifest.json`

```bash
# Find current version
grep '"version"' custom_components/luxor_living/manifest.json
# Output: "version": "0.3.0-beta.1"

# Update version
# OLD: "version": "0.3.0-beta.1",
# NEW: "version": "0.3.0",
```

**Action:** Use editor or sed command:
```bash
sed -i 's/"version": "0.3.0-beta.1"/"version": "0.3.0"/' \
  custom_components/luxor_living/manifest.json

# Verify
grep '"version"' custom_components/luxor_living/manifest.json
# Output: "version": "0.3.0"
```

### Step 1.3: Update CHANGELOG.md

**File:** `/CHANGELOG.md`

**Current State:**
```markdown
## [Unreleased]

### Added
- DataUpdateCoordinator pattern
- ...

### Changed
- ...

## [0.2.12] - 2025-12-23
```

**Target State:**
```markdown
## [0.3.0] - 2025-12-23

### Added
- DataUpdateCoordinator pattern
- ...

### Changed
- ...

## [0.2.12] - 2025-12-22
```

**Action:** Replace `[Unreleased]` with `[0.3.0] - 2025-12-23`

**Bash Command:**
```bash
# Create backup
cp CHANGELOG.md CHANGELOG.md.bak

# Update header (using sed)
sed -i 's/## \[Unreleased\]/## [0.3.0] - 2025-12-23/' CHANGELOG.md

# Verify
head -15 CHANGELOG.md
```

### Step 1.4: Commit Version Bump

```bash
# Stage changes
git add custom_components/luxor_living/manifest.json CHANGELOG.md

# Verify staged changes
git diff --cached
# Should show manifest version change and CHANGELOG date

# Commit with semantic commit message
git commit -m "release(v0.3.0): bump version and update changelog"

# Verify
git log --oneline -1
# Output: release(v0.3.0): bump version and update changelog
```

---

## Phase 2: Git Tagging for v0.3.0

### Step 2.1: Create Annotated Release Tag

```bash
# ✅ Create signed or unsigned tag (choose one)

# Option A: Unsigned (standard for beta/RC releases)
git tag -a v0.3.0 \
  -m "LUXORliving v0.3.0: HACS Stable Release

Release Date: 23. Dezember 2025
Target: HACS (community integration)

## Features
- DataUpdateCoordinator pattern
- Full device registry integration
- Complete type hints on all platforms
- Black code formatting
- Comprehensive test coverage (55%)

## Fixes
- Device registry integration missing
- Inconsistent entity implementations

## Known Issues
- Test coverage at 55% (improving in 0.3.x patches)
- Climate/Cover/Sensor platforms in development

For full changelog, see CHANGELOG.md"

# Option B: Signed tag (for production releases)
git tag -a -s v0.3.0 \
  -m "LUXORliving v0.3.0: HACS Stable Release" \
  --local-user YOUR_GPG_KEY
```

### Step 2.2: Verify Tag Creation

```bash
# ✅ List tags
git tag -l | grep v0.3

# ✅ Show tag details
git show v0.3.0
# Should display tag info + commit details

# ✅ Verify tag points to correct commit
git rev-list -n 1 v0.3.0
# Should match current HEAD
```

### Step 2.3: Push Tag to Remote

```bash
# ✅ Push the specific tag
git push origin v0.3.0

# ✅ Verify on remote
git ls-remote --tags origin | grep v0.3.0
# Should show: refs/tags/v0.3.0 [commit_hash]
```

---

## Phase 3: Tag Cleanup (Legacy Tags)

### Step 3.1: Identify Tags to Remove

```bash
# List all old/inconsistent tags
git tag -l | grep -E "beta|beta\.7|beta\.202512"

# Output:
# v0.2.1-beta.4
# v0.2.1-beta.7.2
# v0.2.10-beta.7.7.3
# v0.2.12-beta.202512231247
```

### Step 3.2: Delete Old Tags Locally

```bash
# Delete one at a time (safer)
git tag -d v0.2.1-beta.4
git tag -d v0.2.1-beta.7.2
git tag -d v0.2.10-beta.7.7.3
git tag -d v0.2.12-beta.202512231247

# Or in one command
git tag -d v0.2.1-beta.4 v0.2.1-beta.7.2 v0.2.10-beta.7.7.3 \
  v0.2.12-beta.202512231247

# Verify deletion
git tag -l | grep -E "beta|202512"
# Should return empty
```

### Step 3.3: Delete Old Tags from Remote

```bash
# Push deletions to remote (one per line for clarity)
git push origin --delete v0.2.1-beta.4
git push origin --delete v0.2.1-beta.7.2
git push origin --delete v0.2.10-beta.7.7.3
git push origin --delete v0.2.12-beta.202512231247

# Or all at once:
git push origin --delete v0.2.1-beta.4 v0.2.1-beta.7.2 \
  v0.2.10-beta.7.7.3 v0.2.12-beta.202512231247

# Verify on remote
git ls-remote --tags origin | grep -E "v0.2.1-beta|v0.2.10-beta"
# Should return empty
```

### Step 3.4: Verify Cleanup

```bash
# ✅ Local tags
git tag -l
# Should NOT include old beta tags

# ✅ Remote tags
git ls-remote --tags origin | grep -v "^"
# Or use GitHub API

# ✅ Check "Releases" section on GitHub web interface
# Old pre-releases should no longer be listed
```

---

## Phase 4: GitHub Release Creation

### Step 4.1: Create Release via Web UI

**URL:** https://github.com/phismith91/luxorliving/releases

**Steps:**
1. Click "Releases" → "Create a new release"
2. Choose tag: `v0.3.0`
3. Release title: `LUXORliving v0.3.0 - HACS Stable Release`
4. Release notes (from CHANGELOG.md):

```markdown
# 🎉 LUXORliving v0.3.0

**Release Date:** 23. Dezember 2025

## Highlights

- ✅ DataUpdateCoordinator pattern for centralized state management
- ✅ Full device registry integration for all platforms
- ✅ Complete type hints (100%) on Light, Switch, Binary Sensor
- ✅ Black code formatting (100% compliant)
- ✅ Comprehensive test suite (74 tests, 55% coverage baseline)
- ✅ py.typed marker for editor type checking support

## 📋 What's New

### Added
- DataUpdateCoordinator pattern (centralized polling)
- LuxorLivingEntity base class with common functionality
- Device registry integration (`device_info` property)
- Type hints on all function parameters and returns
- Code style tools: Black formatter, isort, flake8, mypy, bandit
- py.typed marker for PEP 561 type checking
- Comprehensive test coverage reporting

### Changed
- Light platform refactored to use DataUpdateCoordinator
- Switch platform refactored to use DataUpdateCoordinator
- Binary Sensor platform refactored with auto-detection
- All platforms now extend LuxorLivingEntity base class
- Improved docstrings on all methods
- Import organization with isort

### Fixed
- Device registry integration missing in entities
- Inconsistent entity implementations across platforms
- Type hint coverage gaps

## 🔧 Installation

### Via HACS
1. Open HACS → Integrations
2. Click "+ EXPLORE & DOWNLOAD REPOSITORIES"
3. Search for "LUXORliving"
4. Click "Download"
5. Restart Home Assistant
6. Go to Settings → Devices & Services → Create Integration
7. Search for "LUXORliving" and complete setup

### Manual Installation
1. Download the latest release
2. Extract to `~/.homeassistant/custom_components/luxor_living/`
3. Restart Home Assistant
4. Complete setup via web UI

## 📊 Quality Metrics

- **Tests:** 74/74 passing (100% success rate)
- **Coverage:** 55% baseline (improving in 0.3.x)
- **Type Hints:** 100% on critical modules
- **Code Style:** Black compliant
- **Documentation:** Complete and up-to-date

## ⚠️ Known Issues

- Test coverage: 55% (ongoing improvement)
- Climate, Cover, Sensor platforms in beta (limited features)
- See [Issues](https://github.com/phismith91/luxorliving/issues) for current tracking

## 🙏 Credits

Thanks to all contributors and testers!

## 🔗 Links

- [GitHub Repository](https://github.com/phismith91/luxorliving)
- [CHANGELOG](./CHANGELOG.md)
- [Documentation](./docs/)
- [Quick Start Guide](./docs/QUICKSTART.md)

---

**Changelog:** See [CHANGELOG.md](./CHANGELOG.md) for full history
```

5. ☑️ Check "Set as the latest release"
6. Click "Publish release"

### Step 4.2: Verify Release on GitHub

```bash
# Check via GitHub CLI (if installed)
gh release view v0.3.0

# Or manually verify on:
# https://github.com/phismith91/luxorliving/releases/tag/v0.3.0
```

---

## Phase 5: HACS Submission (Optional/Conditional)

### Step 5.1: Check HACS Auto-Discovery

HACS may automatically discover the new release. Check:
- [HACS Discord Community](https://discord.gg/hacs)
- [HACS GitHub Discussions](https://github.com/hacs/integration/discussions)

### Step 5.2: Manual HACS PR (if needed)

If auto-discovery doesn't work:

```bash
# Clone HACS repository
git clone https://github.com/hacs/default.git hacs-default

# Create feature branch
cd hacs-default
git checkout -b add-luxorliving

# Edit repositories.json
# Add entry:
{
  "domain": "luxor_living",
  "name": "LUXORliving",
  "documentation": "https://github.com/phismith91/luxorliving",
  "download_url": "https://github.com/phismith91/luxorliving/releases/download/v0.3.0/luxor_living-v0.3.0.zip",
  "documentation_url": "https://github.com/phismith91/luxorliving",
  "issues_url": "https://github.com/phismith91/luxorliving/issues",
  "requirements": []
}

# Commit & push
git add repositories.json
git commit -m "Add LUXORliving integration"
git push origin add-luxorliving

# Create PR on GitHub
# https://github.com/hacs/default
```

---

## Phase 6: Post-Release Tasks

### Step 6.1: Update Documentation

```bash
# ✅ Check README.md for version references
grep -n "0\." README.md | head -10

# ✅ Update any version-specific docs
ls docs/*.md

# ✅ Verify QUICKSTART.md is current
```

### Step 6.2: Announce Release

**Channels:**
- [ ] GitHub Releases page (done in Phase 4)
- [ ] Repository README badge (if applicable)
- [ ] [Home Assistant Community Forum](https://community.home-assistant.io)
- [ ] [Home Assistant Discord](https://discord.gg/home-assistant)
- [ ] [HACS Discord](https://discord.gg/hacs)

**Template Message:**
```
📢 LUXORliving v0.3.0 Released!

🎉 LUXORliving v0.3.0 is now available for HACS!

Key Features:
- DataUpdateCoordinator pattern for reliable state management
- Full device registry integration
- Complete type hints (100% on critical platforms)
- 74 comprehensive tests (55% coverage baseline)
- Black-formatted, production-ready code

Installation:
1. Add to HACS Integrations
2. Restart Home Assistant
3. Setup via UI: Settings → Devices & Services

GitHub: https://github.com/phismith91/luxorliving
Releases: https://github.com/phismith91/luxorliving/releases

Questions? Start a discussion: https://github.com/phismith91/luxorliving/discussions
```

### Step 6.3: Create Release Candidate Branch

```bash
# Create backup branch for this release
git checkout -b release/0.3.0
git push origin release/0.3.0

# This allows hotfixes on 0.3.0 if needed (v0.3.1, v0.3.2, etc.)
```

### Step 6.4: Begin Next Development Cycle

```bash
# Update version for next dev cycle
# manifest.json: "version": "0.4.0-beta.1"
sed -i 's/"version": "0.3.0"/"version": "0.4.0-beta.1"/' \
  custom_components/luxor_living/manifest.json

# Update CHANGELOG
# Add new [Unreleased] section:
```

```markdown
## [Unreleased]

### Added
- (features in development)

### Changed
- (ongoing improvements)

### Fixed
- (bug fixes)

## [0.3.0] - 2025-12-23
```

```bash
# Commit
git add manifest.json CHANGELOG.md
git commit -m "chore: prepare v0.4.0-beta.1 development cycle"
git push origin main  # or feature/core-integration
```

---

## Tagging Best Practices

### Best Practice 1: Tagging Consistency

```
✅ GOOD:
  v0.3.0           (release)
  v0.3.0-rc.1      (release candidate)
  v0.3.0-beta.1    (beta)
  v0.3.1           (patch)

❌ BAD:
  0.3.0            (missing 'v' prefix)
  v0.3.0.0         (extra level)
  v0.3.0-beta.1.4  (too many pre-release parts)
  v-0.3.0          (incorrect prefix)
  v0.3_beta.1      (underscore instead of dash)
  v0.3-20251223    (timestamp instead of version)
```

### Best Practice 2: Tag Types

```bash
# ✅ USE: Annotated Tags (recommended for releases)
git tag -a v0.3.0 -m "Release message"
git tag -a -s v1.0.0 -m "Production release"  # Signed

# ❌ AVOID: Lightweight Tags
git tag v0.3.0  # No -a flag
```

### Best Practice 3: Tag Deletion

```bash
# ✅ IF MISTAKE: Delete and recreate
git tag -d v0.3.0
git push origin --delete v0.3.0
git tag -a v0.3.0 -m "..."
git push origin v0.3.0

# ❌ NEVER: Force-push tags
git push origin --force v0.3.0  # Can break clone operations
```

### Best Practice 4: Release Documentation

```bash
# ✅ ALWAYS: Update CHANGELOG before tagging
# ✅ ALWAYS: Create GitHub Release with detailed notes
# ✅ ALWAYS: Test installation from release assets
# ✅ ALWAYS: Announce on community channels

# ❌ NEVER: Tag without updating version files
# ❌ NEVER: Create GitHub Release before tagging
# ❌ NEVER: Forget to push tags to remote
```

---

## Emergency Procedures

### Emergency 1: Hotfix After Release

```bash
# Scenario: Critical bug found in v0.3.0

# Step 1: Create hotfix branch from release tag
git checkout -b hotfix/0.3.1 v0.3.0

# Step 2: Apply fix
# (edit files to fix critical bug)
git add .
git commit -m "fix: critical bug description"

# Step 3: Update version & CHANGELOG
# manifest.json: 0.3.0 → 0.3.1
# CHANGELOG.md: Add [0.3.1] section

# Step 4: Tag and release
git tag -a v0.3.1 -m "LUXORliving v0.3.1: Hotfix for [issue]"
git push origin hotfix/0.3.1 v0.3.1

# Step 5: Create GitHub Release (same as Phase 4)

# Step 6: Merge hotfix back to main
git checkout main
git merge hotfix/0.3.1
git push origin main
```

### Emergency 2: Rollback Failed Release

```bash
# Scenario: v0.3.0 has critical issues, need to rollback

# Step 1: Delete tags locally and remotely
git tag -d v0.3.0
git push origin --delete v0.3.0

# Step 2: Revert version changes
git revert HEAD  # Revert the release commit

# Step 3: Fix issues
# (make necessary changes)

# Step 4: Create new release attempt
git tag -a v0.3.0-rc.1 -m "..."  # Or use different version
git push origin v0.3.0-rc.1

# Step 5: Announce issue on community channels
```

---

## Command Quick Reference

### Tag Management

```bash
# List all tags
git tag -l

# List tags with pattern
git tag -l "v0.3*"

# Show tag details
git show v0.3.0

# Create annotated tag
git tag -a v0.3.0 -m "Message"

# Create signed tag
git tag -a -s v0.3.0 -m "Message"

# Delete local tag
git tag -d v0.3.0

# Delete remote tag
git push origin --delete v0.3.0

# Push specific tag
git push origin v0.3.0

# Push all tags
git push origin --tags

# Verify tag
git verify-tag v0.3.0
```

### Version Updates

```bash
# Update manifest version
sed -i 's/"version": "0.3.0-beta.1"/"version": "0.3.0"/' \
  custom_components/luxor_living/manifest.json

# Verify version
grep '"version"' custom_components/luxor_living/manifest.json

# Update CHANGELOG date
date +"%Y-%m-%d"  # Get today's date
```

### Pre-Release Checks

```bash
# Run all tests
python -m pytest tests/ -q --tb=short

# Check formatting
black --check custom_components/luxor_living tests

# Check imports
isort --check-only custom_components/luxor_living tests

# Type checking
mypy custom_components/luxor_living

# Coverage
python -m pytest tests/ --cov=custom_components/luxor_living
```

---

**Version:** 1.0  
**Last Updated:** 23. Dezember 2025  
**Next Review:** After v0.3.0 release
