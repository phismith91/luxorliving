# Release Notes — v1.1.11

## Fixed

- **KNX bus freeze after 24–72 h uptime — complete fix (issue #141)**: The
  reactive reconnect handler from v1.1.10 only recovered *after* xknx detected
  a transport-layer disconnect. This left the "silent freeze" scenario unaddressed:
  the IP1's internal session/channel table fills up over time until the KNX bus
  stops routing telegrams while the KNX/IP connection itself stays open and xknx
  never detects a problem.

  Two-layer protection is now in place:

  - **Proactive** — `_session_refresh_loop` runs as a background task and cycles
    the REST session every 6 h (logout → login → enable_tunneling). This flushes
    stale session-table entries before saturation, preventing the freeze entirely.
    The 6 h interval is well below the ~7 h onset observed in production logs.
  - **Reactive** (unchanged from v1.1.10) — `_on_connection_state_changed` fires
    when xknx detects a disconnect and immediately re-authenticates.

  The refresh task is started after a successful tunneling setup and is cancelled
  cleanly during integration unload (`async_disconnect`).

- **Blocking file read in event loop** (`overrides.py`): `load_overrides()` was
  called synchronously in the async HA setup path, triggering HA's
  "Detected blocking call to `open()`" warning on every startup. The call is now
  dispatched via `hass.async_add_executor_job` so the file I/O runs in the
  executor thread pool without blocking the event loop.

## Changed

- **Test coverage**: 6 new tests in `TestSessionRefreshLoop` cover the full
  refresh cycle, missing REST client guard, simulation mode guard, exception
  resilience (loop continues after REST failure), task cancellation on disconnect,
  and None-safe teardown. Test count: 783 → 789.
