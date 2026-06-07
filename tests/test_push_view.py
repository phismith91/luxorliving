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
    entry.data = {"push_auth_method": "token", "push_token": "test-token"}
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
    req.headers = {"X-LUXOR-PUSH-TOKEN": "test-token"}

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


_DEFAULT_AUTH = {"push_auth_method": "token", "push_token": "test-token"}


def _make_view(entry_data=None, entry_options=None, entry_id="test_entry"):
    """Return a (view, entry, gateway) triple wired for testing post()."""
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = entry_data if entry_data is not None else dict(_DEFAULT_AUTH)
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
    req.headers = headers if headers is not None else {"X-LUXOR-PUSH-TOKEN": "test-token"}
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
    async def test_no_auth_method_configured_returns_403(self):
        """Push endpoint must reject requests when no auth method is configured.

        Security requirement: unauthenticated access is never permitted.
        An entry with no push_auth_method must not allow arbitrary KNX writes.
        """
        view, entry, gateway = _make_view(entry_data={})

        resp = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": True},
                headers={},
            )
        )

        assert resp.status == 403
        gateway.process_incoming_value.assert_not_called()

    @pytest.mark.asyncio
    async def test_token_auth_without_configured_token_returns_403(self):
        """Token auth with no token stored must reject, not allow all requests."""
        view, entry, gateway = _make_view(entry_data={"push_auth_method": "token"})

        resp = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": True},
                headers={"X-LUXOR-PUSH-TOKEN": "anything"},
            )
        )

        assert resp.status == 403
        gateway.process_incoming_value.assert_not_called()

    @pytest.mark.asyncio
    async def test_bearer_auth_without_configured_token_returns_403(self):
        """Bearer auth with no token stored must reject, not allow all requests."""
        view, entry, gateway = _make_view(entry_data={"push_auth_method": "bearer"})

        resp = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": True},
                headers={"Authorization": "Bearer anything"},
            )
        )

        assert resp.status == 403
        gateway.process_incoming_value.assert_not_called()


@pytest.mark.smoke
class TestPushViewResponseBody:
    """Kill surviving mutants that mutate response body keys/values and value_type key."""

    @pytest.mark.asyncio
    async def test_success_response_body_has_status_ok(self):
        """Kill: {'status': 'ok'} → {'status': 'XX'} or None mutations."""
        import json

        view, entry, _ = _make_view()
        resp = await view.post(
            _make_request({"entry_id": entry.entry_id, "address": "1/2/3", "value": True})
        )
        body = json.loads(resp.body)
        assert body.get("status") == "ok"

    @pytest.mark.asyncio
    async def test_invalid_json_response_body_error_key(self):
        """Kill: {'error': 'invalid_json'} → {None / key mutations}."""
        import json

        view, _, _ = _make_view()
        req = MagicMock()
        req.json = AsyncMock(side_effect=ValueError("bad"))
        req.headers = {}
        resp = await view.post(req)
        body = json.loads(resp.body)
        assert "error" in body
        assert body["error"] == "invalid_json"

    @pytest.mark.asyncio
    async def test_missing_fields_response_error_key(self):
        """Kill: 'missing entry_id or address' → string mutations."""
        import json

        view, _, _ = _make_view()
        resp = await view.post(_make_request({"value": True}))
        body = json.loads(resp.body)
        assert "error" in body
        assert "missing" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_unknown_entry_response_error_key(self):
        """Kill: {'error': 'entry_not_found'} → key/value mutations."""
        import json

        view, _, _ = _make_view()
        view.hass.config_entries.async_get_entry.return_value = None
        resp = await view.post(_make_request({"entry_id": "ghost", "address": "1/2/3", "value": 1}))
        body = json.loads(resp.body)
        assert "error" in body
        assert body["error"] == "entry_not_found"

    @pytest.mark.asyncio
    async def test_token_forbidden_response_error_key(self):
        """Kill: {'error': 'forbidden'} → key/value mutations."""
        import json

        view, entry, _ = _make_view(
            entry_data={"push_token": "secret", "push_auth_method": "token"}
        )
        resp = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": 1},
                headers={"X-LUXOR-PUSH-TOKEN": "wrong"},
            )
        )
        body = json.loads(resp.body)
        assert "error" in body
        assert body["error"] == "forbidden"

    @pytest.mark.asyncio
    async def test_value_type_forwarded_to_gateway(self):
        """Kill: value_type = None / payload.get('VALUE_TYPE') mutations."""
        view, entry, gateway = _make_view()
        resp = await view.post(
            _make_request(
                {
                    "entry_id": entry.entry_id,
                    "address": "1/2/3",
                    "value": 42,
                    "value_type": "percent",
                }
            )
        )
        assert resp.status == 200
        gateway.process_incoming_value.assert_awaited_once_with("1/2/3", 42, "percent")

    @pytest.mark.asyncio
    async def test_value_type_key_is_value_type_not_uppercase(self):
        """Kill: payload.get('value_type') → payload.get('VALUE_TYPE') mutation."""
        view, entry, gateway = _make_view()
        # Lowercase key: 'value_type' — only correct key should be recognized
        await view.post(
            _make_request(
                {
                    "entry_id": entry.entry_id,
                    "address": "1/2/3",
                    "value": 1,
                    "value_type": "binary",
                }
            )
        )
        args = gateway.process_incoming_value.call_args
        assert args[0][2] == "binary"

    @pytest.mark.asyncio
    async def test_address_key_forwarded_correctly(self):
        """Kill: payload.get('address') → payload.get('ADDRESS') mutations."""
        view, entry, gateway = _make_view()
        await view.post(
            _make_request({"entry_id": entry.entry_id, "address": "5/4/3", "value": True})
        )
        args = gateway.process_incoming_value.call_args[0]
        assert args[0] == "5/4/3"

    @pytest.mark.asyncio
    async def test_value_key_forwarded_correctly(self):
        """Kill: payload.get('value') → payload.get('VALUE') mutations."""
        view, entry, gateway = _make_view()
        await view.post(
            _make_request({"entry_id": entry.entry_id, "address": "1/1/1", "value": 99})
        )
        args = gateway.process_incoming_value.call_args[0]
        assert args[1] == 99

    @pytest.mark.asyncio
    async def test_bearer_wrong_token_returns_403_with_error_body(self):
        """Kill: bearer forbidden body key/value mutations."""
        import json

        view, entry, _ = _make_view(
            entry_data={"push_token": "secret", "push_auth_method": "bearer"}
        )
        resp = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": 1},
                headers={"Authorization": "Bearer wrong"},
            )
        )
        assert resp.status == 403
        body = json.loads(resp.body)
        assert "error" in body
        assert body["error"] == "forbidden"

    @pytest.mark.asyncio
    async def test_bearer_missing_prefix_returns_403(self):
        """Kill: 'Bearer ' prefix check mutations."""
        import json

        view, entry, _ = _make_view(
            entry_data={"push_token": "secret", "push_auth_method": "bearer"}
        )
        resp = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": 1},
                headers={"Authorization": "secret"},  # no "Bearer " prefix
            )
        )
        assert resp.status == 403
        body = json.loads(resp.body)
        assert body["error"] == "forbidden"

    @pytest.mark.asyncio
    async def test_bearer_splits_on_space_to_get_token(self):
        """Kill: auth_header.split(' ', 1)[1] → [0] index mutation."""
        view, entry, gateway = _make_view(
            entry_data={"push_token": "mytoken", "push_auth_method": "bearer"}
        )
        resp = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": True},
                headers={"Authorization": "Bearer mytoken"},
            )
        )
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_hmac_missing_signature_returns_403(self):
        """Kill: HMAC sig guard mutations."""
        import json

        view, entry, _ = _make_view(
            entry_data={"push_token": "hmac-key", "push_auth_method": "hmac"}
        )
        resp = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": 1},
                headers={},  # no signature header
            )
        )
        assert resp.status == 403
        body = json.loads(resp.body)
        assert body["error"] == "forbidden"

    @pytest.mark.asyncio
    async def test_hmac_wrong_signature_returns_403(self):
        """Kill: hmac.compare_digest mutations."""
        import json

        view, entry, _ = _make_view(
            entry_data={"push_token": "hmac-key", "push_auth_method": "hmac"}
        )
        resp = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": 1},
                headers={"X-LUXOR-PUSH-SIGNATURE": "badhash"},
            )
        )
        assert resp.status == 403
        body = json.loads(resp.body)
        assert body["error"] == "forbidden"

    @pytest.mark.asyncio
    async def test_options_token_used_for_auth(self):
        """Kill: options_token = state.entry.options.get('push_token') mutations."""
        view, entry, gateway = _make_view(
            entry_data={},
            entry_options={"push_token": "opts-secret", "push_auth_method": "token"},
        )
        good = await view.post(
            _make_request(
                {"entry_id": entry.entry_id, "address": "1/2/3", "value": 1},
                headers={"X-LUXOR-PUSH-TOKEN": "opts-secret"},
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
