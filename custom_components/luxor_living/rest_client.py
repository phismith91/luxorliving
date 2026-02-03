"""REST API Client for BAOS 777 with Tunneling Activation."""

from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any, Dict, Optional

import aiohttp

from .rest_datapoints import DatapointOperationsMixin
from .rest_exceptions import AuthenticationError, TunnelingError
from .rest_session import SessionManagementMixin
from .rest_tunneling import TunnelingManagementMixin

_LOGGER = logging.getLogger(__name__)


class BAOSRestClient(SessionManagementMixin, TunnelingManagementMixin, DatapointOperationsMixin):
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

    def __init__(self, host: str, port: int = 443, use_https: bool = True):
        """
        Initialize REST API Client.

        Args:
            host: IP address of BAOS 777 device
            port: Port for REST API (default: 443 for HTTPS)
            use_https: Use HTTPS for secure communication (default: True, recommended)
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

        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Context manager entry."""

        # Create SSL context in executor to avoid blocking event loop
        def create_ssl_context():
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.set_ciphers("DEFAULT:@SECLEVEL=0")
            return ssl_context

        import asyncio

        loop = asyncio.get_event_loop()
        ssl_context = await loop.run_in_executor(None, create_ssl_context)

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(
            connector=connector, connector_owner=True, timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, *args):
        """Context manager exit - ensures cleanup."""
        await self.logout()
        if self._session:
            await self._session.close()

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
