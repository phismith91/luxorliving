"""REST API Client Session Management."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, Optional

import aiohttp

from .rest_exceptions import AuthenticationError

if TYPE_CHECKING:
    from .rest_client import BAOSRestClient

_LOGGER = logging.getLogger(__name__)


class SessionManagementMixin:
    """Mixin for session management (login, logout, authentication)."""

    async def login(self: "BAOSRestClient", username: str, password: str) -> str:
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
        if not self._session:
            # Create SSL context in executor to avoid blocking event loop
            def create_ssl_context():
                import ssl

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                # TLS 1.2+ for security (legacy devices may need fallback)
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

        url = f"{self.base_url}/rest/login"
        payload = {"username": username, "password": password}

        _LOGGER.debug(f"Attempting login to {url} with payload: {payload}")

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

                # Session timeout: 1 hour (API doesn't send expiresIn in plain cookie response)
                timeout_seconds = 3600
                self.session_expires = datetime.now() + timedelta(seconds=timeout_seconds)

                _LOGGER.info(f"Login successful. Session expires at {self.session_expires}")

                # mypy: ensure return value is str (we validated cookie above)
                assert self.session_token is not None
                return self.session_token

        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Network error during login: {e}")

    async def logout(self: "BAOSRestClient"):
        """
        Logout and end session.

        NOTE: Logout automatically deactivates tunneling!
        """
        if not self.session_token:
            _LOGGER.debug("No active session to logout from")
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

    def _ensure_authenticated(self: "BAOSRestClient"):
        """Raise AuthenticationError if not logged in."""
        if not self.session_token:
            raise AuthenticationError("Not logged in. Call login() first.")

        # Check session expiry
        if self.session_expires and datetime.now() >= self.session_expires:
            raise AuthenticationError("Session expired. Please login again.")

    def _get_auth_headers(self: "BAOSRestClient") -> Dict[str, str]:
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
    def is_authenticated(self: "BAOSRestClient") -> bool:
        """Check if client is authenticated."""
        if not self.session_token:
            return False

        if self.session_expires and datetime.now() >= self.session_expires:
            return False

        return True
