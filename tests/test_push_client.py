"""Tests for PushClient."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.luxor_living.integration_state import IntegrationState
from custom_components.luxor_living.push_client import PushClient


@pytest.mark.asyncio
async def test_push_client_receives_and_forwards(aiohttp_server, socket_enabled):
    """PushClient should connect to websocket server and forward messages to gateway."""

    # Create a simple websocket handler that sends one message and then waits
    async def ws_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        payload = json.dumps({"entry_id": "test_entry", "address": "1/2/3", "value": True})
        await ws.send_str(payload)
        # Keep connection alive briefly
        await asyncio.sleep(0.05)
        await ws.close()
        return ws

    # Create aiohttp test server
    from aiohttp import web

    app = web.Application()
    app.router.add_get("/ws", ws_handler)
    server = await aiohttp_server(app)
    ws_url = f"ws://{server.host}:{server.port}/ws"

    # Register integration state and attach mock gateway
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {}
    entry.options = {}

    state = IntegrationState(mapper=MagicMock(), config={}, overrides={}, entry=entry)
    entry.runtime_data = state

    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    # Create a fake hass-like object with async_create_task
    fake_hass = MagicMock()
    fake_hass.async_create_task = lambda coro: asyncio.create_task(coro)
    fake_hass.config_entries.async_get_entry.return_value = entry

    # Start PushClient
    client = PushClient(fake_hass, entry.entry_id, ws_url)
    client.start()

    # Wait for a short moment to allow connection and message processing
    await asyncio.sleep(0.2)

    # Verify that the gateway received the pushed value at least once
    assert gateway.process_incoming_value.await_count >= 1
    # Optionally check latest call args
    last_call = gateway.process_incoming_value.await_args_list[-1]
    assert last_call.args == ("1/2/3", True, None)

    # Clean up
    await client.stop()
