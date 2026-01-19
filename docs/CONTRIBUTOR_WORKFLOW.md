# Contributor Workflow — Short Guide

Goal: A concise, clear guide for contributors and maintainers.

1) Create a branch (local)
- Follow branch naming rules in `docs/BRANCHING_STRATEGY.md`.
- Examples: `feature/...`, `bugfix/...`, `docs/...`, `chore/...`.

2) Local setup (one-time)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt
pip install -r requirements_style.txt
pre-commit install
```
- Run `pre-commit run --all-files` and fix issues locally.

3) Work & commit
- Write small, focused commits: `feat:`, `fix:`, `docs:`.
- Format: `black . && isort .` or use `pre-commit`.

4) Push & open PR
```bash
git push origin feature/your-branch
# open PR against main and fill the PR template
```
- The PR template should include: short description, testing steps, checklist.

5) Pipelines
- Push/PR run fast checks (preflight/fast checks): `black --check`, `isort --check-only`, smoke tests.
- Full QA Matrix runs only after adding the `run-qa-matrix` label or commenting `/run-qa-matrix`.

6) Review & merge
- At least one approval required (branch protection).
- Merge only when fast checks are green. For large changes, request QA Matrix.

7) Maintainers / Releases
- Maintainers update `manifest.json`, `CHANGELOG.md`, `RELEASE_NOTES.md` before releases.
- Run `./scripts/release_automation.sh --dry-run` before tagging.

Troubleshooting (brief)
- `black --check` / `isort --check-only` failed: run `black .` / `isort .` locally and push the fix.
- Smoke tests failed: run `pytest tests/ -v` locally, fix, and push.

See also: `docs/TESTS.md`, `docs/BRANCHING_STRATEGY.md`.

If anything is unclear, comment on the PR or open an issue.
# Contributor Workflow — Step by Step

This guide is for **anyone** who wants to contribute to LUXORliving — you don't need admin access or special knowledge. Just follow these steps.

## 0. Setup (one-time)

```bash
# Clone the repository
git clone https://github.com/phismith91/luxorliving.git
cd luxorliving

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements_dev.txt
pip install -r requirements_style.txt

# Install pre-commit hooks (prevents bad commits automatically)
pre-commit install
```

## 1. Create a Feature Branch

Use this naming convention for your branch:
- **Feature:** `feature/your-feature-name` (e.g., `feature/add-light-brightness-sync`)
- **Bug fix:** `bugfix/your-bug-name` (e.g., `bugfix/fix-timeout-on-reboot`)
- **Documentation:** `docs/your-doc-name` (e.g., `docs/update-installation-guide`)
- **Chore:** `chore/your-task-name` (e.g., `chore/upgrade-pytest`)

```bash
git checkout -b feature/your-feature-name main
```

## 2. Work Locally

### Make your changes
- Edit files, add tests, update docs.
- Keep commits small and meaningful.

### Run pre-commit checks locally
```bash
# Format your code (black, isort, etc.)
pre-commit run --all-files

# Or just run the formatters:
black .
isort .
```

### Run tests locally
```bash
python -m pytest tests/ -v

# Or just smoke tests (fast):
python -m pytest tests/ -q -m "smoke and not enable_socket"
```

**Important:** All tests must pass before you push. If a test fails, fix it — don't skip it.

## 3. Push to Your Branch

```bash
git add .
git commit -m "feat: add your feature"  # Use conventional commits if possible
git push origin feature/your-feature-name
```

### What happens now?
- **Preflight checks run** (push_preflight workflow):
  - `black --check` (formatting)
  - `isort --check-only` (import sorting)
  - Smoke tests (quick sanity checks)
  - This takes ~2–3 minutes and gives you fast feedback.

Check the status in the GitHub Actions tab or in your terminal.

## 4. Open a Pull Request (PR)

Go to https://github.com/phismith91/luxorliving and click **Compare & pull request**.

### Fill in the PR template
Your PR should include:
- **Title:** Short, descriptive (e.g., "feat: add light brightness sync")
- **Description:** 
  - What does this change?
  - Why is it needed?
  - Any testing you did locally?
- **Checklist:** Mark what applies (tests, docs, etc.)

### What happens now?
- **Fast checks run** (pull_request_fast_checks workflow):
  - `black --check` again
  - `isort --check-only` again
  - Smoke tests again
  - This takes ~2–3 minutes.
  - If it fails, see [Troubleshooting](#troubleshooting) below.

- **A reminder comment** is posted about branch protection (you can ignore this; it's for repo admins).

## 5. Wait for Reviews

A maintainer will review your PR. They might ask for changes or approve it.

### If they ask for changes:
1. Make the changes locally
2. Commit and push again: `git push origin feature/your-feature-name`
3. Fast checks run automatically — no need to do anything.

## 6. (Optional) Request Full QA Matrix

If your change is significant or if a maintainer asks, you can trigger the full QA Matrix (Python 3.11/3.13 × Home Assistant 2025.12/2026.1/latest) by:

**Option A:** Comment on the PR:
```
/run-qa-matrix
```

**Option B:** Add the `run-qa-matrix` label to the PR.

Then the full matrix will run (takes ~10–15 min).

## 7. Merge

Once approved and all checks pass, a maintainer merges your PR to `main`.

---

## Troubleshooting

### "black --check failed"
Your code formatting doesn't match the project style.

**Fix locally:**
```bash
black .
git add .
git commit -m "style: format with black"
git push origin feature/your-feature-name
```

### "isort --check-only failed"
Your imports are not sorted correctly.

**Fix locally:**
```bash
isort .
git add .
git commit -m "style: sort imports with isort"
git push origin feature/your-feature-name
```

### "Smoke tests failed"
One or more tests don't pass.

**Check which test failed:**
```bash
python -m pytest tests/ -v
```

**Fix the test or code, then:**
```bash
python -m pytest tests/ -v  # Verify all pass
git add .
git commit -m "fix: make tests pass"
git push origin feature/your-feature-name
```

### "pre-commit run --all-files fails locally but my IDE says things are fine"
Your IDE might have different settings than the project. Trust pre-commit — it's configured to match the CI checks.

```bash
pre-commit run --all-files  # Always run this before pushing
```

---

## Questions?

- Check [BRANCHING_STRATEGY.md](BRANCHING_STRATEGY.md) for branch naming details.
- See [docs/TESTS.md](TESTS.md) for detailed testing guidance.
- Open an issue if something is unclear.