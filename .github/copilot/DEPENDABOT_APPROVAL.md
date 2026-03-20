# Dependabot PR Approval Policy

Automatic approval steps have been removed from the Dependabot validation
workflow by design — maintainers must review and approve Dependabot PRs
manually.

How to approve a Dependabot PR

1. Open the pull request on GitHub (Pull requests → select PR).
2. Review the CI job results and the code changes.
3. Click **Review changes** → choose **Approve** and submit the review.

Re-enabling automatic approvals (optional)

- If you want automatic approvals again in the future, we recommend using a
  Fine‑grained token scoped to this repository (or a classic PAT with minimal
  `repo` scope). Add it as the secret `PERSONAL_TOKEN` and reintroduce the
  approval step.
- Note: automatic approvals can be risky; prefer manual review for higher
  assurance.

Security note

- Use the minimal permissions required and set a short expiration date for any
  token. Rotate tokens regularly and never commit them into the repository.
