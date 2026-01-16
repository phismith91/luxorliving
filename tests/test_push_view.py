"""Tests for Push webhook / WebSocket forwarder endpoint."""

from unittest.mock import AsyncMock, MagicMock

import pytest

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
    req.json = AsyncMock(
        return_value={"entry_id": entry.entry_id, "address": "1/2/3", "value": True}
    )
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
    entry.data = {"push_token": "secret-token", "push_auth_method": "token"}
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
    req.json = AsyncMock(
        return_value={"entry_id": entry.entry_id, "address": "1/2/3", "value": True}
    )
    req.headers = {"X-LUXOR-PUSH-TOKEN": "wrong-token"}

    resp = await view.post(req)

    assert resp.status == 403
    gateway.process_incoming_value.assert_not_awaited()


@pytest.mark.asyncio
async def test_push_view_bearer_auth():
    """Test that Bearer Authorization header is accepted when configured."""
    entry = MagicMock()
    entry.entry_id = "entry_bearer"
    entry.data = {"push_token": "bearer-secret", "push_auth_method": "bearer"}
    entry.options = {}

    state = IntegrationState(mapper=MagicMock(), config={}, overrides={}, entry=entry)
    register_integration_state(entry.entry_id, state)

    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    hass = MagicMock()
    view = LuxorLivingPushView(hass)

    req = MagicMock()
    req.json = AsyncMock(
        return_value={"entry_id": entry.entry_id, "address": "1/2/3", "value": True}
    )
    req.headers = {"Authorization": "Bearer bearer-secret"}

    resp = await view.post(req)

    assert resp.status == 200
    gateway.process_incoming_value.assert_awaited_once_with("1/2/3", True, None)


@pytest.mark.asyncio
async def test_push_view_hmac_auth():
    """Test that HMAC signature header is validated when configured."""
    import hashlib
    import hmac
    import json

    entry = MagicMock()
    entry.entry_id = "entry_hmac"
    entry.data = {"push_token": "hmac-secret", "push_auth_method": "hmac"}
    entry.options = {}

    state = IntegrationState(mapper=MagicMock(), config={}, overrides={}, entry=entry)
    register_integration_state(entry.entry_id, state)

    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    hass = MagicMock()
    view = LuxorLivingPushView(hass)

    payload = {"entry_id": entry.entry_id, "address": "1/2/3", "value": True}
    sig = hmac.new(
        entry.data["push_token"].encode(),
        json.dumps(payload, sort_keys=True).encode(),
        hashlib.sha256,
    ).hexdigest()

    req = MagicMock()
    req.json = AsyncMock(return_value=payload)
    req.headers = {"X-LUXOR-PUSH-SIGNATURE": sig}

    resp = await view.post(req)

    assert resp.status == 200
    gateway.process_incoming_value.assert_awaited_once_with("1/2/3", True, None)
