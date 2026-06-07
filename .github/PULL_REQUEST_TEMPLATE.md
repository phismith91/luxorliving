## Summary

<!-- What does this PR do and why? Which component/layer is affected? -->

## Type of Change

- [ ] Bug fix
- [ ] New entity platform or device support
- [ ] LXP parser / entity mapper change
- [ ] Config Flow / Options Flow change
- [ ] REST client / BAOS API change
- [ ] KNX protocol change
- [ ] Refactoring / code quality
- [ ] Documentation / CI

## Checklist

**Required for every PR:**

- [ ] `pre-commit run --all-files` passes (black, isort, flake8, bandit,
      prettier)
- [ ] `python -m pytest tests/ -v -m "not enable_socket"` — all tests pass
- [ ] `./scripts/validate_readme.sh` passes
- [ ] New behavior covered by tests
- [ ] Type hints on all new public functions

**If user-facing change:**

- [ ] `CHANGELOG.md` updated
- [ ] README.md test count updated

**If new device / entity type:**

- [ ] Simulation mode works without hardware
- [ ] LXP parser handles the new type

**If touching BAOS REST API or KNX protocol:**

- [ ] Tested on real hardware (IP1 + HA) — strongly recommended
- [ ] `./scripts/check_release_notes.sh` passes
