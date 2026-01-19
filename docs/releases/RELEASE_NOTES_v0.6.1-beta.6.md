# ⚠️ LUXORliving v0.6.1-beta.6 (pre-release)

**Release Type:** Beta (pre-release)
**Release Date:** 19. Januar 2026

### 🩹 Fixes
- **CI / Workflows**: Fix posting comments from workflows using `actions/github-script@v7` — use `github.rest.issues.*` and run comment steps on `pull_request_target` when required.
- **ShellCheck**: Quote `gh api` paths in branch-protection scripts to satisfy SC2086.
- **Pre-commit / Formatting**: Apply black/isort formatting fixes discovered by pre-commit hooks.

### 🧪 Testing & Notes
- CI checks pass on the release branch (Pre-commit, Fast checks, CI/CD pipeline).
- This is a pre-release intended for validation of workflow fixes and small operational changes.

---

For full changelog and details see `CHANGELOG.md` and PRs merged around this release.
