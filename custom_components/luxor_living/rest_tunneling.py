"""REST API Client Tunneling Operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, cast

import aiohttp

from .circuit_breaker import get_rest_api_circuit_breaker
from .rest_exceptions import AuthenticationError, TunnelingError

if TYPE_CHECKING:
    from .rest_client import BAOSRestClient

_LOGGER = logging.getLogger(__name__)


class TunnelingManagementMixin:
    """Mixin for tunneling operations (enable, disable, status)."""

    async def enable_tunneling(self: "BAOSRestClient") -> bool:
        """
        Enable KNX Tunneling via REST API with circuit breaker protection.

        According to LUXORliving API Documentation:
        PUT /rest/device/authtunneling
        {"enabled": true}

        Returns:
            True if tunneling was enabled successfully

        Raises:
            AuthenticationError: If not logged in
            TunnelingError: If activation fails
            CircuitBreakerOpenException: If circuit breaker is open
        """
        circuit_breaker = get_rest_api_circuit_breaker()

        async def _enable_tunneling():
            self._ensure_authenticated()

            url = f"{self.base_url}/rest/device/authtunneling"
            payload = {"enabled": True}
            headers = self._get_auth_headers()

            _LOGGER.debug(f"Enabling tunneling at {url}")
            _LOGGER.debug(f"Tunneling headers: {headers}")
            _LOGGER.debug(
                f"Session token: {self.session_token[:10]}..." if self.session_token else "No token"
            )

            async with self._session.put(url, json=payload, headers=headers) as response:
                _LOGGER.debug(f"Tunneling response status: {response.status}")
                _LOGGER.debug(f"Tunneling response headers: {response.headers}")

                if response.status == 401:
                    raise AuthenticationError("Session expired or invalid")

                if response.status == 403:
                    response_text = await response.text()
                    _LOGGER.error(
                        f"403 Forbidden when enabling tunneling. Response: {response_text}"
                    )
                    raise TunnelingError(
                        "Failed to enable tunneling: Forbidden (403). Check API permissions."
                    )

                # API Documentation Page 12: PUT /rest/device/authtunneling returns 204, not 200!
                if response.status not in (200, 204):
                    response_text = await response.text()
                    _LOGGER.error(
                        f"Tunneling failed with {response.status}. Response: {response_text}"
                    )
                    raise TunnelingError(f"Failed to enable tunneling (status {response.status})")

                # Success! With 204 (No Content) there's no response body
                if response.status == 204:
                    self.tunneling_enabled = True
                    _LOGGER.debug("KNX Tunneling enabled successfully (204 No Content)")
                    return True

                # With 200, verify from response body
                data = await response.json()
                self.tunneling_enabled = data.get("enabled", True)
                _LOGGER.debug("KNX Tunneling enabled successfully (200 OK)")
                return True

        return cast(bool, await circuit_breaker.call(_enable_tunneling))

    async def disable_tunneling(self: "BAOSRestClient") -> bool:
        """
        Disable KNX Tunneling with circuit breaker protection.

        NOTE: Logout also disables tunneling automatically.

        Returns:
            True if tunneling was disabled
        """
        circuit_breaker = get_rest_api_circuit_breaker()

        async def _disable_tunneling():
            self._ensure_authenticated()

            url = f"{self.base_url}/rest/device/authtunneling"
            payload = {"enabled": False}
            headers = self._get_auth_headers()

            _LOGGER.debug(f"Disabling tunneling at {url}")

            async with self._session.put(url, json=payload, headers=headers) as response:
                if response.status in (200, 204):
                    self.tunneling_enabled = False
                    _LOGGER.info(f"KNX Tunneling disabled ({response.status})")
                    return True
                else:
                    response_text = await response.text()
                    _LOGGER.warning(
                        f"Disable tunneling returned {response.status}: {response_text}"
                    )
                    return False

        try:
            return cast(bool, await circuit_breaker.call(_disable_tunneling))
        except Exception as e:
            _LOGGER.error(f"Error disabling tunneling: {e}")
            return False

    async def get_tunneling_status(self: "BAOSRestClient") -> Dict[str, Any]:
        """
        Get current tunneling status.

        Returns:
            {
                "enabled": bool,
                "connectedClients": int,
                "maxSlots": int
            }
        """
        self._ensure_authenticated()
        assert self._session is not None

        url = f"{self.base_url}/rest/device/authtunneling"
        headers = self._get_auth_headers()

        async with self._session.get(url, headers=headers) as response:
            if response.status == 200:
                return cast(Dict[str, Any], await response.json())
            else:
                _LOGGER.warning(f"Get tunneling status returned {response.status}")
                return {"enabled": False, "connectedClients": 0, "maxSlots": 1}
