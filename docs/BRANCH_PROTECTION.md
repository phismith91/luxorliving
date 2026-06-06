# Branch Protection Ruleset

`main` must be protected by GitHub enforcement, not just contributor convention.

## Required reviews and protections

- Require pull requests before merging
- Require **1 approving review**
- Dismiss stale approvals when new commits are pushed
- Require review from `CODEOWNERS`
- Require approval of the most recent push
- Require conversation resolution before merge
- Require branches to be up to date before merging
- Enforce rules for admins
- Require linear history
- Block force pushes
- Block branch deletion

## Required status checks

The recommended required checks for `main` are:

- `Pre-commit checks`
- `Run Tests`
- `Release Checks`

## Repository automation

- Review the current protection with `./scripts/check_branch_protection.sh`
- Apply the recommended configuration with `./scripts/apply_branch_protection.sh`

The helper script uses the GitHub branch protection API so the same policy can be
applied consistently until an organization-level ruleset replaces it.
