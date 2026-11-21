"""Deterministic event-sequence harness for LuxorKNXGateway connection state.

Idea (chaos-testing, but in-process and reproducible): drive a REAL gateway
with every short interleaving of xknx connection events, proactive REST
refreshes (ok / failing) and clock jumps, against a fake IP1 REST client whose
calls are gated so refresh steps can interleave with events. After each
sequence settles, check invariants on the gateway's ``_connected`` flag.

No third-party dependency: the state space is small enough to enumerate.
"""

from __future__ import annotations

import asyncio
import itertools
from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import MagicMock

from xknx.core import XknxConnectionState

from custom_components.luxor_living import knx_gateway as gw_mod
from custom_components.luxor_living.knx_gateway import LuxorKNXGateway

OPS = ("DISC", "CONN", "T5", "T40", "RS", "RF", "STEP", "FIN")
START_CLOCK = 1000.0


class FakeIP1:
    """Fake BAOS REST client. Tracks whether tunneling is authorised."""

    def __init__(self) -> None:
        self.tunneling = True
        self.pending: list[asyncio.Future] = []
        self.calls = 0
        self.fail_on_call: int | None = None

    async def _call(self, name: str) -> None:
        self.calls += 1
        fut = asyncio.get_running_loop().create_future()
        self.pending.append(fut)
        await fut  # released by a STEP op (or the final drain)
        if self.fail_on_call == self.calls:
            raise RuntimeError(f"injected failure in {name}")

    async def logout(self) -> None:
        self.tunneling = False  # logout deactivates tunneling on the IP1
        await self._call("logout")

    async def login(self, username: str, password: str) -> str:
        await self._call("login")
        return "session"

    async def get_tunneling_status(self) -> dict:
        await self._call("get_tunneling_status")
        return {}

    async def disable_tunneling(self) -> bool:
        await self._call("disable_tunneling")
        self.tunneling = False
        return True

    async def enable_tunneling(self) -> bool:
        await self._call("enable_tunneling")
        self.tunneling = True
        return True


class World:
    """One gateway + fake xknx state + fake IP1 + fake clock."""

    def __init__(self) -> None:
        self.clock = START_CLOCK
        self.tasks: list[asyncio.Task] = []
        self.xstate = XknxConnectionState.CONNECTED
        hass = MagicMock()
        hass.data = {}
        hass.async_create_task = self._spawn
        self.gateway = LuxorKNXGateway(
            hass=hass, host="192.0.2.1", port=3671, username="u", password="p"
        )
        self.ip1 = FakeIP1()
        self.gateway._rest_client = self.ip1
        self.gateway._xknx = MagicMock()
        self.gateway._setup_complete = True
        self.gateway._connected = True
        self.gateway._last_refresh_at = self.clock - 100.0
        self._sync_xknx_state()

    def _spawn(self, coro) -> asyncio.Task:
        task = asyncio.ensure_future(coro)
        self.tasks.append(task)
        return task

    def _sync_xknx_state(self) -> None:
        self.gateway._xknx.connection_manager.state = self.xstate

    async def _yield(self, n: int = 5) -> None:
        for _ in range(n):
            await asyncio.sleep(0)

    async def apply(self, op: str) -> None:
        gw = self.gateway
        if op == "DISC":
            self.xstate = XknxConnectionState.DISCONNECTED
            self._sync_xknx_state()
            gw._on_connection_state_changed(XknxConnectionState.DISCONNECTED)
        elif op == "CONN":
            self.xstate = XknxConnectionState.CONNECTED
            self._sync_xknx_state()
            gw._on_connection_state_changed(XknxConnectionState.CONNECTED)
        elif op == "T5":
            self.clock += 5.0
        elif op == "T40":
            self.clock += 40.0
        elif op in ("RS", "RF"):
            # RF = refresh whose enable_tunneling (5th REST call of a refresh) fails
            self.ip1.fail_on_call = self.ip1.calls + 5 if op == "RF" else None
            self._spawn(gw._async_refresh_until_success())
        elif op == "STEP" and self.ip1.pending:
            self.ip1.pending.pop(0).set_result(None)
        elif op == "FIN":  # let every in-flight REST cycle run to completion
            for _ in range(50):
                await self._yield()
                if not self.ip1.pending:
                    break
                self.ip1.pending.pop(0).set_result(None)
        await self._yield()

    async def settle(self) -> None:
        """Release every gated REST call and let all tasks finish."""
        for _ in range(200):
            await self._yield()
            if self.ip1.pending:
                self.ip1.pending.pop(0).set_result(None)
                continue
            if all(t.done() for t in self.tasks):
                return
        raise AssertionError("world did not settle (hung task / lock)")

    def violations(self) -> list[str]:
        gw = self.gateway
        out: list[str] = []
        xk_up = self.xstate == XknxConnectionState.CONNECTED
        if gw._connected and not xk_up:
            out.append("SAFETY: connected=True while xknx DISCONNECTED")
        if gw._connected and not self.ip1.tunneling:
            out.append("SAFETY: connected=True while IP1 tunneling is off")
        if xk_up and self.ip1.tunneling and not gw._connected:
            out.append("LIVENESS: stuck unavailable (xknx up, tunneling on, connected=False)")
        if xk_up and not self.ip1.tunneling and not gw._connected:
            out.append("LIVENESS: stuck unavailable, tunneling off after failed cycle")
        if gw._session_lock.locked():
            out.append("LOCK: _session_lock still held after settle")
        return out


def sequences(max_len: int) -> Iterator[tuple[str, ...]]:
    """All op sequences up to max_len that respect xknx's alternation."""
    for length in range(1, max_len + 1):
        for seq in itertools.product(OPS, repeat=length):
            up = True
            valid = True
            for op in seq:
                if op == "DISC":
                    valid = up
                    up = False
                elif op == "CONN":
                    valid = not up
                    up = True
                if not valid:
                    break
            if valid:
                yield seq


async def run_sequence(seq: tuple[str, ...]) -> list[str]:
    world = World()
    stub = SimpleNamespace(monotonic=lambda: world.clock, now=lambda: world.clock)
    original = gw_mod.time
    original_retry = gw_mod.SESSION_REFRESH_RETRY_INTERVAL
    gw_mod.time = stub  # the loop's own clock stays untouched
    gw_mod.SESSION_REFRESH_RETRY_INTERVAL = 0  # retries run immediately
    try:
        for op in seq:
            await world.apply(op)
        await world.settle()
        return world.violations()
    finally:
        gw_mod.time = original
        gw_mod.SESSION_REFRESH_RETRY_INTERVAL = original_retry
        for t in world.tasks:
            if not t.done():
                t.cancel()
