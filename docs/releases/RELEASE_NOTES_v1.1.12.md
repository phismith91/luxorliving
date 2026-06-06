# Release Notes — v1.1.12

## Fixed

- **KNX bus freeze after ~47 h — race condition between session refresh and
  reconnect handler (issue #141)**: The `_session_refresh_loop` calls `logout()`
  which causes xknx to detect a disconnect and fire `_async_on_reconnect`
  *concurrently*. Without synchronization both coroutines executed
  `logout → login → enable_tunneling` in parallel, creating 2+ orphaned sessions
  per refresh cycle instead of 1. After ~7 cycles the IP1 session table overflowed
  and the KNX bus froze (confirmed by user log showing L_DATA_CON timeouts on all
  group addresses).

  Fix: `asyncio.Lock` (`_session_lock`) shared by both coroutines. The reconnect
  handler skips execution immediately if the refresh loop holds the lock; otherwise
  it acquires the lock before any REST session operation. This guarantees only one
  session is active at a time.

- **Session refresh interval reduced 6 h → 4 h** for a wider safety margin against
  IP1 session table saturation.

- **Lingering `_session_refresh_task` in tests**: Two gateway tests that called
  `async_setup()` without a matching `async_disconnect()` left a background task
  running, causing pytest-asyncio ≥ 1.3 to raise `Failed: Lingering task after test`.

## Tests

5 new regression tests for the session lock race condition. Test count: 789 → 794.
