# Branching Strategy

This document explains how we organize branches and what naming conventions we use.

## Branch Types

### Production Branches
- **`main`** — stable, release-ready code
  - Protected: requires PR review + status checks
  - Merge only via PR (no force-push)
  - Each merge should be release-ready or close to it

### Work Branches
Use these for your contributions. They follow a naming convention:

| Type | Pattern | Example | Purpose |
|------|---------|---------|---------|
| Feature | `feature/*` | `feature/add-cover-position` | New functionality |
| Bug fix | `bugfix/*` | `bugfix/fix-timeout-on-reconnect` | Bug fixes |
| Docs | `docs/*` | `docs/update-readme` | Documentation only |
| Chore | `chore/*` | `chore/upgrade-pytest` | Dependencies, refactoring, tooling |
| Experimental | `exp/*` | `exp/try-new-parser` | Experimental / don't merge yet |

### Release Branches (Admin only)
- **`release/vX.Y.Z`** — prepare a release (rarely used; usually direct releases from `main`)

---

## Workflow at a Glance

```
┌─── (1) Create branch from main
│
feature/your-feature ──→ (2) Push commits
│                           ↓
│                      Fast checks run (black, isort, smoke)
│                           ↓
│                      (3) Open PR
│                           ↓
│                      Faster checks + Review
│                           ↓
│                      (4) Optional: add run-qa-matrix label
│                           ↓
│                      Full QA matrix runs (Python × HA)
│                           ↓
│                      (5) Approve & merge to main
│
└─── main (protected, release-ready)
```

---

## Naming Rules

1. **Use lowercase**  
   ✅ `feature/add-cover` — YES  
   ❌ `Feature/Add-Cover` — NO

2. **Use hyphens for word separation**  
   ✅ `feature/add-cover-position` — YES  
   ❌ `feature/add_cover_position` — NO

3. **Be descriptive but concise**  
   ✅ `feature/add-cover-position-sync` — YES  
   ❌ `feature/stuff` or `f1` — NO

4. **No special characters except hyphen**  
   ✅ `bugfix/fix-config-flow-timeout` — YES  
   ❌ `bugfix/fix-config.flow@timeout` — NO

---

## When to Delete Your Branch

After your PR is merged, GitHub offers to delete your branch. **Do it** — keeps the repo clean.

If you forget:
```bash
git branch -d feature/your-feature  # Local
git push origin --delete feature/your-feature  # Remote
```

---

## Special Cases

### Long-running Feature Branches
If you're working on a big feature over multiple days:
1. Keep your branch up to date with `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   git push -f origin feature/your-feature
   ```
2. Push regularly so others can see progress.
3. Open a **draft PR** early to discuss approach (GitHub UI: click "Draft" button).

### Multiple Features from One Branch (Not Recommended)
Keep it simple: one branch = one logical change.

If you accidentally mixed features:
```bash
git reset --soft origin/main  # Undo commits but keep changes
# Stage and commit each feature separately
git add <files-for-feature-1>
git commit -m "feat: feature 1"
git add <files-for-feature-2>
git commit -m "feat: feature 2"
git push -f origin feature/your-feature
```

---

## Questions?

- See [CONTRIBUTOR_WORKFLOW.md](CONTRIBUTOR_WORKFLOW.md) for the full step-by-step guide.
- Check GitHub's [branching docs](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository) for more.
