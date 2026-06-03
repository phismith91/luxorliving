"""Tests for Push webhook / WebSocket forwarder endpoint."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.luxor_living.__init__ import LuxorLivingPushView
from custom_components.luxor_living.integration_state import IntegrationState


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_push_view_calls_gateway():
    """Test that the push view forwards payloads to the configured gateway."""
    # Prepare integration state and register
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {}
    entry.options = {}

    state = IntegrationState(mapper=MagicMock(), config={}, overrides={}, entry=entry)
    entry.runtime_data = state

    # Attach mock gateway
    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    # Use a simple MagicMock for hass (we only need it to instantiate the view)
    hass = MagicMock()
    hass.config_entries.async_get_entry.return_value = entry
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
    entry.runtime_data = state

    # Mock gateway exists but should not be called due to auth failure
    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    hass = MagicMock()
    hass.config_entries.async_get_entry.return_value = entry
    view = LuxorLivingPushView(hass)

    req = MagicMock()
    req.json = AsyncMock(
        return_value={"entry_id": entry.entry_id, "address": "1/2/3", "value": True}
    )
    req.headers = {"X-LUXOR-PUSH-TOKEN": "wrong-token"}

    resp = await view.post(req)

    assert resp.status == 403
    gateway.process_incoming_value.assert_not_awaited()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_push_view_bearer_auth():
    """Test that Bearer Authorization header is accepted when configured."""
    entry = MagicMock()
    entry.entry_id = "entry_bearer"
    entry.data = {"push_token": "bearer-secret", "push_auth_method": "bearer"}
    entry.options = {}

    state = IntegrationState(mapper=MagicMock(), config={}, overrides={}, entry=entry)
    entry.runtime_data = state

    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    hass = MagicMock()
    hass.config_entries.async_get_entry.return_value = entry
    view = LuxorLivingPushView(hass)

    req = MagicMock()
    req.json = AsyncMock(
        return_value={"entry_id": entry.entry_id, "address": "1/2/3", "value": True}
    )
    req.headers = {"Authorization": "Bearer bearer-secret"}

    resp = await view.post(req)

    assert resp.status == 200
    gateway.process_incoming_value.assert_awaited_once_with("1/2/3", True, None)


@pytest.mark.integration
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
    entry.runtime_data = state

    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    hass = MagicMock()
    hass.config_entries.async_get_entry.return_value = entry
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


# ── Helper ────────────────────────────────────────────────────────────────────


def _make_view(entry_data=None, entry_options=None, entry_id="test_entry"):
    """Return a (view, entry, gateway) triple wired for testing post()."""
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = entry_data or {}
    entry.options = entry_options or {}

    from custom_components.luxor_living.integration_state import IntegrationState

    state = IntegrationState(mapper=MagicMock(), config={}, overrides={}, entry=entry)
    entry.runtime_data = state

    gateway = MagicMock()
    gateway.process_incoming_value = AsyncMock()
    state.knx_gateway = gateway

    hass = MagicMock()
    hass.config_entries.async_get_entry.return_value = entry

    from custom_components.luxor_living.__init__ import LuxorLivingPushView

    view = LuxorLivingPushView(hass)
    return view, entry, gateway


def _make_request(payload, headers=None):
    req = MagicMock()
    req.json = AsyncMock(return_value=payload)
    req.headers = headers or {}
    return req


class TestPushViewMutationTargets:
    """Smoke tests targeting surviving mutants in push_view.post()."""

    # ── HTTP status codes ─────────────────────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self):
        """Kill mutmut_10: status=400 → status=None."""
        view, _, _ = _make_view()
        req = MagicMock()
        req.json = AsyncMock(side_effect=ValueError("bad json"))
        req.headers = {}

        resp = await view.post(req)

        assert resp.status == 400

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_missing_entry_id_returns_400(self):
        """Kill mutmut_40: status=400 → no status for missing required fields."""
        view, _, _ = _make_view()
        resp = await view.post(_make_request({"address": "1/2/3", "value": True}))

        assert resp.status == 400

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_missing_address_returns_400(self):
        """Kill mutmut_40 (address variant): both entry_id and address are required."""
        view, entry, _ = _make_view()
        resp = await view.post(_make_request({"entry_id": entry.entry_id, "value": True}))

        assert resp.status == 400

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_unknown_entry_returns_404(self):
        """Kill mutmut_65: status=404 → status=405.

        Also kills mutmut_50: 'not hasattr(runtime_data)' → 'hasattr(runtime_data)'
        which would turn a 404 guard into a passthrough.
        """
        view, _, _ = _make_view()
        view.hass.config_entries.async_get_entry.return_value = None

        resp = await view.post(
            _make_request({"entry_id": "nonexistent", "address": "1/2/3", "value": 1})
        )

        assert resp.status == 404

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_entry_without_runtime_data_returns_404(self):
        """Kill mutmut_50: 'not hasattr(runtime_data)' → 'hasattr(runtime_data)'."""
        view, entry, _ = _make_view()
        del entry.runtime_data  # entry exists but has no runtime_data

        resp = await view.post(
            _make_request({"entry_id": entry.entry_id, "address": "1/2/3", "value": 1})
        )

        assert resp.status == 404

    # ── Payload key names ─────────────────────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_entry_id_key_name_is_entry_id(self):
        """Kill mutmut_20: payload.get('entry_id') → payload.get('XXentry_idXX').

        The gateway must be called when the payload uses the key 'entry_id',
        and NOT called when the key is anything else.
        """
        view, entry, gateway = _make_view()

        await view.post(_make_request({"entry_id": entry.entry_id, "address": "1/2/3", "value": 1}))
        gateway.process_incoming_value.assert_awaited_once()

    # ── Auth method key names ─────────────────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_token_auth_reads_push_token_key(self):
        """Kill mutmut_70: data.get('push_token') → data.get('PUSH_TOKEN').

        When auth_method='token' and push_token='secret', a request with
        the correct header must succeed (200) and one with wrong header must
        fail (403).
        """
        view, entry, _ = _make_view(
            entry_data={"push_token": "secret", "push_auth_method": "token"}
        )

        good = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": 1},
                headers={"X-LUXOR-PUSH-TOKEN": "secret"},
            )
        )
        bad = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": 1},
                headers={"X-LUXOR-PUSH-TOKEN": "wrong"},
            )
        )

        assert good.status == 200
        assert bad.status == 403

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_no_auth_config_defaults_to_none_method(self):
        """Kill mutmut_90: 'none' → 'NONE' fallback.

        When no push_auth_method is configured the endpoint must accept
        unauthenticated requests.
        """
        view, entry, gateway = _make_view()  # no auth configured

        resp = await view.post(
            _make_request({"entry_id": entry.entry_id, "address": "1/2/3", "value": True})
        )

        assert resp.status == 200
        gateway.process_incoming_value.assert_awaited_once()
