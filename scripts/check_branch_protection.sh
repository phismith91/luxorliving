#!/usr/bin/env bash
set -euo pipefail

# Check current branch protection for main
# Usage: ./scripts/check_branch_protection.sh
# Requires: `gh` CLI

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI is required. Install from https://cli.github.com/" >&2
  exit 2
fi

OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)

echo "Fetching branch protection for ${OWNER}/${REPO}:main"
if gh api /repos/${OWNER}/${REPO}/branches/main/protection -H "Accept: application/vnd.github+json" >/dev/null 2>&1; then
  gh api /repos/${OWNER}/${REPO}/branches/main/protection -H "Accept: application/vnd.github+json" --jq '.'
else
  echo "No branch protection configured or insufficient permissions to view it."
fi
