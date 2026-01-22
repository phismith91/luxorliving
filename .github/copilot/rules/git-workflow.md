# Git Workflow Rules

- Conventional commits only: feat, fix, refactor, docs, test, chore, ci, perf;
  no direct pushes to main.
- Always branch from main, keep branches focused, rebase onto main before PR;
  delete merged branches.
- PR checklist: plan first, update docs/CHANGELOG if user-facing, run pytest +
  lint + format, include test plan in description.
- Keep diffs minimal and scoped; avoid drive-by refactors; prefer multiple small
  PRs over one large.
- No secrets in commits; review `git diff --cached` before commit; use
  `GIT_SSH_COMMAND='ssh -F /dev/null'` for pushes.
