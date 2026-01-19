# Post‑Mortem: Branch Protection + ShellCheck / Commenting failures (2026-01-19)

## Kurzüberblick

- Incident: Branch Protection Reminder workflow failed with TypeError reading
  `createComment` and later with 403 `Resource not accessible by integration`
  when attempting to post comments to PRs.
- Impact: Reminder comments were not posted for PRs; workflows that expected to
  add labels/comments were failing on relevant PR events.
- Timeframe: 2026-01-19 (local timezone)

## Timeline / Actions

1. Initial failure observed in run 60803095480: TypeError: Cannot read
   properties of undefined (reading 'createComment').
2. Investigation: `actions/github-script@v7` changed API surface — REST
   endpoints are under `github.rest` not `github` top-level.
3. Quick fixes:
   - Changed `github.issues.createComment` → `github.rest.issues.createComment`
     in `.github/workflows/branch_protection_reminder.yml`.
   - Identified additional occurrences in `qa_matrix_comment_trigger.yml` —
     changed `github.issues.*` → `github.rest.issues.*` (addLabels,
     createComment).
4. Re‑run revealed `HttpError: Resource not accessible by integration` (403)
   when attempting to post comment — caused by the workflow running under
   `pull_request` and not having proper repo context for commenting.
5. Fix: Changed event to `pull_request_target` so the step runs in the context
   of the base repository with write permission to post comments.
6. The PR could not be merged due to branch protection `enforce_admins: true`
   (required checks). Created `fix/shellcheck-quote` branch, iterated fixes, and
   pushed formatting commits.
7. Temporary steps: Disabled `enforce_admins` briefly (via branch-protection
   API) to allow an admin to merge PR #53 after all checks passed; re-enabled it
   immediately after merge.

## Root Causes

- API mismatch: `actions/github-script@v7` exposes REST APIs under `github.rest`
  — relying on `github.issues.*` caused runtime TypeError.
- Permissions/context: Running on `pull_request` prevented the action from using
  the base repo token to create comments in some cases (403).
  `pull_request_target` is required for workflows that need to act as the base
  repository.
- Branch protection blocked admin merges until checks passed; merging required
  coordination (or temporary admin override).

## Learnings

- Always verify `actions/github-script` API surface for the version used; prefer
  `github.rest.*` for REST calls.
- Use `pull_request_target` for actions that must post comments, add labels, or
  change PR state — but be mindful of security implications (do not check out
  untrusted code when using this event).
- Keep a small, focused PR for infra/workflow fixes and ensure pre-commit hooks
  are applied before opening PR (pre-commit hooks can modify files and cause CI
  to fail on formatting).
- Document branch-protection procedures and have a clear owner who can perform a
  temporary admin override if absolutely necessary.

## Next steps

- Add the above to `docs/postmortems/` and link to relevant PRs (#53) and runs.
- Search repo for other usages of `github.issues` and update to
  `github.rest.issues` where required.
- Add a short CI test or workflow lint step to detect common
  `actions/github-script` misuse (optional).

## Artifacts & Failure Details

- First failing run: 21143448300 (job 60803095480) — TypeError: Cannot read
  properties of undefined (reading 'createComment').
- Subsequent run: 21143690418 — 403 HttpError: Resource not accessible by
  integration when calling POST /repos/.../issues/53/comments
- Relevant PR: #53 (fix/shellcheck-quote) — contained the following commits:
  - 5aa9a53: ci(shellcheck): quote gh api paths to satisfy SC2086
  - 98d0c5d: ci(workflows): use github.rest.issues API in github-script v7 steps
  - a8e8a0b: ci(workflows): use pull_request_target for comment step to allow
    posting comments
- Pre-commit formatting changed `tests/conftest.py` (black) causing pre-commit
  checks to fail until the formatting commit was pushed.
- Branch-protection: `enforce_admins: true` blocked an immediate admin merge
  until checks were green; a temporary toggle was used to allow merging the fix
  after validation.

## References

- PR #53 — fixes for ShellCheck and workflows
- Run IDs: 21143448300, 21143690418, 21143842733
- Logs: `branch_protection_reminder` run logs (see GitHub Actions)

## Contributors

- Phil Esprimo (phismith91) — investigation, fixes, merge
