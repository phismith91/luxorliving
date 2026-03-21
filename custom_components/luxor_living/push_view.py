"""Webhook/WebSocket push endpoint for LUXORliving integration."""

from __future__ import annotations

import json
import logging

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class LuxorLivingPushView(HomeAssistantView):
    """Endpoint to receive externally pushed KNX values (webhook / websocket forwarder)."""

    url = "/api/luxor_living/push"
    name = "api:luxor_living:push"
    requires_auth = False  # Token-based auth handled optionally per config entry

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the push view."""
        self.hass = hass

    async def post(self, request):
        """Handle incoming push event.

        Expected JSON payload:
            {
                "entry_id": "<config_entry_id>",
                "address": "1/2/3",
                "value": true|42|23.5|[...],
                "value_type": "binary"|"percent"|None
            }

        Authentication:
            - If the config entry defines "push_token" in data or options, a matching
              header "X-LUXOR-PUSH-TOKEN: <token>" is required. If absent, 403 returned.
            - If no token configured, the endpoint accepts unauthenticated calls (local use).
        """
        try:
            payload = await request.json()
        except (json.JSONDecodeError, ValueError) as err:
            _LOGGER.debug("Push endpoint received invalid JSON: %s", err)
            from aiohttp import web

            return web.json_response({"error": "invalid_json"}, status=400)

        entry_id = payload.get("entry_id")
        address = payload.get("address")
        value = payload.get("value")
        value_type = payload.get("value_type")

        if not entry_id or not address:
            from aiohttp import web

            return web.json_response({"error": "missing entry_id or address"}, status=400)

        # Authorization: check configured auth method
        config_entry = self.hass.config_entries.async_get_entry(entry_id)
        if config_entry is None or not hasattr(config_entry, "runtime_data"):
            from aiohttp import web

            return web.json_response({"error": "entry_not_found"}, status=404)
        state = config_entry.runtime_data

        # Determine configured values (allow in-data or options)
        config_token = state.entry.data.get("push_token") if state.entry else None
        options_token = state.entry.options.get("push_token") if state.entry else None
        configured_token = config_token or options_token

        auth_method = (
            state.entry.data.get("push_auth_method")
            if state.entry and state.entry.data.get("push_auth_method")
            else state.entry.options.get("push_auth_method") if state.entry else None
        ) or "none"

        # Token-based (legacy): header X-LUXOR-PUSH-TOKEN must match
        if auth_method == "token":
            token_header = request.headers.get("X-LUXOR-PUSH-TOKEN")
            if configured_token and token_header != configured_token:
                from aiohttp import web

                return web.json_response({"error": "forbidden"}, status=403)

        # Bearer token: Authorization: Bearer <token>
        elif auth_method == "bearer":
            auth_header = request.headers.get("Authorization", "")
            if configured_token and not auth_header.startswith("Bearer "):
                from aiohttp import web

                return web.json_response({"error": "forbidden"}, status=403)
            bearer = auth_header.split(" ", 1)[1] if " " in auth_header else ""
            if configured_token and bearer != configured_token:
                from aiohttp import web

                return web.json_response({"error": "forbidden"}, status=403)

        # HMAC: header X-LUXOR-PUSH-SIGNATURE hex-encoded sha256 of sorted-json using token as key
        elif auth_method == "hmac":
            import hashlib
            import hmac

            sig_header = request.headers.get("X-LUXOR-PUSH-SIGNATURE", "")
            if not configured_token or not sig_header:
                from aiohttp import web

                return web.json_response({"error": "forbidden"}, status=403)

            # Compute signature over deterministic JSON representation
            expected = hmac.new(
                configured_token.encode(),
                json.dumps(payload, sort_keys=True).encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, sig_header):
                from aiohttp import web

                return web.json_response({"error": "forbidden"}, status=403)

        # else: none -> accept unauthenticated pushes
        # Handle push
        try:
            gateway = state.get_gateway_or_raise()
            await gateway.process_incoming_value(address, value, value_type)
            from aiohttp import web

            return web.json_response({"status": "ok"})
        except RuntimeError as err:
            from aiohttp import web

            return web.json_response({"error": str(err)}, status=503)
        except Exception as err:
            _LOGGER.exception("Error handling push request: %s", err)
            from aiohttp import web

            return web.json_response({"error": "internal_error"}, status=500)
