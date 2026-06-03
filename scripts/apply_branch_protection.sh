#!/usr/bin/env bash
set -euo pipefail

# Apply recommended branch protection to main using gh api
# Usage: ./scripts/apply_branch_protection.sh
# Requires: `gh` CLI, repo admin permissions

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI is required. Install from https://cli.github.com/" >&2
  exit 2
fi

OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)

cat > /tmp/branch_protection_payload.json <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Run Tests",
      "Pre-commit checks",
      "Release Checks"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "require_last_push_approval": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

echo "Applying branch protection to ${OWNER}/${REPO} (branch: main)"
gh api --method PUT -H "Accept: application/vnd.github+json" \
  "/repos/${OWNER}/${REPO}/branches/main/protection" --input /tmp/branch_protection_payload.json

echo "Done. Verify settings in https://github.com/${OWNER}/${REPO}/settings/branches"
