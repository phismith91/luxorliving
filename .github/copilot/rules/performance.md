# Performance Rules

- Avoid blocking I/O in HA event loop: no `time.sleep`/`requests` in async code; use async clients and `asyncio.sleep` sparingly.
- Minimize network chatter to KNX/REST; batch where possible; implement backoff and rate limiting; cache stable metadata safely.
- Keep logging lean at INFO; avoid chatty debug in hot paths; guard noisy logs behind debug flags.
- Prefer incremental updates over full refresh; respect Home Assistant coordinator refresh intervals; avoid tight polling loops.
- Measure before optimizing; when performance changes, note impact and add coverage for regressions.
