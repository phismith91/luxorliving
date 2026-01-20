# Coding Standards (HA/Python)

- Formatting: black (line length 100), isort profile=black; keep imports minimal and ordered.
- Type hints required; prefer `from __future__ import annotations`; use Protocols/TypedDicts for structured data.
- Async rules: no `asyncio.run` or `time.sleep` in HA code; use HA helpers/coordinators; await I/O; avoid blocking calls.
- Entities: stable `unique_id`, `_attr_*` usage, device_info populated, services validated, diagnostics scrub secrets.
- Logging: concise, no secrets or URLs with tokens; guard noisy logs; use `LOGGER.debug` sparingly in hot paths.
- Errors: handle KNX/REST failures with backoff and clear messages; avoid broad except; re-raise when needed.
