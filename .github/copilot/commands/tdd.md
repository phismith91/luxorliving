# /tdd

Invoke the tdd-guide agent to enforce test-first workflow.

Steps:

1. Define behavior and fixtures; write failing pytest covering happy path +
   edge.
2. Implement minimal code to pass; keep async/await correct; no blocking calls.
3. Re-run tests, refactor, ensure coverage targets met; run black/isort.
