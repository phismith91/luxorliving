# Agent update: Branch protection & GitHub Actions comment failures (2026-01-19)

Summary for automated agents:
- Problem: Workflows used `github.issues.createComment` or `github.issues.addLabels` while running `actions/github-script@v7`; v7 exposes REST calls under `github.rest`, so direct `github.issues.*` was undefined and threw TypeError.
- Permission nuance: Workflows triggered on `pull_request` do not have access to the base repository write context for certain actions; use `pull_request_target` for steps that need to create comments or labels in the base repo. Beware: using `pull_request_target` means you must NOT check out untrusted PR code before performing write actions.
- Operational note: When branch-protection has `enforce_admins: true`, admins cannot bypass required checks; merging fixes may require bringing checks to success or temporarily toggling the setting by a repo admin.

Actions taken & where to look:
- Files changed: `.github/workflows/branch_protection_reminder.yml`, `.github/workflows/qa_matrix_comment_trigger.yml`, `.github/workflows/qa_matrix_report.yml` (use `github.rest.issues.*`).
- Postmortem: `docs/postmortems/2026-01-19-ci-branch-protection-and-shellcheck.md`
- Follow-ups: created `docs/cleanup/cleanup_candidates_2026-01-19.md` and issue #54 to discuss archival/removal of candidates.

Quick checks agents can run:
- Search for occurrences of `github.issues.` and flag to review if present.
- Validate workflows that post comments use `pull_request_target` and ensure no untrusted code is checked out prior to write actions.
- Ensure workflows declare `permissions` with `issues: write` where needed.

