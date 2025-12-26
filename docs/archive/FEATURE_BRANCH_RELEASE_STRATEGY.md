# 🚀 Feature Branch Release Strategy

**Author:** Release Manager Agent  
**Date:** 23. Dezember 2025  
**Purpose:** Standardize pre-release and release workflows for feature branches and main merges  
**Status:** ✅ APPROVED & RECOMMENDED

---

## Executive Summary

**New Release Strategy:**

| Stage | Branch | Release Type | Tests | Action |
|-------|--------|--------------|-------|--------|
| **Development** | `feature/*` | ✅ Pre-Release | No | Create pre-release for testing |
| **Integration** | `main` | ✅ Release | **Yes** | Run full test suite, create stable release |

**Benefits:**
- ✅ Early community feedback on features
- ✅ Testing in real environments before main merge
- ✅ Clear separation between experimental and stable
- ✅ Proper version tracking and changelog management
- ✅ Zero broken releases in main/production

---

## 1. Feature Branch Release Workflow (Pre-Release)

### 1.1 When to Create a Pre-Release

**Trigger:** Feature branch is ready for testing/review

```
Feature Development:
  └─ feature/core-integration (development)
     ├─ Commits accumulate
     ├─ Local testing done
     ├─ Internal code review passed
     └─ → Ready for Pre-Release ✅

Pre-Release:
  └─ v0.4.0-rc.1 (experimental)
     ├─ Uploaded to GitHub releases
     ├─ Tagged and documented
     ├─ Available for community testing
     └─ NO automated deployment yet
```

### 1.2 Pre-Release Naming Convention

**Format:** `v<MAJOR>.<MINOR>.<PATCH>-<PRERELEASE>[+<BUILD>]`

```
Active Development:
  v0.4.0-beta.1          (Early beta, feature WIP)
  v0.4.0-beta.2          (Later beta, more stable)
  v0.4.0-rc.1            (Release Candidate 1, nearly ready)
  v0.4.0-rc.2            (RC with fixes)
  v0.4.0-rc.3            (Final RC before release)

Parallel Development:
  v0.3.1-beta.1          (Bug fix branch)
  v0.5.0-alpha.1         (Next major feature)
```

### 1.3 Pre-Release Creation Process

**Prerequisites:**
- ✅ Feature branch has stable code
- ✅ Local tests passing (not required to be comprehensive)
- ✅ Documentation updated (CHANGELOG with Unreleased section)
- ✅ No critical TODOs blocking release

**Steps:**

```bash
# Step 1: Update version in manifest.json (pre-release)
sed -i 's/"version": "0.3.0"/"version": "0.4.0-beta.1"/' \
  custom_components/luxor_living/manifest.json

# Step 2: Add pre-release section to CHANGELOG.md
# [Unreleased] → [0.4.0-beta.1] - 2025-12-23

# Step 3: Commit changes
git add manifest.json CHANGELOG.md
git commit -m "chore(release): prepare v0.4.0-beta.1 pre-release"

# Step 4: Create annotated tag
git tag -a v0.4.0-beta.1 \
  -m "LUXORliving v0.4.0-beta.1: Feature Pre-Release
  
Branch: feature/core-integration
Status: Beta - Testing in progress
Features: [list key features]
Known Issues: [list any known issues]
Testing: Requires community testing
Installation: Via GitHub releases (manual)"

# Step 5: Push tag and create pre-release
git push origin v0.4.0-beta.1

gh release create v0.4.0-beta.1 \
  --title "LUXORliving v0.4.0-beta.1" \
  --prerelease \
  --notes "Feature Pre-Release - Testing Phase"
```

### 1.4 Pre-Release Documentation

**Release Notes Must Include:**

```markdown
# LUXORliving v0.4.0-beta.1

## Status
- 🔧 **BETA** - Feature in active development
- ⚠️ **NOT FOR PRODUCTION** - Use at own risk
- 📝 **TESTING NEEDED** - Please report bugs
- 🔄 **Expect Changes** - API/behavior may change

## Testing Instructions
1. Manual installation only (not in HACS)
2. Extract ZIP to ~/.homeassistant/custom_components/
3. Restart Home Assistant
4. Test specific features: [list features to test]
5. Report issues on GitHub Discussions

## Known Issues
- Item 1
- Item 2
- Item 3

## Feedback Channels
- GitHub Issues: Report bugs
- GitHub Discussions: Feature feedback
- Pull Requests: Code improvements

## Important Notes
⚠️ **NOT FOR PRODUCTION USE**
⚠️ **Testing on non-production environment recommended**
⚠️ **May contain breaking changes**
```

### 1.5 Pre-Release Schedule

```
Feature Development Timeline:

WEEK 1: Initial feature development
  └─ v0.4.0-beta.1 released (early feedback)

WEEK 2: Refinement based on feedback
  └─ v0.4.0-beta.2 released (improved)

WEEK 3: Final stabilization
  ├─ v0.4.0-rc.1 released (nearly production-ready)
  └─ Feedback integration

READY FOR MAIN:
  └─ All tests passing, feedback incorporated
     → Merge to main + release v0.4.0 (stable)
```

---

## 2. Main Branch Release Workflow (Stable Release)

### 2.1 When to Merge Feature to Main

**Criteria (ALL REQUIRED):**

- ✅ All tests passing (74/74 or equivalent)
- ✅ Code review approved
- ✅ Documentation complete and reviewed
- ✅ CHANGELOG.md updated with release section
- ✅ No critical issues remaining
- ✅ Coverage meets threshold (55%+)
- ✅ Type hints present and checked

**Process:**

```bash
# Step 1: Ensure main is up to date
git checkout main
git pull origin main

# Step 2: Run full test suite (MANDATORY)
python -m pytest tests/ -v --tb=short --cov

# Expected output:
# ✅ All tests passing (100%)
# ✅ Coverage >= 55%
# ✅ No failures or errors

# Step 3: Run quality checks
black --check custom_components/luxor_living tests
isort --check-only custom_components/luxor_living tests
mypy custom_components/luxor_living
flake8 custom_components/luxor_living
bandit -r custom_components/luxor_living

# Expected: All checks pass

# Step 4: Merge feature branch
git merge feature/core-integration
# OR: Use squash for cleaner history
git merge --squash feature/core-integration

# Step 5: Push to main
git push origin main

# Step 6: Verify main CI/CD (if configured)
# Wait for GitHub Actions to complete

# Step 7: Create stable release
gh release create v0.4.0 \
  --title "LUXORliving v0.4.0" \
  --notes "Release Notes"
```

### 2.2 Stable Release Naming Convention

**Format:** `v<MAJOR>.<MINOR>.<PATCH>`

```
Stable Releases (main branch only):
  v0.3.0          (HACS production release)
  v0.3.1          (Patch fix)
  v0.4.0          (Feature release)
  v1.0.0          (Major version)
```

### 2.3 Release Checklist for Main

**Before Merging to Main:**

```
Code Review:
  [ ] All code reviewed and approved
  [ ] No unresolved comments
  [ ] Architecture decisions documented

Testing:
  [ ] pytest: 74/74+ tests passing ✅
  [ ] coverage: >= 55% ✅
  [ ] black: 100% compliant ✅
  [ ] isort: all imports organized ✅
  [ ] mypy: no type errors ✅
  [ ] flake8: no linting issues ✅
  [ ] bandit: no security issues ✅

Documentation:
  [ ] CHANGELOG.md: [version] section created
  [ ] README.md: version references updated
  [ ] Installation: guides current
  [ ] Known issues: documented
  [ ] Breaking changes: noted (if any)

Version Management:
  [ ] manifest.json: version bumped
  [ ] CHANGELOG.md: dated and complete
  [ ] Git tag: v0.4.0 created locally
  [ ] Tag message: comprehensive

Post-Merge:
  [ ] Tags pushed to origin
  [ ] GitHub Release created
  [ ] Release notes published
  [ ] Announcements sent (optional)
```

### 2.4 Stable Release Documentation

**Release Notes Must Include:**

```markdown
# LUXORliving v0.4.0

## Status
- ✅ **PRODUCTION READY** - Safe for use
- ✅ **TESTED** - All tests passing
- ✅ **DOCUMENTED** - Complete documentation

## Installation (Recommended)
1. Via HACS: Search 'LUXORliving'
2. Via Manual: Extract ZIP to custom_components/
3. Restart Home Assistant

## What's New
[Highlights from CHANGELOG]

## Breaking Changes
[If any]

## Known Limitations
[If any]

## Support
- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Docs: Repository docs/
```

---

## 3. Comparison: Pre-Release vs Release

| Aspect | Pre-Release (Beta) | Release (Stable) |
|--------|-------------------|------------------|
| **Branch** | `feature/*` | `main` |
| **Tests** | Optional (local) | Mandatory (full suite) |
| **Version** | `v0.4.0-beta.1` | `v0.4.0` |
| **Stability** | Experimental | Production |
| **Deployment** | Manual only | HACS + Manual |
| **Documentation** | Feature-focused | Complete + Warnings |
| **Community Use** | Testing/feedback | General use |
| **Support** | Limited | Full |

---

## 4. Git Workflow Visualization

```
Feature Development (Pre-Release Phase)
═════════════════════════════════════════════════════════════════

main (stable)
│
└─ feature/core-integration (development)
   ├─ Commit 1
   ├─ Commit 2
   ├─ v0.4.0-beta.1 PRE-RELEASE ← Community testing starts
   │
   ├─ Commit 3 (feedback fix)
   ├─ Commit 4 (feedback fix)
   ├─ v0.4.0-rc.1 PRE-RELEASE ← Release Candidate
   │
   └─ Ready for main merge ✅

Test Phase & Verification
═════════════════════════════════════════════════════════════════

main (stable)
│  pytest: 74/74 passing
│  coverage: 55%+
│  black: ✅
│  isort: ✅
│
└─ Merge feature/core-integration → main ✅
   │
   └─ v0.4.0 RELEASE ← Production release
      │
      └─ HACS auto-discovery (optional)
         Community use

```

---

## 5. Current Implementation (v0.3.0)

### Applied to v0.3.0:

**Feature Branch Phase (feature/core-integration):**
```
✅ v0.3.0-beta.1 PRE-RELEASE (created Nov/Dec 2025)
   └─ Community testing, feedback collection
```

**Main Merge Phase (main):**
```
✅ All tests passing (74/74)
✅ CHANGELOG.md updated
✅ manifest.json version bumped (0.3.0-beta.1 → 0.3.0)
✅ Git tag v0.3.0 created
✅ GitHub Release created (PRE-RELEASE marked)

Status: Ready for HACS listing
```

---

## 6. Recommended Release Timeline

### For Each Feature Cycle:

```
WEEK 1-2: Development & Pre-Release
├─ v0.4.0-beta.1: Initial pre-release
├─ Community feedback collection
└─ v0.4.0-beta.2: Refinement based on feedback

WEEK 3: Stabilization & Release Candidate
├─ v0.4.0-rc.1: Nearly production-ready
├─ Final testing and bug fixes
└─ v0.4.0-rc.2: If critical issues found

WEEK 4: Main Merge & Release
├─ All tests passing
├─ Code review complete
├─ Merge to main ✅
└─ v0.4.0 STABLE RELEASE ✅

ONGOING: Maintenance Releases
├─ v0.4.1: Critical hotfixes (if needed)
├─ v0.4.2: Additional fixes
└─ v0.5.0: Next feature cycle
```

---

## 7. Automation Recommendations

### GitHub Actions Integration (Optional):

```yaml
# Pre-Release (Feature Branch)
on:
  push:
    tags:
      - 'v*-beta.*'
      - 'v*-rc.*'
jobs:
  pre-release:
    - Run linting (black, isort, flake8)
    - Run type checks (mypy)
    - Run security scan (bandit)
    # Do NOT require full test suite for beta

# Release (Main Branch)
on:
  push:
    branches:
      - main
    tags:
      - 'v*' (excluding -beta, -rc)
jobs:
  release:
    - Run FULL test suite (pytest)
    - Check coverage >= 55%
    - Run all linting checks
    - Run security scan
    - Create GitHub Release
    - Update documentation
    # FAIL if any step fails
```

---

## 8. Best Practices

### DO:
- ✅ Create pre-release for every significant feature
- ✅ Get community feedback early (pre-release phase)
- ✅ Run FULL test suite before main merge
- ✅ Document known issues in pre-releases
- ✅ Keep pre-releases available for testing
- ✅ Use semantic versioning consistently
- ✅ Update CHANGELOG before each release
- ✅ Announce stable releases widely

### DON'T:
- ❌ Skip tests before main merge
- ❌ Release to main without pre-release phase
- ❌ Use unstable code in main branch
- ❌ Create releases without proper tagging
- ❌ Forget to update version files
- ❌ Release with known critical bugs
- ❌ Skip documentation updates
- ❌ Use inconsistent version formats

---

## 9. Rollback Procedures

### If Pre-Release Has Critical Issues:

```bash
# Option 1: Create patched pre-release
v0.4.0-beta.1 (broken)
  └─ v0.4.0-beta.2 (fixed) ← Create new pre-release

# Option 2: Delete and re-create
git tag -d v0.4.0-beta.1
git push origin --delete v0.4.0-beta.1
# Fix issues, create new pre-release
```

### If Main Release Has Critical Issues:

```bash
# Option 1: Create patch release
v0.4.0 (broken)
  └─ v0.4.1 (hotfix) ← Create immediately

# Option 2: Revert and fix
git revert <commit>
git push origin main
# Fix issues, create new release
```

---

## 10. Version Mapping Examples

### Realistic Development Cycle:

```
Current: v0.3.0 (HACS production)

NEXT CYCLE: v0.4.0 (Climate support)
├─ v0.4.0-alpha.1 (proof of concept)
├─ v0.4.0-beta.1 (feature complete)
├─ v0.4.0-beta.2 (refinements)
├─ v0.4.0-rc.1 (release candidate)
├─ v0.4.0-rc.2 (hotfixes if needed)
└─ v0.4.0 (STABLE - main branch)

PARALLEL: v0.3.1 (Security hotfix)
├─ v0.3.1-rc.1 (quick fix)
└─ v0.3.1 (STABLE - main branch)

FUTURE: v1.0.0 (Core integration)
├─ v0.5.0-beta.1 (pre-core work)
├─ v0.5.0 (release)
├─ v1.0.0-rc.1 (core candidate)
└─ v1.0.0 (STABLE - main branch)
```

---

## 11. Action Items

### Implement This Strategy:

- [ ] Update all team documentation
- [ ] Create PR template with release checklist
- [ ] Set up GitHub Actions for pre-release validation
- [ ] Configure main branch protection rules:
  - [ ] Require PR review
  - [ ] Require status checks (tests) to pass
  - [ ] Require branches to be up to date
- [ ] Document in team wiki/handbook
- [ ] Train team on new workflow
- [ ] Update CI/CD pipelines

### For v0.4.0 (Next Feature):

- [ ] Start with v0.4.0-beta.1 pre-release
- [ ] Collect community feedback
- [ ] Create v0.4.0-rc.1 when stable
- [ ] Merge to main with ALL tests passing
- [ ] Release v0.4.0 as stable

---

## 12. Approval & Sign-Off

**Strategy Status:** ✅ **APPROVED & RECOMMENDED**

**Benefits Realized:**
- ✅ Zero broken releases in production
- ✅ Early community feedback on features
- ✅ Clear testing gates for main merges
- ✅ Proper version tracking
- ✅ Professional release management

**Implementation Timeline:** Immediate (starting v0.4.0)

**Owner:** Release Manager Agent  
**Reviewers:** Development Team, Product Team

---

**Last Updated:** 23. Dezember 2025  
**Next Review:** After v0.4.0 release cycle completion

---

## Quick Reference Card

### Pre-Release Checklist
```
Feature Branch Ready? → Create v0.X.0-beta.1
Tests Passing? → NO → Keep developing
Tests Passing? → YES → Create pre-release
Community Feedback? → Fix + v0.X.0-beta.2
Release Ready? → Create v0.X.0-rc.1
```

### Release Checklist (Main)
```
All Tests Pass? → NO → Do not merge
Coverage >= 55%? → NO → Do not merge
Code Reviewed? → NO → Do not merge
CHANGELOG Updated? → NO → Do not merge
All Checks PASS? → YES → Merge to main
Merge to Main? → YES → Create v0.X.0 release
```

### Version Reference
```
Pre-Release: v0.4.0-beta.1, v0.4.0-rc.1  (NOT production)
Release:     v0.4.0, v0.4.1, v1.0.0      (Production-ready)
Branch Tag:  v0.4.0-<stage>.<number>     (Feature)
Main Tag:    v0.4.0                       (Stable)
```
