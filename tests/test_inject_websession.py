"""Tests for Platinum inject-websession compliance.

Both the REST client and the push client must obtain their aiohttp session from
Home Assistant's shared `async_get_clientsession(hass)` helper instead of
creating (and owning) their own `ClientSession`.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

import custom_components.luxor_living.push_client as push_client_mod
from custom_components.luxor_living.push_client import PushClient
from custom_components.luxor_living.rest_client import BAOSRestClient


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_push_run_acquires_shared_session(monkeypatch):
    """PushClient._run obtains the session from async_get_clientsession(hass)."""
    shared = MagicMock()
    captured = {}

    def fake_get_clientsession(hass):
        captured["hass"] = hass
        return shared

    monkeypatch.setattr(push_client_mod, "async_get_clientsession", fake_get_clientsession)

    client = PushClient(MagicMock(), "entry", "ws://example/ws")
    client._stopped = True  # skip the connect loop body, only acquire session
    await client._run()

    assert client._session is shared
    assert captured["hass"] is client.hass


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_push_stop_does_not_close_shared_session():
    """PushClient.stop must not close the HA-owned shared session."""
    shared = MagicMock()
    shared.close = AsyncMock()

    client = PushClient(MagicMock(), "entry", "ws://example/ws")
    client._session = shared
    await client.stop()

    shared.close.assert_not_called()


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_rest_client_uses_injected_session():
    """BAOSRestClient accepts an injected session and treats it as not-owned."""
    shared = MagicMock()
    shared.close = AsyncMock()

    client = BAOSRestClient("1.2.3.4", session=shared)
    assert client._session is shared

    # Context-manager entry must not replace an injected session.
    await client.__aenter__()
    assert client._session is shared


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_rest_client_does_not_close_injected_session():
    """Exiting the context manager must not close an injected (shared) session."""
    shared = MagicMock()
    shared.close = AsyncMock()

    client = BAOSRestClient("1.2.3.4", session=shared)
    client.logout = AsyncMock()
    await client.__aexit__(None, None, None)

    shared.close.assert_not_called()
