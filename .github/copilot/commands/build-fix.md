# /build-fix

Use the build-error-resolver agent to fix failing tests/lints.

Steps:

1. Capture exact error output (pytest, lint, type checks).
2. Apply minimal fix; avoid refactors; prefer smallest change.
3. Re-run targeted tests; report root cause and verification commands.
