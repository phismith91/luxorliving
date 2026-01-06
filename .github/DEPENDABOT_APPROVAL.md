# Dependabot PR Auto-Approval

This project auto-runs a Dependabot PR validation workflow that attempts to auto-approve Dependabot PRs.

If the `juliangruber/approve-pull-request-action@v2` step fails with **"Resource not accessible by integration"** or a similar permission error, follow these steps:

1. Repository Workflow Permissions
   - Go to: Settings → Actions → General → Workflow permissions
   - Ensure **Allow GitHub Actions to create and approve pull requests** (or equivalent) is enabled. This is required for `GITHUB_TOKEN` to create PR reviews.

2. Branch Protection
   - If branch protection rules limit who can approve, adjust them so that approvals from Actions or token-based automation are permitted when needed.

3. Fallback with PAT (optional)
   - If your organization restricts workflow permissions and you still want automatic approvals, create a Personal Access Token (PAT) with `repo` scope and add it as a repository secret named `PERSONAL_TOKEN`.
   - The Dependabot workflow includes a fallback step that will use `PERSONAL_TOKEN` to approve the PR if the primary approve action fails.

4. Security Note
   - Using a PAT is less preferred than enabling Actions permissions because a PAT is a long-lived credential. Use it only when necessary and rotate it regularly.

5. Troubleshooting
   - After changing settings, re-run the Dependabot workflow (Actions → select run → Re-run jobs).
   - Check the workflow logs for the approve step and the fallback step to see whether approval succeeded and which token was used.
