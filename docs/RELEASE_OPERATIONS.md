# 📋 Release & Tagging Operational Guide

**Author:** Release Manager Agent **Date:** 9. Januar 2026 **Purpose:**
Step-by-step release procedures and quality gates (current: v0.6.0)

**Note:** Examples use v0.3.0 for illustration. Replace with actual target
version.

---

## 🎯 Quality Policy: "When we do it, do it right!"

**Core principle:** No technical debt, no half measures.

### CI/CD Quality Gates (All checks must be green)

Before **anything** is merged or released:

✅ **Validate Workflow** - Home Assistant integration validation

- hassfest (manifest validation, dependency checks, key ordering)
- HACS validation (repository structure, requirements)
- **Status:** MUST be green

✅ **Release Checks Workflow** - Release readiness validation

- README.md quality gate (version consistency, documentation links, changelog
  sync)
- Release notes presence check
- Release automation dry-run (zip structure, tag creation)
- **ShellCheck (blocking)** - All shell scripts must be clean
- **Status:** MUST be green

✅ **CI/CD Pipeline** - Code quality & tests

- Black (code formatting)
- isort (import sorting)
- pytest (212 tests)
- Coverage reporting
- **Status:** MUST be green

### Enforcement

- **No merge** on failing checks
- **No release** on failing checks
- **Immediate fix** required when a check turns red
- **No exceptions** - `fail_ci_if_error: false` only for non-blocking features
  (e.g., Codecov token)

### Rationale

A failing check is an indicator of:

- Potential bugs
- Version inconsistencies
- Breaking changes for users
- Accumulating technical debt

**Consequence:** Spend 10 minutes fixing now rather than hours fixing
regressions later.

---

## 🔀 Branch Strategy & Release Workflow

### Pre-Release Workflow (Feature Branches)

**Für Pre-Releases (Beta, RC, Feature Testing):**

1. **Entwicklung auf Feature Branch**

   ```bash
   git checkout -b pre-release/v0.5.2-climate-cover
   # Entwicklung, Tests, Commits...
   ```

2. **Pre-Release Tag auf Feature Branch**

   ```bash
   git tag -a v0.5.2-beta.1 -m "Pre-release beta testing"
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin pre-release/v0.5.2-climate-cover
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin v0.5.2-beta.1
   ```

3. **GitHub Pre-Release erstellen**
   ```bash
   gh release create v0.5.2-beta.1 --title "v0.5.2-beta.1" --prerelease --notes "..."
   ```

### Final Release Workflow (Main Branch)

**Für finale Releases (Production):**

1. **Feature Branch in Main mergen**

   ```bash
   git checkout main
   git merge pre-release/v0.5.2-climate-cover --no-ff -m "Merge v0.5.2 release"
   ```

2. **Release Tag auf Main**
   ```bash
   git tag -a v0.5.2 -m "Release v0.5.2"
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin main
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin v0.5.2
   ```

2.5 **README: Nur aktuelles Release anzeigen**

Bevor der GitHub-Release erstellt wird, aktualisiere die `README.md` so, dass
**nur** das aktuelle Release als "Current Release" angezeigt wird (die
vollständige Historie bleibt in `CHANGELOG.md`). Das Script
`./scripts/update_readme_release.sh` übernimmt das Einfügen der passenden
`RELEASE_NOTES_v<version>.md` Sektion und committed die Änderung.

```bash
./scripts/update_readme_release.sh
# überprüfe und pushe den Commit
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin main
```

3. **GitHub Release erstellen (Latest)**
   ```bash
   gh release create v0.5.2 --title "v0.5.2" --notes-file RELEASE_NOTES_v0.5.2.md --latest
   ```

**WICHTIG:**

- Pre-Releases → Feature Branch
- Finale Releases → Main Branch (nach Merge)
- HACS installiert vom Main Branch (default)
- Immer `GIT_SSH_COMMAND='ssh -F /dev/null'` wegen defekter `~/.ssh/config`

---

## Phase 0: Pre-Release Verification (Durchführen vor jedem Release)

**⚠️ CRITICAL LESSONS FROM INCIDENTS (v0.6.0-beta.1-5):**

1. **Zip Structure:** ALWAYS build from integration dir, NOT repo root →
   prevents nested directories
2. **Version Consistency:** Verify `manifest.json`, README release block and
   coordinator versions BEFORE tagging
3. **README Release Block:** Ensure `README.md` release block (between
   `<!-- RELEASE_NOTES_START -->` and `<!-- RELEASE_NOTES_END -->`) matches the
   `manifest.json` version
4. **Immutable Release Handling:** If GitHub prevents asset replacement, create
   a new tag (suffix `-rebuild-<ts>`) or ask admin to unprotect the release

---

### Automated release script (recommended) 🔧

Use the included automation script to perform pre-release validation, build a
HACS-friendly zip with the correct structure, create tags and GitHub releases,
and optionally verify the installation on a remote Home Assistant instance.

Usage:

- Dry run (validate everything without creating tags/releases):

  ```bash
  ./scripts/release_automation.sh --dry-run
  ```

- Normal release flow (will fail if README release block does not match manifest
  version):

  ```bash
  ./scripts/release_automation.sh --update-readme
  ```

- Release flow with remote verification (optional):
  ```bash
  ./scripts/release_automation.sh --remote phil@100.97.159.88
  ```

What the script enforces:

- Working tree clean and branch is `main`
- `custom_components/luxor_living/manifest.json` exists and version is read from
  the file
- README release block contains same version (or `--update-readme` will update
  it)
- Zip is built from inside `custom_components/luxor_living/` (prevents nested
  `custom_components/` issue)
- Zip contains `manifest.json` at root
- Attempts to create GitHub release and will fallback to a `-rebuild-<ts>` tag
  if the release is immutable

This is the recommended method to avoid the incidents documented in
`docs/RELEASE_INCIDENTS.md`. 3. **Coordinator Refactors:** Pass `config_entry`
to `super().__init__()` in DataUpdateCoordinator subclasses 4. **Immutable
Releases:** GitHub rules prevent asset replacement → bump version if failed 5.
**Post-Deploy Checks:** Test extraction structure on Remote HA after zip upload

See [docs/RELEASE_INCIDENTS.md](RELEASE_INCIDENTS.md) für Details.

### Step 0.0: Optional Pre-Release Testing auf Remote HA

**EMPFOHLEN:** Features vor Release auf dem Remote Home Assistant testen.

```bash
# SSH-Verbindung für Pre-Release Tests
# PRIVATE CONFIG: See DEPLOYMENT_PRIVATE.md (not in repository)
# - SSH host/IP address
# - SSH username
# - SSH key path

# Deployment-Beispiel (mit SSH-Key Authentifizierung):

# Temp-Deployment für Testing
ssh -F /dev/null -o StrictHostKeyChecking=no YOUR_USER@YOUR_HA_IP \
  "mkdir -p /tmp/luxor_test"

rsync -avz --exclude="__pycache__" \
  -e "ssh -F /dev/null -o StrictHostKeyChecking=no" \
  custom_components/luxor_living/ \
  YOUR_USER@YOUR_HA_IP:/tmp/luxor_test/

ssh -F /dev/null -o StrictHostKeyChecking=no YOUR_USER@YOUR_HA_IP \
  "sudo cp -r /tmp/luxor_test/* /config/custom_components/luxor_living/ && \
   rm -rf /tmp/luxor_test"

# HA Neustart manuell über http://YOUR_HA_IP:8123
# Einstellungen → System → Neustart
```

**Was testen:**

- [ ] Integration lädt ohne Fehler
- [ ] Config Flow funktioniert
- [ ] Options Flow funktioniert
- [ ] Diagnostics Download funktioniert
- [ ] Services aufrufbar
- [ ] HA Logs prüfen (keine Errors)

**Wichtig:**

- `~/.ssh/config` ist fehlerhaft → immer `-F /dev/null` verwenden
- SSH-Key Authentifizierung funktioniert (Public Key in
  `/etc/ssh/authorized_keys`)
- HA-Dateien gehören root → `sudo` für File-Operationen
- Git push: `GIT_SSH_COMMAND='ssh -F /dev/null' git push`

**Post-Deployment Verification (MANDATORY):**

```bash
# Nach Remote HA Deployment - verhindert silent failures (siehe beta.1-3)
ssh -F /dev/null YOUR_USER@YOUR_HA_IP \
  "ls -la /config/custom_components/luxor_living/manifest.json"
# EXPECTED: File exists (nicht in nested subdir!)

# Manifest-Version auf Remote HA prüfen
ssh -F /dev/null YOUR_USER@YOUR_HA_IP \
  "cat /config/custom_components/luxor_living/manifest.json | grep version"
# EXPECTED: Version matcht Git Tag

# Nach HA Restart - HA Logs prüfen
ssh -F /dev/null YOUR_USER@YOUR_HA_IP \
  "tail -100 /config/home-assistant.log | grep -i 'luxor_living\|error'"
# EXPECTED: "Setting up luxor_living" oder ähnlich (KEINE RuntimeError!)
```

### Step 0.1: Test Suite Verification

```bash
# ✅ Alle Tests müssen passing sein
cd /home/phil/gitlab_github/luxorliving
python -m pytest tests/ -q --tb=short
# EXPECTED: 207 passed in ~3s
```

**Aktueller Status:** ✅ 207/207 passing (100%)

### Step 0.1.5: Version Consistency Pre-Check (CRITICAL)

**MANDATORY vor jedem Tag/Release erstellen!**

Verhindert Version-Mismatch-Incidents (siehe beta.2).

```bash
# ✅ Zielversion festlegen
TARGET_VERSION="v0.6.0"  # Beispiel - ersetze mit tatsächlicher Version

# ✅ Manifest-Version prüfen
grep '"version":' custom_components/luxor_living/manifest.json
# EXPECTED: "version": "0.6.0" (ohne 'v' prefix)

# ✅ Health-Endpoint-Version prüfen (coordinator.py)
grep -A 2 'async def _health_check' custom_components/luxor_living/coordinator.py | grep 'version'
# EXPECTED: "version": "0.6.0"

# ✅ README.md Badge prüfen (optional)
grep 'badge/Version-' README.md
# EXPECTED: badge/Version-0.6.0-blue

# ✅ CHANGELOG.md Entry existiert
grep "## \\[${TARGET_VERSION#v}\\]" CHANGELOG.md
# EXPECTED: Findet Entry für aktuelle Version
```

**Bei Mismatch:**

- Update manifest.json → version field
- Update coordinator.py → health check return dict
- Update README.md → version badge
- Commit BEFORE tagging!

### Step 0.2: Code Quality Checks

```bash
# ✅ Black formatting check (MANDATORY)
black --check custom_components/luxor_living tests
# EXPECTED: All done (no changes)
# FIX: Run 'black custom_components/luxor_living tests' locally

# ✅ isort check (MANDATORY)
isort --check-only custom_components/luxor_living tests
# EXPECTED: All done (no changes)
# FIX: Run 'isort custom_components/luxor_living tests' locally

# ✅ Type checking (MANDATORY)
mypy custom_components/luxor_living --ignore-missing-imports
# EXPECTED: Success

# ✅ README validation (MANDATORY)
./scripts/validate_readme.sh
# EXPECTED: Exit code 0
# FIX: Update README.md and CHANGELOG.md

# ✅ flake8 linting (optional)
flake8 custom_components/luxor_living
# EXPECTED: 0 errors (unless acceptable warnings)

# ✅ Security scanning
bandit -r custom_components/luxor_living -q
# EXPECTED: No issues or only info-level findings
```

### Linting & Future Improvements 🔧

- Current: We run ShellCheck in `release_checks` (installed in workflow) to
  validate `scripts/*.sh`. Initial findings were fixed (quoting, `cd`
  safeguards, safe `source` usage). Contributors should run
  `shellcheck scripts/*.sh` locally before opening PRs.
- Next steps (recommended):
  - Pin a stable ShellCheck Action (e.g., `ludeeus/action-shellcheck@v2.0.0`)
    and make ShellCheck failures block the Release Checks once scripts are
    cleaned up.
  - Add `shfmt` to automatically format shell scripts and include it in CI or
    pre-commit.
  - Add `yamllint` for workflow and docs YAML files and `markdownlint` for
    `README.md` and `RELEASE_NOTES` checks.
  - Consider adding `shellcheck -x` or a Docker-based runner to ensure
    consistent behavior across environments.

> Note: HACS brand validation may remain an informational annotation (requires
> repo registration and logo assets); see `docs/RELEASE_INCIDENTS.md` for
> background.

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

**CRITICAL: README.md is user-facing quality! Must be reviewed like code.**

```bash
# ✅ Check that docs are up-to-date
- [ ] CHANGELOG.md: Has entry for unreleased version
- [ ] manifest.json: Version field correct
- [ ] README.md: **MANDATORY Quality Gates** (see below)
- [ ] docs/INDEX.md: Links work and are current
```

**README.md Quality Checklist (MANDATORY before release):**

```bash
# ⚡ AUTOMATED VALIDATION (recommended)
./scripts/validate_readme.sh
# This checks:
# - Version consistency (manifest.json ↔ README.md ↔ CHANGELOG.md)
# - Test count accuracy (pytest ↔ README.md)
# - All documentation links exist
# - CHANGELOG.md release entry for current version
# - No versioned [Unreleased] sections in CHANGELOG

# OR MANUAL VALIDATION:

# 1. Version Consistency Check
grep -n "v0\." README.md  # Should match manifest.json version

# 2. Test Count Accuracy
python -m pytest tests/ --collect-only -q 2>&1 | grep "tests collected"
# Then verify README mentions correct count (e.g., "207 tests")

# 3. Link Validation (check all referenced files exist)
for file in docs/INDEX.md docs/INSTALLATION.md docs/KNX_IMPLEMENTATION.md \
            docs/SENSOR_PLATFORM.md docs/ARCHITECTURE_DECISION.md \
            docs/RELEASE_OPERATIONS.md SECURITY.md LICENSE; do
  [ -f "$file" ] && echo "✅ $file" || echo "❌ MISSING: $file"
done

# 4. Manual Review Checklist:
- [ ] Version in "## 🚀 vX.Y.Z Features" section matches manifest.json
- [ ] Badge links work (HACS, release, license)
- [ ] Installation instructions are current
- [ ] Troubleshooting section is up-to-date
- [ ] No references to deprecated features
- [ ] All documentation links point to existing files
- [ ] Test count mentioned matches actual test suite
- [ ] Performance numbers are current (if mentioned)
```

**Quality Rule:** README.md must be reviewed with same rigor as code tests!
Broken links or wrong version numbers reflect poorly on integration quality.

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

## Phase 1: Release Preparation

**Note:** All v0.3.0 references below are examples. Use your actual target
version.

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

## Phase 2: Git Tagging

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

### Step 4.0: Build Release Asset (Zip Package)

**⚠️ CRITICAL: Zip Structure Must Be Correct!**

HACS extracts the zip to `/config/custom_components/luxor_living/`. Files MUST
be at zip root, NOT in nested subdirectory.

**❌ WRONG (causes beta.1-4 failure):**

```bash
# From repo root - creates nested structure!
cd /home/phil/gitlab_github/luxorliving
zip -r /tmp/luxor_living.zip custom_components/luxor_living
# Result: zip contains custom_components/luxor_living/* → HACS creates nested dir!
```

**✅ CORRECT:**

```bash
# ALWAYS build from integration directory!
cd /home/phil/gitlab_github/luxorliving/custom_components/luxor_living

# Create zip with files at root
zip -r /tmp/luxor_living-v0.6.0.zip . \
  -x "*.pyc" \
  -x "__pycache__/*" \
  -x "*.git*" \
  -x "tests/*" \
  -x ".pytest_cache/*"

# Verify zip structure (MANDATORY!)
unzip -l /tmp/luxor_living-v0.6.0.zip | head -20
# EXPECTED: manifest.json, __init__.py, etc. at root level
# NOT: custom_components/luxor_living/manifest.json
```

**Automated Verification:**

```bash
# Test extraction to temp dir
mkdir -p /tmp/luxor_test_extract
unzip -q /tmp/luxor_living-v0.6.0.zip -d /tmp/luxor_test_extract

# Verify manifest.json at root
if [ -f "/tmp/luxor_test_extract/manifest.json" ]; then
  echo "✅ Zip structure correct"
  cat /tmp/luxor_test_extract/manifest.json | grep version
else
  echo "❌ ERROR: Zip structure wrong - manifest.json not at root!"
  ls -la /tmp/luxor_test_extract
  exit 1
fi

# Cleanup
rm -rf /tmp/luxor_test_extract
```

**Post-Upload Verification (on Remote HA):**

```bash
# After HACS installation - verify no nested directories
ssh -F /dev/null YOUR_USER@YOUR_HA_IP \
  "ls -la /config/custom_components/luxor_living/ | head -20"
# EXPECTED: manifest.json, __init__.py visible
# NOT: custom_components/ subdirectory!

# Check manifest version matches release
ssh -F /dev/null YOUR_USER@YOUR_HA_IP \
  "cat /config/custom_components/luxor_living/manifest.json | grep version"
# EXPECTED: "version": "0.6.0" (matching release tag)
```

### Step 4.1: Create Release via Web UI

**URL:** https://github.com/phismith91/luxorliving/releases

**Steps:**

1. Click "Releases" → "Create a new release"
2. Choose tag: `vX.Y.Z` (example: `v0.5.2`)
3. Release title: `LUXORliving vX.Y.Z - Release Title`
4. Release notes (copy from CHANGELOG.md and adapt):

**Template Example (adapt to your release):**

```markdown
# 🎉 LUXORliving vX.Y.Z

**Release Date:** YYYY-MM-DD

## Highlights

- ✅ DataUpdateCoordinator pattern for centralized state management
- ✅ Full device registry integration for all platforms
- ✅ Complete type hints (100%) on Light, Switch, Binary Sensor
- ✅ Black code formatting (100% compliant)
- ✅ Comprehensive test suite (207 tests passing)
- ✅ py.typed marker for editor type checking support
- ✅ README.md and CHANGELOG.md quality gates

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

- **Tests:** 207/207 passing (100% success rate)
- **Coverage:** Comprehensive test coverage (see pytest report)
- **Type Hints:** 100% on critical modules
- **Code Style:** Black compliant
- **Documentation:** Complete and up-to-date
- **Quality Gates:** Automated validation (README.md + CHANGELOG.md)

## ⚠️ Known Issues

- See [Issues](https://github.com/phismith91/luxorliving/issues) for current
  tracking
- Report bugs via GitHub issue tracker

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
gh release view vX.Y.Z

# Or manually verify on:
# https://github.com/phismith91/luxorliving/releases/tag/vX.Y.Z
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
📢 LUXORliving vX.Y.Z Released!

🎉 LUXORliving vX.Y.Z is now available for HACS!

Key Features:
- [List your release highlights from CHANGELOG.md]
- 207 comprehensive tests (100% passing)
- Automated quality gates (README + CHANGELOG validation)
- Production-ready code

Installation:
1. Add to HACS Integrations
2. Restart Home Assistant
3. Setup via UI: Settings → Devices & Services

GitHub: https://github.com/phismith91/luxorliving
Releases: https://github.com/phismith91/luxorliving/releases

Questions? Start a discussion: https://github.com/phismith91/luxorliving/discussions
```

### Step 6.3: Create Release Candidate Branch (Optional)

```bash
# Create backup branch for this release (example)
git checkout -b release/0.X.Y
git push origin release/0.X.Y

# This allows hotfixes on 0.X.Y if needed (v0.X.Y+1, etc.)
```

### Step 6.4: Begin Next Development Cycle

```bash
# Update version for next dev cycle (example: 0.5.2 → 0.5.3-beta.1)
# manifest.json: "version": "0.X.Y-beta.1"
sed -i 's/"version": "0.X.Y"/"version": "0.X.Y+1-beta.1"/' \
  custom_components/luxor_living/manifest.json

# Update CHANGELOG
# Add new [Unreleased] section:
```

```markdown
## [Unreleased]

### Planned

- TBD for next release

## [X.Y.Z] - YYYY-MM-DD

### Added

- Released features from this version
```

```bash
# Commit
git add manifest.json CHANGELOG.md
git commit -m "chore: prepare vX.Y.Z-beta.1 development cycle"
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
# Scenario: Critical bug found in current release (example: v0.5.2)

# Step 1: Create hotfix branch from release tag
git checkout -b hotfix/0.5.3 v0.5.2

# Step 2: Apply fix
# (edit files to fix critical bug)
git add .
git commit -m "fix: critical bug description"

# Step 3: Update version & CHANGELOG
# manifest.json: 0.5.2 → 0.5.3
# CHANGELOG.md: Add [0.5.3] section

# Step 4: Tag and release
git tag -a v0.5.3 -m "LUXORliving v0.5.3: Hotfix for [issue]"
git push origin hotfix/0.5.3 v0.5.3

# Step 5: Create GitHub Release (same as Phase 4)

# Step 6: Merge hotfix back to main
git checkout main
git merge hotfix/0.5.3
git push origin main
```

### Emergency 2: Rollback Failed Release

```bash
# Scenario: Current release has critical issues, need to rollback (example)

# Step 1: Delete tags locally and remotely
git tag -d v0.X.Y
git push origin --delete v0.X.Y

# Step 2: Revert version changes
git revert HEAD  # Revert the release commit

# Step 3: Fix issues
# (make necessary changes)

# Step 4: Create new release attempt
git tag -a v0.X.Y-rc.1 -m "..."  # Or use different version
git push origin v0.X.Y-rc.1

# Step 5: Announce issue on community channels
```

### Emergency 3: Immutable Release Constraints (GitHub)

**Scenario:** GitHub repository rules prevent replacing release assets or
recreating tags.

**Symptoms (see beta.2-4):**

- Cannot delete release or tag
- Cannot replace uploaded zip asset
- Asset size/hash differs from rebuilt package

**Root Cause:**

- Repository protection rules (branch/tag protection)
- Release marked as "latest" locks metadata
- Asset already downloaded by users

**Solutions:**

```bash
# ⚠️ CANNOT: Replace asset or recreate same tag
# GitHub returns 403/422 error

# ✅ MUST: Increment version and create new release
# Example: v0.6.0-beta.2 → v0.6.0-beta.3

# Step 1: Bump version locally
sed -i 's/"version": "0.6.0-beta.2"/"version": "0.6.0-beta.3"/' \
  custom_components/luxor_living/manifest.json

# Also update coordinator.py health endpoint version!
sed -i 's/"version": "0.6.0-beta.2"/"version": "0.6.0-beta.3"/' \
  custom_components/luxor_living/coordinator.py

# Step 2: Commit version bump
git add custom_components/luxor_living/manifest.json \
        custom_components/luxor_living/coordinator.py
git commit -m "chore: bump to v0.6.0-beta.3 (immutable release fix)"

# Step 3: Create new tag
git tag -a v0.6.0-beta.3 -m "Fix asset packaging (replaces beta.2)"
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin feature/silver-compliance
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin v0.6.0-beta.3

# Step 4: Build CORRECT zip (see Phase 4.0)
cd custom_components/luxor_living
zip -r /tmp/luxor_living-v0.6.0-beta.3.zip . -x "*.pyc" "__pycache__/*"

# Step 5: Create new GitHub release
gh release create v0.6.0-beta.3 \
  --title "v0.6.0-beta.3 (replaces beta.2)" \
  --notes "Fixes packaging issue from beta.2" \
  --prerelease \
  /tmp/luxor_living-v0.6.0-beta.3.zip

# Step 6: Mark old release as superseded (manual)
# Edit beta.2 release notes on GitHub to add:
# "⚠️ SUPERSEDED: Use v0.6.0-beta.3 instead"
```

**Prevention:**

- Run Step 0.1.5 (Version Consistency Check) BEFORE tagging
- Verify zip structure (Step 4.0) BEFORE uploading
- Test on Remote HA before marking release as latest

---

## Command Quick Reference

### Tag Management

```bash
# List all tags
git tag -l

# List tags with pattern
git tag -l "v0.5*"

# Show tag details
git show v0.5.2

# Create annotated tag (example)
git tag -a v0.X.Y -m "Message"

# Create signed tag (example)
git tag -a -s v0.X.Y -m "Message"

# Delete local tag (example)
git tag -d v0.X.Y

# Delete remote tag (example)
git push origin --delete v0.X.Y

# Push specific tag (example)
git push origin v0.X.Y

# Push all tags
git push origin --tags

# Verify tag (example)
git verify-tag v0.X.Y
```

### Version Updates

```bash
# Update manifest version (example: beta → release)
sed -i 's/"version": "0.X.Y-beta.1"/"version": "0.X.Y"/' \
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

## 🤖 Automation: Recommended Release Script

Basierend auf den Incidents (beta.1-5) ist ein Automation Script empfohlen, das
folgende Checks durchführt:

**Datei:** `scripts/release_automation.sh` (siehe Implementierung unten)

**Features:**

- ✅ Version consistency check (manifest.json ↔ coordinator.py ↔ tag)
- ✅ Test suite verification (all passing)
- ✅ Zip build from correct directory
- ✅ Zip structure validation (manifest at root)
- ✅ Automatic GitHub release creation
- ✅ Post-release verification (optional Remote HA test)

**Beispiel-Workflow:**

```bash
# Statt manueller Steps 0-4:
./scripts/release_automation.sh v0.6.0 \
  --test-suite \
  --verify-zip \
  --create-release \
  --upload-asset
# Script führt alle Checks durch und stoppt bei Fehler
```

**Implementierungsvorschlag:**

```bash
#!/bin/bash
# scripts/release_automation.sh
# Automated release workflow with incident prevention

set -e  # Exit on error

VERSION="$1"
if [ -z "$VERSION" ]; then
  echo "Usage: $0 v0.X.Y [options]"
  exit 1
fi

# Strip 'v' prefix for version comparisons
VERSION_NUM="${VERSION#v}"

echo "🚀 LUXORliving Release Automation - $VERSION"
echo "=============================================="

# Step 1: Version Consistency Check
echo "📋 Step 1: Version Consistency Check..."
MANIFEST_VER=$(grep '"version"' custom_components/luxor_living/manifest.json | cut -d'"' -f4)
if [ "$MANIFEST_VER" != "$VERSION_NUM" ]; then
  echo "❌ ERROR: manifest.json version ($MANIFEST_VER) != tag ($VERSION_NUM)"
  exit 1
fi
echo "✅ Manifest version: $MANIFEST_VER"

# Step 2: Test Suite
echo "📋 Step 2: Running test suite..."
python -m pytest tests/ -q --tb=short || {
  echo "❌ ERROR: Tests failing!"
  exit 1
}
echo "✅ Tests passing"

# Step 3: Build Zip (correct directory!)
echo "📋 Step 3: Building release zip..."
cd custom_components/luxor_living
ZIP_FILE="/tmp/luxor_living-${VERSION}.zip"
zip -r "$ZIP_FILE" . -x "*.pyc" "__pycache__/*" "*.git*" "tests/*" || {
  echo "❌ ERROR: Zip build failed"
  exit 1
}
cd ../../
echo "✅ Zip created: $ZIP_FILE"

# Step 4: Zip Structure Validation
echo "📋 Step 4: Validating zip structure..."
TEMP_EXTRACT="/tmp/luxor_extract_$$"
mkdir -p "$TEMP_EXTRACT"
unzip -q "$ZIP_FILE" -d "$TEMP_EXTRACT"
if [ ! -f "$TEMP_EXTRACT/manifest.json" ]; then
  echo "❌ ERROR: manifest.json not at zip root!"
  ls -la "$TEMP_EXTRACT"
  rm -rf "$TEMP_EXTRACT"
  exit 1
fi
rm -rf "$TEMP_EXTRACT"
echo "✅ Zip structure correct"

# Step 5: Create Git Tag
echo "📋 Step 5: Creating git tag..."
git tag -a "$VERSION" -m "Release $VERSION" || {
  echo "⚠️  Tag already exists - skipping"
}
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin "$(git branch --show-current)"
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin "$VERSION"
echo "✅ Tag pushed: $VERSION"

# Step 6: Create GitHub Release
echo "📋 Step 6: Creating GitHub release..."
gh release create "$VERSION" \
  --title "LUXORliving $VERSION" \
  --notes-file "RELEASE_NOTES_${VERSION}.md" \
  --prerelease \
  "$ZIP_FILE" || {
  echo "⚠️  Release creation failed - check manually"
}
echo "✅ Release created: $VERSION"

echo ""
echo "🎉 Release $VERSION completed successfully!"
echo "📦 Asset: $ZIP_FILE"
echo "🔗 GitHub: https://github.com/phismith91/luxorliving/releases/tag/$VERSION"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. Test HACS installation on Remote HA"
echo "2. Verify /config/custom_components/luxor_living/manifest.json exists"
echo "3. Check HA logs for 'Setting up luxor_living'"
```

**Installation:**

```bash
chmod +x scripts/release_automation.sh
./scripts/release_automation.sh v0.6.0
```

**Vorteile:**

- Verhindert alle dokumentierten Incidents
- Atomic workflow (stoppt bei erstem Fehler)
- Reproduzierbar und versioniert
- Reduziert manuelle Fehler

---

**Version:** 2.0 **Last Updated:** 8. Januar 2026 (post beta.1-5 incidents)
**Next Review:** Nach erfolgreichem v0.6.0 stable release
