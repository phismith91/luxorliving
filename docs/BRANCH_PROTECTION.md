# Branch Protection — Recommended settings for `main`

This document contains recommended branch protection settings for the `main`
branch and example `gh api` payloads an admin can use to apply them.

> Note: Applying branch protection requires repo admin permissions.

## Goals

- Prevent accidental merges that would bypass checks
- Enforce quick, reliable CI checks before merge
- Keep history clean and auditable

## Recommended minimal settings

- Require pull request reviews before merging (1 approval)
- Require status checks to pass (fast checks) — fail fast on formatting/linting
- Require branches to be up to date before merging (enforce merging/rebasing)
- Enforce linear history
- Disable force-pushes and branch deletions
- Include administrators (optional but recommended)

### Example status checks to require

Pick the checks that give fast, meaningful feedback:

- `Pull Request — Fast checks` (our fast PR workflow)
- `Pre-commit checks` (pre-commit CI workflow)
- `Push — Preflight checks` (for pushed branches)

If you want to be stricter, add:

- `Release Checks` (optional — run on merges to `main` for release readiness)

> Tip: The exact `context` names used by GitHub for required checks are
> displayed in the checks UI after the workflow runs once. Use those exact
> strings in the payload below.

## Example payload (gh api)

Below is an example `gh api` call to set branch protection for `main`. Replace
the `contexts` array with the exact check names you want to require.

```bash
cat <<'JSON' > /tmp/branch-protection.json
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Pull Request — Fast checks",
      "Pre-commit checks",
      "Push — Preflight checks"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

# Apply (requires repo admin):
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/{owner}/{repo}/branches/main/protection \
  --input /tmp/branch-protection.json
```

## Delegate or step-by-step

1. An admin runs the `gh api` command above (replace `{owner}/{repo}`).
2. Verify required checks appear in Branch protection settings and adjust
   contexts if names differ.
3. Optionally enable more strict settings (e.g.,
   `required_approving_review_count: 2`, code owners reviews).

## Notes

- If a status check name does not match exactly, GitHub will reject it — use the
  UI to find the exact check name after workflows run once.
- If you add `Release Checks` as required, ensure it can run reliably on merges
  to `main` (it may require additional permissions or secrets).

---

If you'd like, I can prepare a short PR that suggests these default settings and
the `gh api` payload for an admin to run. Would you like me to create that PR
now?
