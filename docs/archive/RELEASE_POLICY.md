# 🎯 Release Manager Policy: Feature Branch Pre-Releases

**Approved:** 23. Dezember 2025  
**Author:** Release Manager Agent  
**Status:** ✅ ACTIVE POLICY

---

## The Policy

**Every feature branch that reaches testing readiness must have a pre-release created.**  
**Only code in main branch gets a stable release.**

### Simple Rule:

```
Feature Branch (feature/*)  → Pre-Release (v0.X.0-beta.1)
Main Branch (main)          → Release (v0.X.0)
```

---

## When to Create Pre-Release

✅ **DO CREATE** v0.4.0-beta.1 when:
- Code compiles and runs
- Feature is functionally complete
- Basic functionality tested
- Ready for community feedback

❌ **DON'T CREATE** if:
- Code doesn't compile
- Syntax errors present
- Completely broken functionality

---

## When to Create Release (Stable)

✅ **DO CREATE** v0.4.0 when:
- Merged to main branch
- **ALL tests passing** (74/74)
- Coverage ≥ 55%
- Code review approved
- Documentation complete

❌ **DON'T CREATE** if:
- Any test fails
- Tests not run
- Code review pending
- Version not bumped

---

## Quick Commands

### Create Pre-Release:
```bash
# 1. Update version
sed -i 's/"version": "0.3.0"/"version": "0.4.0-beta.1"/' \
  custom_components/luxor_living/manifest.json

# 2. Commit
git add manifest.json
git commit -m "chore: prepare v0.4.0-beta.1 pre-release"

# 3. Tag
git tag -a v0.4.0-beta.1 -m "Pre-Release v0.4.0-beta.1"

# 4. Push & Release
git push origin v0.4.0-beta.1
gh release create v0.4.0-beta.1 --prerelease --notes "Pre-Release Testing"
```

### Create Release (Main):
```bash
# 1. Ensure on main
git checkout main
git pull origin main

# 2. Run full tests (MANDATORY!)
pytest tests/ -v --tb=short --cov

# 3. Update version & CHANGELOG
# manifest.json: 0.4.0-beta.1 → 0.4.0
# CHANGELOG.md: [Unreleased] → [0.4.0] - 2025-12-23

# 4. Commit
git add manifest.json CHANGELOG.md
git commit -m "release(v0.4.0): bump version for main release"

# 5. Tag
git tag -a v0.4.0 -m "Release v0.4.0"

# 6. Push & Release
git push origin v0.4.0
gh release create v0.4.0 --notes "Release v0.4.0 - Production Ready"
```

---

## Version Examples

| Branch | Version | Status | Tests | HACS |
|--------|---------|--------|-------|------|
| feature/core-integration | v0.4.0-beta.1 | Testing | No | ❌ |
| feature/core-integration | v0.4.0-rc.1 | Release Candidate | No | ❌ |
| main | v0.4.0 | Production | **YES** ✅ | ✅ |
| main | v0.4.1 | Hotfix | **YES** ✅ | ✅ |

---

## Current Status (v0.3.0)

✅ Pre-Release Created: v0.3.0-beta.1 (feature branch)  
✅ Release Created: v0.3.0 (GitHub release, marked as pre-release)  
✅ Tests: 74/74 passing  
✅ Coverage: 55%  

**Next:** Merge feature/core-integration to main, run full tests, release v0.4.0

---

## Benefits of This Approach

| Benefit | Pre-Release | Stable Release |
|---------|-------------|-----------------|
| Community Feedback | ✅ Yes | ✅ Yes |
| Production Safe | ❌ No | ✅ Yes |
| Tests Required | ❌ No | ✅ YES |
| HACS Listed | ❌ No | ✅ Yes |
| Breaking Changes | ⚠️ Possible | ✅ None |

---

## No More Broken Main Releases

**Old Way:**
```
feature/core-integration (untested)
  ↓
main branch release (TEST FAILS!)
  ↓
❌ Broken release in production
```

**New Way:**
```
feature/core-integration (pre-release)
  ↓ (community testing)
v0.4.0-beta.1 → v0.4.0-rc.1 (feedback incorporated)
  ↓
main branch (all tests pass!)
  ↓
✅ v0.4.0 stable release guaranteed
```

---

## Checklist: Pre-Release

```
Feature Branch Ready?
  [ ] Code compiles
  [ ] Basic functionality works
  [ ] No syntax errors
  [ ] Ready for testing

Create Pre-Release:
  [ ] Version bumped to v0.4.0-beta.1
  [ ] CHANGELOG updated
  [ ] Git tag created
  [ ] GitHub release marked as pre-release
  [ ] Installation instructions provided

Distribute:
  [ ] GitHub release published
  [ ] Community notified (optional)
  [ ] Testing instructions clear
  [ ] Known issues documented
```

---

## Checklist: Main Release

```
Feature Ready for Main?
  [ ] Tests: 74/74+ passing (RUN THEM!)
  [ ] Coverage: ≥ 55%
  [ ] Code review approved
  [ ] Documentation complete
  [ ] CHANGELOG updated with release date
  [ ] Version bumped in manifest.json
  [ ] No critical issues pending

Merge to Main:
  [ ] Feature branch merged to main
  [ ] Tests re-run on main (all pass!)
  [ ] Staging environment tested (if available)

Create Release:
  [ ] Git tag v0.4.0 created
  [ ] GitHub release created (NOT pre-release)
  [ ] Release notes comprehensive
  [ ] Installation instructions included
  [ ] Links to documentation present

Publish:
  [ ] Release published on GitHub
  [ ] Announcements sent (if appropriate)
  [ ] Version tracked in project
  [ ] Stable release marked in releases page
```

---

## Rules (Non-Negotiable)

1. **NO releases from feature branches without pre-release marker**
   - Use `-beta`, `-rc`, `-alpha` suffix
   - Mark as "pre-release" on GitHub
   - Clearly document as testing version

2. **NO releases to main without full test suite**
   - Run: `pytest tests/ -v --tb=short --cov`
   - Must have: 74/74+ tests passing
   - Must have: Coverage ≥ 55%
   - No exceptions

3. **NO versions without tags**
   - Every release must have git tag
   - Tag must match version in manifest.json
   - Tag messages must be descriptive

4. **NO main branch releases without CHANGELOG update**
   - Update CHANGELOG.md BEFORE tagging
   - Use format: `## [0.4.0] - 2025-12-23`
   - Include summary of changes

5. **NO skipping code review**
   - All code must be reviewed before main merge
   - Tests must pass before merge
   - Documentation must be reviewed

---

## Enforcement

**Recommended GitHub Branch Protection:**

```yaml
# Main branch protection rules
- Require pull request reviews (1 approving review)
- Require status checks to pass
  - ✅ pytest (all tests pass)
  - ✅ black (formatting)
  - ✅ isort (imports)
  - ✅ mypy (type hints)
  - ✅ flake8 (linting)
- Require branches to be up to date before merge
- Include administrators in restrictions
```

---

## Examples in Action

### Example 1: v0.4.0 Climate Feature

```
WEEK 1: Pre-Release
  └─ feature/climate-support
     ├─ Development and testing
     ├─ v0.4.0-beta.1 created (GitHub release)
     └─ Community feedback: "Works great!"

WEEK 2: Refinement
  ├─ v0.4.0-beta.2 (more features)
  ├─ v0.4.0-rc.1 (release candidate)
  └─ "Ready for production!"

WEEK 3: Main Release
  ├─ Merge feature/climate-support to main
  ├─ Run tests: 74/74 ✅
  ├─ v0.4.0 stable release created ✅
  └─ Available in HACS marketplace
```

### Example 2: v0.4.1 Security Hotfix

```
WEEK 1: Emergency Fix
  └─ feature/security-hotfix
     ├─ Critical issue fixed
     ├─ v0.4.1-rc.1 created (urgent release)
     └─ Community testing in 1 hour

WEEK 1 (later): Main Release
  ├─ Merge to main
  ├─ Run tests: 74/74 ✅
  ├─ v0.4.1 released immediately ✅
  └─ Announcement sent to users
```

---

**This is the new standard. No exceptions.**

Release Manager Agent - 23. Dezember 2025
