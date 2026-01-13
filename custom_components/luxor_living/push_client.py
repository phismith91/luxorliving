"""WebSocket push client for LUXORliving integration.

Connects to a configured WebSocket endpoint and forwards incoming JSON messages
as pushed values into the local KNX gateway via process_incoming_value.

The expected message format is JSON:
{
  "entry_id": "<config_entry_id>",
  "address": "1/2/3",
  "value": true|42|23.5|[...],
  "value_type": "binary"|"percent"|null
}

The client performs exponential backoff on reconnects and supports an optional
`Authorization: Bearer <token>` header when `ws_token` is configured.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from aiohttp import ClientSession, ClientWebSocketResponse

from .integration_state import get_integration_state

_LOGGER = logging.getLogger(__name__)


class PushClient:
    """Simple WebSocket push client with reconnection/backoff logic."""

    def __init__(self, hass, entry_id: str, ws_url: str, ws_token: str | None = None) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self._ws_url = ws_url
        self._ws_token = ws_token
        self._session: ClientSession | None = None
        self._task: asyncio.Task | None = None
        self._stopped = False

    def start(self) -> None:
        """Start background task for websocket connection."""
        if self._task and not self._task.done():
            return
        self._task = self.hass.async_create_task(self._run())

    async def stop(self) -> None:
        """Stop the client and cancel background task."""
        self._stopped = True
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._session:
            try:
                await self._session.close()
            except Exception:
                pass

    async def _run(self) -> None:
        """Connection loop with exponential backoff."""
        backoff = 1.0
        self._session = ClientSession()

        while not self._stopped:
            try:
                headers = {}
                if self._ws_token:
                    headers["Authorization"] = f"Bearer {self._ws_token}"

                _LOGGER.info("Connecting to push websocket: %s", self._ws_url)
                async with self._session.ws_connect(self._ws_url, headers=headers) as ws:
                    _LOGGER.info("Connected to push websocket: %s", self._ws_url)
                    backoff = 1.0
                    await self._listen(ws)
            except asyncio.CancelledError:
                raise
            except Exception as err:
                _LOGGER.warning("Push websocket connection error: %s - retrying in %.1fs", err, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)

    async def _listen(self, ws: ClientWebSocketResponse) -> None:
        """Listen for incoming messages and forward them."""
        async for msg in ws:
            if msg.type.name in ("CLOSED", "CLOSING"):
                break
            if msg.type.name == "TEXT":
                try:
                    payload = json.loads(msg.data)
                except Exception:
                    _LOGGER.debug("Received non-json push payload: %s", msg.data)
                    continue

                entry_id = payload.get("entry_id")
                if entry_id != self.entry_id:
                    _LOGGER.debug("Push for different entry_id %s (expected %s) - ignoring", entry_id, self.entry_id)
                    continue

                address = payload.get("address")
                value = payload.get("value")
                value_type = payload.get("value_type")

                if not address:
                    _LOGGER.debug("Push payload missing address: %s", payload)
                    continue

                try:
                    state = get_integration_state(self.entry_id)
                    gateway = state.get_gateway_or_raise()
                    # schedule processing in hass loop
                    self.hass.async_create_task(gateway.process_incoming_value(address, value, value_type))
                except Exception as err:
                    _LOGGER.error("Failed to process push message: %s", err, exc_info=True)
            else:
                # ignore binary/ping/pong
                continue
