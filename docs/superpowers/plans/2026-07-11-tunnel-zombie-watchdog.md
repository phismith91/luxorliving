# Tunnel Zombie Watchdog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect a "zombie" KNX tunnel — xknx reports `CONNECTED` but every outgoing telegram fails its `L_DATA_CON` confirmation for an extended period — and force a full gateway reconnect (REST + KNX) instead of waiting for xknx's own heartbeat/disconnect detection, which real-world logs show can take 9+ hours to notice.

**Architecture:** A new periodic task (`_zombie_watchdog_loop`, 30s cadence) polls xknx's built-in `connection_manager.cemi_count_outgoing_error` counter — incremented by the xknx library itself on every `ConfirmationError` (the exact condition logged as `"L_DATA_CON Data Link Layer confirmation timed out"` in `xknx.log`). If the counter jumps by more than a threshold within one check window, the watchdog schedules `_async_zombie_recover()`, which calls the gateway's existing `async_disconnect()` + `async_setup()` — the same full REST+KNX reconnect a user is currently told to do manually. A cooldown prevents reconnect storms if the underlying bus stays down.

**Why polling a counter instead of a logging handler:** xknx already counts every `ConfirmationError` on `xknx.connection_manager.cemi_count_outgoing_error` (see `xknx/cemi/cemi_handler.py:84,91` and `xknx/core/connection_manager.py:26-27,44-45` in the installed `xknx==3.15.0` package). Reading a public int attribute is simpler and more robust than attaching a `logging.Handler` to `xknx.log` and pattern-matching warning text — no string coupling to a message xknx could reword any time, and no separate handler lifecycle to register/unregister.

**Tech Stack:** Python 3.13, asyncio, existing `LuxorKNXGateway` class in `custom_components/luxor_living/knx_gateway.py`, pytest + pytest-asyncio, xknx 3.15.0.

**Context this plan assumes:** Marcus' 2026-07-10 log (`docs/home-assistant_2026-07-10T08-25-13.061Z.log`) shows ~20 `L_DATA_CON confirmation timed out` warnings per minute for ~9 hours (00:27–09:23), with the already-deployed periodic REST-session-flush fix (`_async_forced_refresh`, PR #180) active throughout and not stopping it — because that fix only cycles the REST/tunneling-slot layer, never the xknx tunnel object itself. This plan is the follow-up: force the actual xknx-level reconnect when this specific symptom recurs.

---

## File Structure

- **Modify `custom_components/luxor_living/const.py`**: add 3 new constants (`ZOMBIE_CHECK_INTERVAL`, `ZOMBIE_ERROR_THRESHOLD`, `ZOMBIE_RECONNECT_COOLDOWN`), next to the existing `RECONNECT_*` constants.
- **Modify `custom_components/luxor_living/knx_gateway.py`**: 3 new instance fields in `__init__`, 2 new methods (`_zombie_watchdog_loop`, `_async_zombie_recover`), task start wired into `async_setup()` (mirrors `_session_refresh_task`), task cancel wired into `async_disconnect()` (mirrors `_session_refresh_task` teardown).
- **Modify `tests/test_knx_gateway.py`**: new `TestZombieWatchdog` class, mirroring the existing `TestSessionRefreshLoop` class's fixture/mocking style (same file, same patterns, so no new test infrastructure needed).

No new files. This is a small, self-contained addition to an existing class — does not warrant splitting `knx_gateway.py`.

---

### Task 1: Add watchdog constants

**Files:**
- Modify: `custom_components/luxor_living/const.py:27-29`

- [ ] **Step 1: Add the constants**

Insert after line 29 (`RECONNECT_COOLDOWN_SECS = 30 ...`):

```python
ZOMBIE_CHECK_INTERVAL = 30  # seconds between cemi_count_outgoing_error polls
ZOMBIE_ERROR_THRESHOLD = 5  # new L_DATA_CON confirmation failures per check interval to declare zombie tunnel
ZOMBIE_RECONNECT_COOLDOWN = 300  # seconds to wait after a zombie-triggered reconnect before arming again
```

- [ ] **Step 2: Commit**

```bash
cd "/home/philipp/projects/luxorliving  (public + maintance)"
git add custom_components/luxor_living/const.py
git commit -m "feat: add zombie-tunnel watchdog constants"
```

---

### Task 2: Add gateway state fields

**Files:**
- Modify: `custom_components/luxor_living/knx_gateway.py:83-88` (inside `__init__`, right after the existing `_session_refresh_task`/`_reconnect_failures` fields)
- Test: `tests/test_knx_gateway.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_knx_gateway.py`, inside `class TestLuxorKNXGateway` (after `test_init_routing_mode`, ~line 90):

```python
    def test_init_zombie_watchdog_state(self, mock_hass):
        """New zombie-watchdog fields must start unarmed/zeroed."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
        )

        assert gateway._zombie_watchdog_task is None
        assert gateway._last_cemi_error_count == 0
        assert gateway._last_zombie_reconnect_at == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_knx_gateway.py::TestLuxorKNXGateway::test_init_zombie_watchdog_state -v`
Expected: FAIL with `AttributeError: 'LuxorKNXGateway' object has no attribute '_zombie_watchdog_task'`

- [ ] **Step 3: Implement**

In `custom_components/luxor_living/knx_gateway.py`, add after line 88 (`self._last_not_connected_log_at: float = 0.0 ...`):

```python
        self._zombie_watchdog_task: asyncio.Task | None = None
        self._last_cemi_error_count: int = 0  # cemi_count_outgoing_error at last watchdog check
        self._last_zombie_reconnect_at: float = 0.0  # monotonic time of last zombie-triggered reconnect
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_knx_gateway.py::TestLuxorKNXGateway::test_init_zombie_watchdog_state -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd "/home/philipp/projects/luxorliving  (public + maintance)"
git add custom_components/luxor_living/knx_gateway.py tests/test_knx_gateway.py
git commit -m "feat: add zombie-watchdog state fields to LuxorKNXGateway"
```

---

### Task 3: Implement `_zombie_watchdog_loop` — no-op below threshold

**Files:**
- Modify: `custom_components/luxor_living/knx_gateway.py` (new method, place directly after `_async_forced_refresh`, i.e. after the method ending at the current line 397 — search for `async def _on_connection_state_changed` and insert the new methods immediately before it)
- Test: `tests/test_knx_gateway.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_knx_gateway.py`, new class after `class TestSessionRefreshLoop` (after its last method, before `class TestSessionLockRaceCondition`, ~line 858):

```python
class TestZombieWatchdog:
    """Tests for the zombie-tunnel watchdog (_zombie_watchdog_loop)."""

    def _make_gateway(self, mock_hass, *, simulation_mode: bool = False) -> LuxorKNXGateway:
        return LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=simulation_mode,
        )

    def _controlled_sleep(self, sleep_calls: list[int], stop_after: int = 2):
        async def _sleep(interval: int) -> None:
            sleep_calls.append(interval)
            if len(sleep_calls) >= stop_after:
                raise asyncio.CancelledError

        return _sleep

    @pytest.mark.asyncio
    async def test_watchdog_noop_below_threshold(self, mock_hass):
        """Error count increasing by less than the threshold must not reconnect."""
        from custom_components.luxor_living.const import ZOMBIE_ERROR_THRESHOLD

        gateway = self._make_gateway(mock_hass)
        mock_xknx = MagicMock()
        mock_xknx.connection_manager.cemi_count_outgoing_error = ZOMBIE_ERROR_THRESHOLD - 1
        gateway._xknx = mock_xknx

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_watchdog_skips_without_xknx(self, mock_hass):
        """Loop must not crash and must skip the check when _xknx is None."""
        gateway = self._make_gateway(mock_hass)
        gateway._xknx = None

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_watchdog_skips_in_simulation_mode(self, mock_hass):
        """Loop must not act on the counter in simulation mode."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)
        mock_xknx = MagicMock()
        mock_xknx.connection_manager.cemi_count_outgoing_error = 999
        gateway._xknx = mock_xknx

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_knx_gateway.py::TestZombieWatchdog -v`
Expected: FAIL with `AttributeError: 'LuxorKNXGateway' object has no attribute '_zombie_watchdog_loop'`

- [ ] **Step 3: Implement the method**

In `custom_components/luxor_living/knx_gateway.py`, add this new method immediately before `def _on_connection_state_changed` (currently starting at line 399 — insert before it):

```python
    async def _zombie_watchdog_loop(self) -> None:
        """Detect a 'zombie' tunnel and force a full reconnect.

        xknx can report CONNECTED for hours while every outgoing telegram
        fails its L_DATA_CON confirmation — the IP1/bus stops acking without
        xknx's own heartbeat ever detecting a real disconnect (confirmed on
        Marcus' 2026-07-10 log: ~20 confirmation timeouts/min for 9h, with
        the periodic REST-session flush from #180 active throughout and not
        stopping it, since that fix only cycles REST auth, never the xknx
        tunnel object).

        Polls xknx's own cemi_count_outgoing_error counter — incremented on
        every ConfirmationError — instead of parsing xknx.log warning text.
        """
        try:
            while True:
                await asyncio.sleep(ZOMBIE_CHECK_INTERVAL)
                if not self._xknx or self.simulation_mode:
                    continue
                error_count = self._xknx.connection_manager.cemi_count_outgoing_error
                delta = error_count - self._last_cemi_error_count
                self._last_cemi_error_count = error_count
                if delta < ZOMBIE_ERROR_THRESHOLD:
                    continue
                now = time.monotonic()
                if now - self._last_zombie_reconnect_at < ZOMBIE_RECONNECT_COOLDOWN:
                    continue
                self._last_zombie_reconnect_at = now
                _LOGGER.warning(
                    "KNX gateway %s:%s zombie tunnel detected — %d confirmation "
                    "failures in %ds with no disconnect event, forcing full reconnect",
                    self.host,
                    self.port,
                    delta,
                    ZOMBIE_CHECK_INTERVAL,
                )
                self.hass.async_create_task(self._async_zombie_recover())
        except asyncio.CancelledError:
            _LOGGER.debug("Zombie watchdog loop cancelled")
            raise
```

Add the new constants to the existing `from .const import (...)` block near the top of the file (currently lines 25-31):

```python
from .const import (
    NOT_CONNECTED_LOG_INTERVAL,
    RECONNECT_COOLDOWN_SECS,
    RECONNECT_FAILURE_THRESHOLD,
    RECONNECT_FAILURE_WINDOW,
    SESSION_REFRESH_INTERVAL,
    ZOMBIE_CHECK_INTERVAL,
    ZOMBIE_ERROR_THRESHOLD,
    ZOMBIE_RECONNECT_COOLDOWN,
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_knx_gateway.py::TestZombieWatchdog -v`
Expected: PASS (3 tests) — note `test_watchdog_noop_below_threshold` and `test_watchdog_skips_in_simulation_mode` currently reference `_async_zombie_recover`, which doesn't exist yet; that's fine because both assert it's *not* called, so `AttributeError` won't be hit (the method reference only needs to exist for the *positive* trigger test in Task 4).

- [ ] **Step 5: Commit**

```bash
cd "/home/philipp/projects/luxorliving  (public + maintance)"
git add custom_components/luxor_living/knx_gateway.py tests/test_knx_gateway.py
git commit -m "feat: add zombie-tunnel detection loop (no-op below threshold)"
```

---

### Task 4: Threshold breach triggers recovery, cooldown prevents re-trigger

**Files:**
- Modify: `custom_components/luxor_living/knx_gateway.py` (new `_async_zombie_recover` method)
- Test: `tests/test_knx_gateway.py`

- [ ] **Step 1: Write the failing tests**

Add to `class TestZombieWatchdog` in `tests/test_knx_gateway.py`, after `test_watchdog_skips_in_simulation_mode`:

```python
    @pytest.mark.asyncio
    async def test_watchdog_triggers_recovery_above_threshold(self, mock_hass):
        """Error count jumping by >= threshold must schedule _async_zombie_recover."""
        from custom_components.luxor_living.const import ZOMBIE_ERROR_THRESHOLD

        gateway = self._make_gateway(mock_hass)
        mock_xknx = MagicMock()
        mock_xknx.connection_manager.cemi_count_outgoing_error = ZOMBIE_ERROR_THRESHOLD
        gateway._xknx = mock_xknx

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_called_once()
        # Coroutine objects expose __name__ == the method name; close it to
        # avoid a "never awaited" warning since we don't run the event loop here.
        scheduled_coro = mock_hass.async_create_task.call_args[0][0]
        assert scheduled_coro.__name__ == "_async_zombie_recover"
        scheduled_coro.close()

    @pytest.mark.asyncio
    async def test_watchdog_respects_cooldown(self, mock_hass):
        """A second breach within ZOMBIE_RECONNECT_COOLDOWN must not re-trigger."""
        from custom_components.luxor_living.const import ZOMBIE_ERROR_THRESHOLD

        gateway = self._make_gateway(mock_hass)
        gateway._last_zombie_reconnect_at = time.monotonic()  # just fired
        mock_xknx = MagicMock()
        mock_xknx.connection_manager.cemi_count_outgoing_error = ZOMBIE_ERROR_THRESHOLD
        gateway._xknx = mock_xknx

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_zombie_recover_calls_disconnect_then_setup(self, mock_hass):
        """Recovery must fully disconnect, then run setup again, in order."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)
        call_order: list[str] = []

        async def _fake_disconnect():
            call_order.append("disconnect")

        async def _fake_setup():
            call_order.append("setup")
            return True

        gateway.async_disconnect = _fake_disconnect
        gateway.async_setup = _fake_setup

        await gateway._async_zombie_recover()

        assert call_order == ["disconnect", "setup"]

    @pytest.mark.asyncio
    async def test_async_zombie_recover_swallows_exceptions(self, mock_hass):
        """A failure during recovery must be logged, not raised (fire-and-forget task)."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)

        async def _boom():
            raise RuntimeError("gateway unreachable")

        gateway.async_disconnect = _boom

        await gateway._async_zombie_recover()  # must not raise
```

Add `import time` usage — `time` is already imported at the top of `test_knx_gateway.py`? Check first:

```bash
grep -n "^import time" tests/test_knx_gateway.py
```

If missing, add `import time` to the imports at the top of `tests/test_knx_gateway.py` (alongside the existing `import asyncio`).

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_knx_gateway.py::TestZombieWatchdog -v`
Expected: `test_watchdog_triggers_recovery_above_threshold` and the two `_async_zombie_recover` tests FAIL with `AttributeError: 'LuxorKNXGateway' object has no attribute '_async_zombie_recover'`. `test_watchdog_respects_cooldown` should already PASS (cooldown logic doesn't need the new method to correctly not-trigger) — if it fails instead, re-check the cooldown branch placement from Task 3.

- [ ] **Step 3: Implement `_async_zombie_recover`**

Add immediately after `_zombie_watchdog_loop` (same insertion point as Task 3, still before `_on_connection_state_changed`):

```python
    async def _async_zombie_recover(self) -> None:
        """Force a full REST+KNX reconnect after zombie-tunnel detection.

        Fire-and-forget task (scheduled via hass.async_create_task): never
        let the exception escape unhandled, matching _async_forced_refresh.
        """
        try:
            await self.async_disconnect()
            await self.async_setup()
            _LOGGER.warning(
                "Zombie-tunnel recovery complete (host=%s)", self.host
            )
        except Exception as err:
            _LOGGER.error(
                "Zombie-tunnel recovery failed (host=%s): %s", self.host, err
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_knx_gateway.py::TestZombieWatchdog -v`
Expected: PASS (7 tests total in the class)

- [ ] **Step 5: Commit**

```bash
cd "/home/philipp/projects/luxorliving  (public + maintance)"
git add custom_components/luxor_living/knx_gateway.py tests/test_knx_gateway.py
git commit -m "feat: trigger full reconnect on zombie-tunnel detection, with cooldown"
```

---

### Task 5: Wire the watchdog task into `async_setup()` / `async_disconnect()`

**Files:**
- Modify: `custom_components/luxor_living/knx_gateway.py:221-228` (start, mirrors `_session_refresh_task` block)
- Modify: `custom_components/luxor_living/knx_gateway.py:289-296` (cancel, mirrors `_session_refresh_task` teardown)
- Test: `tests/test_knx_gateway.py`

- [ ] **Step 1: Write the failing tests**

Add to `class TestZombieWatchdog`:

```python
    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.BAOSRestClient")
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    async def test_watchdog_task_started_on_setup_tunneling(
        self, mock_xknx_class, mock_rest_class, mock_hass
    ):
        """async_setup() must start the zombie watchdog task for tunneling mode.

        Mirrors the mock shape of test_async_setup_with_rest_auth (same file,
        TestLuxorKNXGateway class) — AsyncMock XKNX/BAOSRestClient so a real
        tunneling async_setup() completes without touching the network.
        """
        mock_rest_client = AsyncMock()
        mock_rest_client.login = AsyncMock(return_value="test_token")
        mock_rest_client.enable_tunneling = AsyncMock(return_value=True)
        mock_rest_client.logout = AsyncMock()
        mock_rest_client.__aexit__ = AsyncMock()
        mock_rest_class.return_value = mock_rest_client

        mock_xknx = AsyncMock()
        mock_xknx.start = AsyncMock()
        mock_xknx.stop = AsyncMock()
        mock_xknx.telegram_queue.register_telegram_received_cb = MagicMock()
        mock_xknx.connection_manager.register_connection_state_changed_cb = MagicMock(
            return_value=MagicMock()
        )
        mock_xknx.connection_manager.cemi_count_outgoing_error = 0
        mock_xknx_class.return_value = mock_xknx

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            connection_type="tunneling",
            simulation_mode=False,
        )

        await gateway.async_setup()

        assert gateway._zombie_watchdog_task is not None
        assert not gateway._zombie_watchdog_task.done()

        # Teardown: cancel both background tasks so no lingering tasks remain
        await gateway.async_disconnect()

    @pytest.mark.asyncio
    async def test_watchdog_task_cancelled_on_disconnect(self, mock_hass):
        """async_disconnect() must cancel a running zombie watchdog task."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)
        await gateway.async_setup()

        async def _never_ending():
            await asyncio.sleep(99999)

        task = asyncio.create_task(_never_ending())
        gateway._zombie_watchdog_task = task

        await gateway.async_disconnect()

        assert task.cancelled()
        assert gateway._zombie_watchdog_task is None

    @pytest.mark.asyncio
    async def test_watchdog_task_none_safe_on_disconnect(self, mock_hass):
        """async_disconnect() must not raise when _zombie_watchdog_task is None."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)
        await gateway.async_setup()
        gateway._zombie_watchdog_task = None

        await gateway.async_disconnect()  # must not raise
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_knx_gateway.py::TestZombieWatchdog -v`
Expected: `test_watchdog_task_cancelled_on_disconnect` and `test_watchdog_task_none_safe_on_disconnect` PASS already if `_zombie_watchdog_task` teardown code doesn't exist yet? No — they will FAIL or the cancel-check will trivially pass without proving anything, because `async_disconnect()` doesn't reference `_zombie_watchdog_task` yet. Confirm real failure by checking `gateway._zombie_watchdog_task is None` after disconnect — if the field is simply never touched, the manually-planted task in `test_watchdog_task_cancelled_on_disconnect` stays uncancelled: `assert task.cancelled()` FAILS. Good, that's the real failing assertion.

- [ ] **Step 3: Implement wiring**

In `async_setup()`, inside `_setup_knx_connection`, right after the existing `_session_refresh_task` block (currently lines 221-228), add:

```python
                self._last_cemi_error_count = (
                    self._xknx.connection_manager.cemi_count_outgoing_error
                )
                self._zombie_watchdog_task = asyncio.create_task(
                    self._zombie_watchdog_loop(),
                    name="luxor_zombie_watchdog",
                )
                _LOGGER.debug(
                    "Zombie watchdog started (check interval %ds, threshold %d)",
                    ZOMBIE_CHECK_INTERVAL,
                    ZOMBIE_ERROR_THRESHOLD,
                )
```

This must stay inside the existing `if self._connection_type == ConnectionType.TUNNELING:` block, right after the `_LOGGER.debug("Session refresh loop started ...")` line.

In `async_disconnect()`, right after the existing session-refresh-task cancellation block (currently lines 289-296, ending `self._session_refresh_task = None`), add:

```python
        # Cancel zombie watchdog loop
        if self._zombie_watchdog_task and not self._zombie_watchdog_task.done():
            self._zombie_watchdog_task.cancel()
            try:
                await self._zombie_watchdog_task
            except asyncio.CancelledError:
                pass
        self._zombie_watchdog_task = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_knx_gateway.py::TestZombieWatchdog -v`
Expected: PASS (10 tests total in the class)

- [ ] **Step 5: Commit**

```bash
cd "/home/philipp/projects/luxorliving  (public + maintance)"
git add custom_components/luxor_living/knx_gateway.py tests/test_knx_gateway.py
git commit -m "feat: start/stop zombie watchdog task with the gateway lifecycle"
```

---

### Task 6: Full verification and changelog

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Run the full test suite**

Run: `python3 -m pytest tests/ -m "not enable_socket" --ignore=tests/test_performance.py --ignore=tests/test_lxp_integration.py -q`
Expected: all tests pass (939 + ~13 new = ~952), 0 failures.

- [ ] **Step 2: Run pre-commit on the changed files**

Run: `PATH="$PATH:$HOME/.local/bin" pre-commit run --files custom_components/luxor_living/const.py custom_components/luxor_living/knx_gateway.py tests/test_knx_gateway.py`
Expected: black, isort, flake8, bandit all pass. Fix any formatting/lint issues black/isort don't auto-fix, re-run until clean.

- [ ] **Step 3: Add a CHANGELOG entry**

Add under the `### Fixed` section for the current unreleased version in `CHANGELOG.md` (check the top of the file for the current `[Unreleased]` or latest pre-release heading and match its format):

```markdown
- **Zombie-tunnel watchdog**: The IP1 tunnel can report CONNECTED for hours while every outgoing telegram fails its L_DATA_CON confirmation, with xknx's own heartbeat never detecting a real disconnect (confirmed on a 2026-07-10 log: ~20 confirmation timeouts/min for 9h, unaffected by the existing periodic REST-session flush from #180, which only cycles the REST layer, not the xknx tunnel object). A new watchdog polls xknx's `cemi_count_outgoing_error` counter every 30s and forces a full REST+KNX reconnect if it jumps by 5+ in one window, with a 5-minute cooldown to avoid reconnect storms.
```

- [ ] **Step 4: Commit**

```bash
cd "/home/philipp/projects/luxorliving  (public + maintance)"
git add CHANGELOG.md
git commit -m "docs: changelog entry for zombie-tunnel watchdog"
```

---

## Self-Review Notes (for whoever executes this plan)

- **Spec coverage:** detection via existing xknx counter (Task 3), forced full reconnect (Task 4), cooldown to prevent storms (Task 4), lifecycle wiring so it starts/stops with the gateway (Task 5), visibility via WARNING logs consistent with the logging-level fix already merged in `fix/wetterstation-vorne-naming-and-refresh-logging` (Task 3's `_LOGGER.warning` calls). All covered.
- **Not in scope for this plan (call out explicitly, don't silently add):** no UI/config option to tune the threshold/interval — these are constants, matching how `SESSION_REFRESH_INTERVAL` and `RECONNECT_FAILURE_THRESHOLD` are already unconfigurable constants in this codebase. Add a config option only if Marcus' real-world data shows the defaults need per-installation tuning.
- **Branch:** create a fresh branch off `main` before starting (`git checkout main && git pull && git checkout -b feat/zombie-tunnel-watchdog`) — per this repo's workflow, never commit directly to `main`.
- **After all tasks:** push the branch and open a PR (`gh pr create`), do not merge directly — Release Manager has exclusive merge authority per `AGENTS.md`.
