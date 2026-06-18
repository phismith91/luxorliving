"""REST API Client for BAOS 777 with Tunneling Activation."""

from __future__ import annotations

import asyncio
import logging
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, cast

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
        session: Optional[aiohttp.ClientSession] = None,
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

        self.session_token: Optional[str] = None
        self.session_expires: Optional[datetime] = None
        self.tunneling_enabled = False

        self._session: Optional[aiohttp.ClientSession] = session
        self._owns_session = session is None
        self._timeout = aiohttp.ClientTimeout(total=30)

    async def __aenter__(self):
        """Context manager entry."""
        if self._owns_session and self._session is None:
            loop = asyncio.get_running_loop()
            ssl_context = await loop.run_in_executor(None, _make_ssl_context)
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(
                connector=connector, connector_owner=True, timeout=self._timeout
            )
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
            loop = asyncio.get_running_loop()
            ssl_context = await loop.run_in_executor(None, _make_ssl_context)
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(
                connector=connector, connector_owner=True, timeout=self._timeout
            )

        url = f"{self.base_url}/rest/login"
        payload = {"username": username, "password": password}

        _LOGGER.debug(f"Attempting login to {url} with user: {username}")

        try:
            async with self._session.post(url, json=payload) as response:
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
            async with self._session.post(url, headers=headers) as response:
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

    # NOT CALLED BY INTEGRATION — logout disables tunneling automatically; kept for completeness
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

    # NOT CALLED BY INTEGRATION — reserved for future diagnostics/health checks
    async def get_tunneling_status(self) -> Dict[str, Any]:
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

    # NOT CALLED BY INTEGRATION — reserved for future datapoint polling (superseded by knxprod static lookup)
    async def async_get_datapoints(self) -> Optional[list]:
        """
        Get all BAOS datapoints with their current values.

        Per BAOS REST API Documentation:
        GET /rest/datapoints

        Returns list of datapoint objects:
        [
            {
                "id": 1,
                "name": "1/0/0",
                "value": true,
                "type": "DPT-1",
                "room": "Bedroom",
                "function": "Light"
            },
            ...
        ]

        Returns:
            List of datapoint dicts, or None on error
        """
        self._ensure_authenticated()
        assert self._session is not None

        url = f"{self.base_url}/rest/datapoints"
        headers = self._get_auth_headers()

        _LOGGER.debug(f"🔍 Fetching all datapoints from {url}")

        try:
            async with self._session.get(url, headers=headers) as response:
                if response.status == 401:
                    _LOGGER.error("Session expired when fetching datapoints")
                    return None

                if response.status != 200:
                    response_text = await response.text()
                    _LOGGER.error(
                        f"Failed to fetch datapoints: {response.status} - {response_text}"
                    )
                    return None

                response_data = cast(Dict[str, Any], await response.json())

                # BAOS API returns {"datapoints": [{"id": 1, "url": "..."}]}
                if isinstance(response_data, dict) and "datapoints" in response_data:
                    datapoints = response_data["datapoints"]
                    _LOGGER.debug(f"Fetched {len(datapoints)} datapoint references from BAOS")
                    _LOGGER.debug(f"🔍 First 3 datapoints: {datapoints[:3]}")
                    return cast(Optional[list], datapoints)
                else:
                    _LOGGER.error(f"Unexpected API format: {type(response_data)}")
                    _LOGGER.debug(f"Response data: {response_data}")
                    return None

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Network error fetching datapoints: {e}")
            return None

    # NOT CALLED BY INTEGRATION — reserved for future datapoint polling (superseded by knxprod static lookup)
    async def async_get_datapoint_details(
        self, datapoint_id: int, timeout: float = 2.0
    ) -> Optional[dict]:
        """
        Get full details of a specific BAOS datapoint including GroupAddress name.

        Per BAOS REST API Documentation:
        GET /rest/datapoint/<id>

        Returns:
        {
            "id": 1,
            "name": "1/0/0",
            "value": true,
            "type": "DPT-1",
            "room": "Bedroom",
            "function": "Light"
        }

        Args:
            datapoint_id: BAOS datapoint ID (integer)
            timeout: Request timeout in seconds (default: 2.0)

        Returns:
            Full datapoint dict with name, value, type, etc., or None on error
        """
        self._ensure_authenticated()
        assert self._session is not None

        url = f"{self.base_url}/rest/datapoints/{datapoint_id}"
        headers = self._get_auth_headers()

        _LOGGER.debug(
            f"🔍 Fetching datapoint details {datapoint_id} from {url} (timeout={timeout}s)"
        )

        try:
            async with asyncio.timeout(timeout):
                async with self._session.get(url, headers=headers) as response:
                    if response.status == 401:
                        _LOGGER.debug(f"Session expired when fetching datapoint {datapoint_id}")
                        return None

                    if response.status == 404:
                        _LOGGER.debug(f"Datapoint {datapoint_id} not found")
                        return None

                    if response.status != 200:
                        _LOGGER.debug(
                            f"Failed to fetch datapoint {datapoint_id}: {response.status}"
                        )
                        return None

                    datapoint = cast(Optional[dict], await response.json())
                    _LOGGER.info(f"📁 Datapoint {datapoint_id} response: {datapoint}")
                    return datapoint

        except asyncio.TimeoutError:
            _LOGGER.debug(f"Timeout fetching datapoint {datapoint_id} after {timeout}s")
            return None
        except aiohttp.ClientError as e:
            _LOGGER.debug(f"Network error fetching datapoint {datapoint_id}: {e}")
            return None

    # NOT CALLED BY INTEGRATION — reserved for future datapoint polling (superseded by knxprod static lookup)
    async def async_get_datapoint_value(
        self, datapoint_id: int, timeout: float = 2.0
    ) -> Optional[Any]:
        """
        Get current value of a specific BAOS datapoint.

        Per BAOS REST API Documentation:
        GET /rest/datapoint/<id>

        Returns:
        {
            "id": 1,
            "name": "1/0/0",
            "value": true,
            "type": "DPT-1"
        }

        Args:
            datapoint_id: BAOS datapoint ID (integer)
            timeout: Request timeout in seconds (default: 2.0)

        Returns:
            Datapoint value, or None on error
        """
        self._ensure_authenticated()
        assert self._session is not None

        url = f"{self.base_url}/rest/datapoint/{datapoint_id}"
        headers = self._get_auth_headers()

        _LOGGER.debug(f"🔍 Fetching datapoint {datapoint_id} from {url} (timeout={timeout}s)")

        try:
            async with asyncio.timeout(timeout):
                async with self._session.get(url, headers=headers) as response:
                    if response.status == 401:
                        _LOGGER.error(f"Session expired when fetching datapoint {datapoint_id}")
                        return None

                    if response.status == 404:
                        _LOGGER.warning(f"Datapoint {datapoint_id} not found")
                        return None

                    if response.status != 200:
                        response_text = await response.text()
                        _LOGGER.error(
                            f"Failed to fetch datapoint {datapoint_id}: {response.status} - {response_text}"
                        )
                        return None

                    datapoint = await response.json()
                    value = datapoint.get("value")
                    _LOGGER.debug(f"Datapoint {datapoint_id} value: {value}")
                    return value

        except asyncio.TimeoutError:
            _LOGGER.warning(f"Timeout fetching datapoint {datapoint_id} after {timeout}s")
            return None
        except aiohttp.ClientError as e:
            _LOGGER.warning(f"Client error fetching datapoint {datapoint_id}: {e}")
            return None
        except Exception as e:
            _LOGGER.error(
                f"💥 Unexpected error fetching datapoint {datapoint_id}: {e}", exc_info=True
            )
            return None

    def _ensure_authenticated(self):
        """Raise AuthenticationError if not logged in."""
        if not self.session_token:
            raise AuthenticationError("Not logged in. Call login() first.")

        # Check session expiry
        if self.session_expires and datetime.now() >= self.session_expires:
            raise AuthenticationError("Session expired. Please login again.")

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers per BAOS REST API Documentation (Page 7).

        Two supported methods:
        1. Cookie: user=%22TOKEN%22 (where %22 is URL-encoded double quote)
        2. Authorization: Token token=TOKEN (note "Token" prefix!)
        """
        if not self.session_token:
            return {}

        # URL-encode the cookie value: user="TOKEN" → user=%22TOKEN%22
        import urllib.parse

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
    def get_diagnostics(self) -> Dict[str, Any]:
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


# Example usage
async def main():
    """Show example usage of BAOSRestClient.

    NOTE: This example uses default credentials for demonstration only.
    In production (Home Assistant integration), credentials are:
    - Entered by users via the configuration UI
    - Stored securely in Home Assistant's encrypted config entry
    - Retrieved at runtime from the config entry
    See config_flow.py and __init__.py for the actual credential handling.
    """
    async with BAOSRestClient("192.168.1.3") as client:
        # Login with example credentials (NOT used in production)
        await client.login("admin", "admin")
        print(f"✅ Logged in. Token: {client.session_token[:20]}...")

        # Enable tunneling
        await client.enable_tunneling()
        print("✅ Tunneling enabled")

        # Check status
        status = await client.get_tunneling_status()
        print(f"📊 Tunneling status: {status}")

        # Diagnostics
        diag = client.get_diagnostics()
        print(f"🔍 Diagnostics: {diag}")

        # Logout (auto-disables tunneling)
        await client.logout()
        print("✅ Logged out (tunneling auto-disabled)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
