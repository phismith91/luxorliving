# Workflow Overview

Quick visual reference for the entire development and release workflow.

## Contributor Workflow (Simplified View)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LOCAL SETUP (one-time)                                       │
├─────────────────────────────────────────────────────────────────┤
│ • Clone repo                                                    │
│ • Create venv, install deps                                    │
│ • pre-commit install  ← Prevents bad commits                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CREATE BRANCH                                                │
├─────────────────────────────────────────────────────────────────┤
│ git checkout -b feature/your-feature main                       │
│ (Naming: feature/*, bugfix/*, docs/*, chore/*, exp/*)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. WORK LOCALLY                                                 │
├─────────────────────────────────────────────────────────────────┤
│ • Edit files, add tests                                         │
│ • pre-commit run --all-files  ← Local format/lint check        │
│ • pytest tests/ -v            ← Run all tests locally           │
│ • Keep commits small & meaningful                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. PUSH TO BRANCH                                               │
├─────────────────────────────────────────────────────────────────┤
│ git push origin feature/your-feature                            │
│                                                                 │
│ ✓ Push Preflight Workflow Runs (automatic)                     │
│   • black --check                                              │
│   • isort --check-only                                         │
│   • pytest (smoke tests only)                                  │
│   ~ 2–3 min, fails fast on format/lint                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. OPEN PULL REQUEST                                            │
├─────────────────────────────────────────────────────────────────┤
│ • Use PR template                                              │
│ • Describe what & why                                          │
│ • Check off test/doc boxes                                     │
│                                                                 │
│ ✓ Pull Request Fast Checks Run (automatic)                    │
│   • black --check                                              │
│   • isort --check-only                                         │
│   • pytest (smoke tests only)                                  │
│   ~ 2–3 min                                                    │
│                                                                 │
│ ✓ Branch Protection Reminder Posted (info only)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. REVIEW + OPTIONAL FULL TESTS                                 │
├─────────────────────────────────────────────────────────────────┤
│ • Maintainer reviews code                                       │
│ • If significant: Comment "/run-qa-matrix" to trigger full QA  │
│                                                                 │
│ ✓ QA Matrix Runs (on label or manual trigger)                 │
│   • Python 3.11 × Home Assistant 2025.12, 2026.1, latest      │
│   • Python 3.13 × Home Assistant 2025.12, 2026.1, latest      │
│   ~ 10–15 min, comprehensive testing                           │
│                                                                 │
│ • Codecov coverage report posted                               │
│ • PlantUML diagrams rendered (if any)                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. MERGE TO MAIN                                                │
├─────────────────────────────────────────────────────────────────┤
│ • Maintainer clicks "Merge" (only after approvals + checks)    │
│ • Branch deleted (optional, GitHub prompts)                    │
│ • main now has your change, ready for next release            │
└─────────────────────────────────────────────────────────────────┘
```

## Release Workflow (Admin/Maintainer only)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. PREPARE RELEASE                                              │
├─────────────────────────────────────────────────────────────────┤
│ • Ensure main is green (all PRs merged & tests passing)        │
│ • Update manifest.json version (0.6.1 → 0.6.2)               │
│ • Create RELEASE_NOTES_vX.Y.Z.md                              │
│ • Update CHANGELOG.md with new version section                │
│ • Run: pytest tests/ -v (local, ensure pass)                  │
│ • Commit: "Release vX.Y.Z"                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. TAG & PUSH                                                   │
├─────────────────────────────────────────────────────────────────┤
│ git tag -a vX.Y.Z -m "Release vX.Y.Z"                          │
│ GIT_SSH_COMMAND='ssh -F /dev/null' git push origin vX.Y.Z    │
│                                                                 │
│ ✓ Release Checks Run (automatic on main push)                 │
│   • black --check                                              │
│   • isort --check-only                                         │
│   • pytest (smoke + integration subset)                        │
│   • validate_readme.sh                                         │
│   • validate_hacs.sh                                           │
│   • release_automation.sh --dry-run                            │
│   ~ 5–10 min, prevents bad releases                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CREATE GITHUB RELEASE                                        │
├─────────────────────────────────────────────────────────────────┤
│ gh release create vX.Y.Z \                                      │
│   --title "vX.Y.Z - Title" \                                   │
│   --notes-file RELEASE_NOTES_vX.Y.Z.md \                      │
│   --latest                                                      │
│                                                                 │
│ Release published on GitHub; users can download/install       │
└─────────────────────────────────────────────────────────────────┘
```

## CI Check Details

### Push Preflight (feature branch → push)
| Check | Duration | Fails if | Action |
|-------|----------|----------|--------|
| black --check | <1s | Code not formatted | Run `black .` locally |
| isort --check-only | <1s | Imports not sorted | Run `isort .` locally |
| pytest (smoke) | ~30s | Quick tests fail | Fix tests, run locally first |

### Pull Request Fast Checks (PR sync)
| Check | Duration | Fails if | Action |
|-------|----------|----------|--------|
| black --check | <1s | Code not formatted | Run `black .` locally |
| isort --check-only | <1s | Imports not sorted | Run `isort .` locally |
| pytest (smoke) | ~30s | Quick tests fail | Fix tests |

### QA Matrix (on label `run-qa-matrix`)
| Axis | Variants | Duration | Notes |
|------|----------|----------|-------|
| Python | 3.11, 3.13 | Each ~5–10 min | Tests all Python versions |
| HA | 2025.12, 2026.1, latest | Per Python | Tests all HA versions |
| Tests | smoke → integration → full | Parallel per matrix cell | Only fails if truly broken |
| Coverage | Codecov upload | After tests | Tracks coverage history |

### Release Checks (main push at release)
| Check | Purpose | Fails if |
|-------|---------|----------|
| black + isort | Format/lint gate | Code not formatted |
| pytest (smoke + integration subset) | Quick sanity | Tests break |
| validate_readme.sh | README version matches | Version mismatch |
| validate_hacs.sh | HACS compliance | hacs.json or manifest invalid |
| release_automation.sh --dry-run | Release would succeed | Dry-run fails (prevents bad release) |

---

## Labels & When to Use Them

| Label | Used by | Triggers | When |
|-------|---------|----------|------|
| `run-qa-matrix` | Reviewers, Contributors | QA Matrix workflow | PR needs full testing |
| `bug` | Anyone | Routing to backlog | Bug report |
| `enhancement` | Anyone | Routing | Feature request |
| `testing` | Reviewer | Attention signal | Needs test focus |
| `documentation` | Anyone | GitHub automation | Docs-only PR |

---

## Common Questions

**Q: My push preflight failed on format. What do I do?**  
A: Run `black .` and `isort .` locally, commit, and push again. Preflight runs again automatically.

**Q: How long does QA matrix take?**  
A: ~10–15 minutes for the full 6 combinations (2 Python × 3 HA versions).

**Q: Do I need to run tests locally before pushing?**  
A: Yes, strongly recommended. CI should verify, not discover issues. Use: `pytest tests/ -v`

**Q: What's the difference between smoke and integration tests?**  
A: Smoke = quick sanity checks (<30s). Integration = deeper, slower tests. See [docs/TESTS.md](TESTS.md).

**Q: Can I force-push to my feature branch?**  
A: Yes (e.g., after rebasing). Just be careful not to force-push to `main` — it's protected.

**Q: Release workflow seems complex. Can I skip anything?**  
A: No. The Release Checks gate prevents bad releases. Follow the process.

---

For detailed step-by-step, see [CONTRIBUTOR_WORKFLOW.md](CONTRIBUTOR_WORKFLOW.md).