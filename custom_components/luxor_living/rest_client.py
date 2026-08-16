"""REST API Client for BAOS 777 with Tunneling Activation."""

from __future__ import annotations

import asyncio
import logging
import ssl
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, cast

import aiohttp

from .circuit_breaker import get_rest_api_circuit_breaker

_LOGGER = logging.getLogger(__name__)


def _make_ssl_context() -> ssl.SSLContext:
    """Return an SSL context for the IP1 gateway.

    The IP1 ships with a self-signed certificate so hostname verification and
    cert chain validation must be disabled (``CERT_NONE``). It also negotiates a
    legacy cipher that modern OpenSSL refuses at its default security level, so
    ``@SECLEVEL=0`` is REQUIRED — dropping it caused ``SSLV3_ALERT_HANDSHAKE_FAILURE``
    against real hardware (see v1.2.0-rc.1). This mirrors Home Assistant's
    ``SSLCipherList.INSECURE`` ("DEFAULT:@SECLEVEL=0"), which the injected shared
    session uses; this context is the fallback for the owned-session path.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
    return ctx


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class TunnelingError(Exception):
    """Raised when tunneling activation fails."""

    pass


class BAOSRestClient:
    """
    REST API Client for Weinzierl BAOS 777.

    Handles:
    - Login/Logout (Session Management)
    - Tunneling Activation/Deactivation
    - Status Queries

    Based on LUXORliving API Documentation:
    - POST /rest/auth/login → Session Token
    - PUT /rest/device/authtunneling → Enable/Disable Tunneling
    """

    def __init__(
        self,
        host: str,
        port: int = 443,
        use_https: bool = True,
        session: aiohttp.ClientSession | None = None,
    ):
        """
        Initialize REST API Client.

        Args:
            host: IP address of BAOS 777 device
            port: Port for REST API (default: 443 for HTTPS)
            use_https: Use HTTPS for secure communication (default: True, recommended)
            session: Optional aiohttp session to use. When provided (Home
                Assistant's shared session from ``async_get_clientsession(hass,
                verify_ssl=False, ssl_cipher=SSLCipherList.INSECURE)``), the
                client uses it and never closes it. The caller is responsible for
                configuring the IP1's legacy TLS (``verify_ssl=False`` +
                ``ssl_cipher=INSECURE``). When omitted, the client lazily creates
                and owns its own session built on :func:`_make_ssl_context`.
        """
        self.host = host
        self.port = port
        self.use_https = use_https
        # Use HTTPS by default for secure authentication
        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{host}:{port}"

        self.session_token: str | None = None
        self.session_expires: datetime | None = None
        self.tunneling_enabled = False

        self._session: aiohttp.ClientSession | None = session
        self._owns_session = session is None
        self._timeout = aiohttp.ClientTimeout(total=30)

    async def _create_owned_session(self) -> None:
        loop = asyncio.get_running_loop()
        ssl_context = await loop.run_in_executor(None, _make_ssl_context)
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(
            connector=connector, connector_owner=True, timeout=self._timeout
        )

    async def __aenter__(self):
        """Context manager entry."""
        if self._owns_session and self._session is None:
            await self._create_owned_session()
        return self

    async def __aexit__(self, *args):
        """Context manager exit - ensures cleanup."""
        await self.logout()
        # Only close sessions we own; injected (shared) sessions belong to HA.
        if self._owns_session and self._session:
            await self._session.close()

    async def login(self, username: str, password: str) -> str:
        """
        Login via REST API.

        Args:
            username: Username (default: admin)
            password: Password

        Returns:
            Session token

        Raises:
            AuthenticationError: If login fails
        """
        if not self._session and self._owns_session:
            await self._create_owned_session()

        url = f"{self.base_url}/rest/login"
        payload = {"username": username, "password": password}

        _LOGGER.debug(f"Attempting login to {url} with user: {username}")

        try:
            async with self._session.post(url, json=payload, timeout=self._timeout) as response:
                _LOGGER.debug(f"Login response status: {response.status}")
                _LOGGER.debug(f"Login response headers: {response.headers}")

                if response.status == 401:
                    response_text = await response.text()
                    _LOGGER.error(f"401 Unauthorized. Response body: {response_text}")
                    raise AuthenticationError("Invalid username or password")

                if response.status != 200:
                    raise AuthenticationError(f"Login failed with status {response.status}")

                # Response is a plain cookie string, not JSON
                cookie = await response.text()
                cookie = cookie.strip()

                if not cookie:
                    raise AuthenticationError("No session cookie in response")

                self.session_token = cookie

                # IP1 firmware enforces a hard 24 h session limit. Track expiry at 23.5 h
                # so _ensure_authenticated() fails before the gateway drops the session.
                # The reconnect handler in knx_gateway.py renews tunneling on actual drops.
                timeout_seconds = int(23.5 * 3600)  # 84600 s
                self.session_expires = datetime.now() + timedelta(seconds=timeout_seconds)

                _LOGGER.info(f"Login successful. Session expires at {self.session_expires}")

                # mypy: ensure return value is str (we validated cookie above)
                assert self.session_token is not None
                return self.session_token

        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Network error during login: {e}")

    async def logout(self):
        """
        Logout and end session.

        NOTE: Logout automatically deactivates tunneling!
        """
        if not self.session_token or not self._session:
            _LOGGER.debug("No active session to logout from")
            self.session_token = None
            self.session_expires = None
            self.tunneling_enabled = False
            return

        url = f"{self.base_url}/rest/logout"  # Correct endpoint per API docs
        headers = self._get_auth_headers()

        _LOGGER.debug(f"Logging out from {url}")

        try:
            async with self._session.post(url, headers=headers, timeout=self._timeout) as response:
                if response.status in (200, 204):  # API returns 204 per docs
                    _LOGGER.info("Logout successful. Tunneling auto-deactivated.")
                else:
                    _LOGGER.warning(f"Logout returned status {response.status}")

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error during logout: {e}")

        finally:
            # Clear session state
            self.session_token = None
            self.session_expires = None
            self.tunneling_enabled = False

    async def enable_tunneling(self) -> bool:
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

            _LOGGER.debug(
                "Enabling tunneling at %s (token: %s)",
                url,
                "set" if self.session_token else "missing",
            )

            async with self._session.put(
                url, json=payload, headers=headers, timeout=self._timeout
            ) as response:
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

    async def disable_tunneling(self) -> bool:
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

    async def get_tunneling_status(self) -> dict[str, Any]:
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
                return cast(dict[str, Any], await response.json())
            else:
                _LOGGER.warning(f"Get tunneling status returned {response.status}")
                return {"enabled": False, "connectedClients": 0, "maxSlots": 1}

    def _ensure_authenticated(self):
        """Raise AuthenticationError if not logged in."""
        if not self.session_token:
            raise AuthenticationError("Not logged in. Call login() first.")

        # Check session expiry
        if self.session_expires and datetime.now() >= self.session_expires:
            raise AuthenticationError("Session expired. Please login again.")

    def _get_auth_headers(self) -> dict[str, str]:
        """
        Get authentication headers per BAOS REST API Documentation (Page 7).

        Two supported methods:
        1. Cookie: user=%22TOKEN%22 (where %22 is URL-encoded double quote)
        2. Authorization: Token token=TOKEN (note "Token" prefix!)
        """
        if not self.session_token:
            return {}

        # URL-encode the cookie value: user="TOKEN" → user=%22TOKEN%22
        encoded_token = urllib.parse.quote(f'"{self.session_token}"')

        headers = {
            # Method 1: Cookie header
            "Cookie": f"user={encoded_token}",
            # Method 2: Authorization header with "Token" prefix (CRITICAL!)
            "Authorization": f"Token token={self.session_token}",
        }

        _LOGGER.debug("Auth headers: Cookie=user=%22...%22, Authorization=Token token=...")
        return headers

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        if not self.session_token:
            return False

        if self.session_expires and datetime.now() >= self.session_expires:
            return False

        return True

    # NOT CALLED BY INTEGRATION — used only in tests; diagnostics.py uses knx_gateway attributes directly
    def get_diagnostics(self) -> dict[str, Any]:
        """
        Get diagnostic information.

        Returns:
            Dictionary with client state for diagnostics
        """
        return {
            "host": self.host,
            "port": self.port,
            "use_https": self.use_https,
            "authenticated": self.is_authenticated,
            "session_token": bool(self.session_token),
            "session_expires": self.session_expires.isoformat() if self.session_expires else None,
            "tunneling_enabled": self.tunneling_enabled,
        }
