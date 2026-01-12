"""Tests for Push webhook / WebSocket forwarder endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.luxor_living.__init__ import LuxorLivingPushView
from custom_components.luxor_living.integration_state import (
    IntegrationState,
    register_integration_state,
)


@pytest.mark.asyncio
async def test_push_view_calls_gateway():
    """Test that the push view forwards payloads to the configured gateway."""
    # Prepare integration state and register
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {}
    entry.options = {}

    state = IntegrationState(mapper=MagicMock(), config={}, overrides={}, entry=entry)
    register_integration_state(entry.entry_id, state)

    # Attach mock gateway
    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    # Use a simple MagicMock for hass (we only need it to instantiate the view)
    hass = MagicMock()
    view = LuxorLivingPushView(hass)

    # Fake request with JSON coroutine and headers
    req = MagicMock()
    req.json = AsyncMock(return_value={"entry_id": entry.entry_id, "address": "1/2/3", "value": True})
    req.headers = {}

    resp = await view.post(req)

    # Ensure gateway was called with normalized parameters
    gateway.process_incoming_value.assert_awaited_once_with("1/2/3", True, None)

    # Response should indicate success
    assert resp.status == 200


@pytest.mark.asyncio
async def test_push_view_forbidden_when_token_mismatch():
    """Test that push requests are rejected when token is configured but missing/invalid."""
    entry = MagicMock()
    entry.entry_id = "entry_with_token"
    entry.data = {"push_token": "secret-token"}
    entry.options = {}

    state = IntegrationState(mapper=MagicMock(), config={}, overrides={}, entry=entry)
    register_integration_state(entry.entry_id, state)

    # Mock gateway exists but should not be called due to auth failure
    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    hass = MagicMock()
    view = LuxorLivingPushView(hass)

    req = MagicMock()
    req.json = AsyncMock(return_value={"entry_id": entry.entry_id, "address": "1/2/3", "value": True})
    req.headers = {"X-LUXOR-PUSH-TOKEN": "wrong-token"}

    resp = await view.post(req)

    assert resp.status == 403
    gateway.process_incoming_value.assert_not_awaited()
