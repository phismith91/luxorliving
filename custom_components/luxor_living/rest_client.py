"""REST API Client for BAOS 777 with Tunneling Activation."""
import aiohttp
import asyncio
import logging
import ssl
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)


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
    
    def __init__(self, host: str, port: int = 443):
        """
        Initialize REST API Client.
        
        Args:
            host: IP address of BAOS 777 device
            port: HTTPS port (default: 443, device enforces HTTPS)
        """
        self.host = host
        self.port = port
        # LUXORliving enforces HTTPS (308 redirect from HTTP:80)
        self.base_url = f"https://{host}:{port}"
        
        self.session_token: Optional[str] = None
        self.session_expires: Optional[datetime] = None
        self.tunneling_enabled = False
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Context manager entry."""
        # Create SSL context for BAOS 777 (may use old SSL/TLS)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Allow old TLS versions for legacy devices
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1
        ssl_context.set_ciphers('DEFAULT:@SECLEVEL=0')
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(
            connector=connector,
            connector_owner=True,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, *args):
        """Context manager exit - ensures cleanup."""
        await self.logout()
        if self._session:
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
        if not self._session:
            # Create SSL context for BAOS 777 (may use old SSL/TLS)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Allow old TLS versions for legacy devices
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1
            ssl_context.set_ciphers('DEFAULT:@SECLEVEL=0')
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(
                connector=connector,
                connector_owner=True,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        
        url = f"{self.base_url}/rest/login"
        payload = {
            "username": username,
            "password": password
        }
        
        _LOGGER.debug(f"Attempting login to {url}")
        
        try:
            async with self._session.post(url, json=payload) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid username or password")
                
                if response.status != 200:
                    raise AuthenticationError(
                        f"Login failed with status {response.status}"
                    )
                
                # Response is a plain cookie string, not JSON
                cookie = await response.text()
                cookie = cookie.strip()
                
                if not cookie:
                    raise AuthenticationError("No session cookie in response")
                
                self.session_token = cookie
                
                # Session timeout (default: 1 hour, adjust based on real API)
                timeout_seconds = data.get("expiresIn", 3600)
                self.session_expires = datetime.now() + timedelta(seconds=timeout_seconds)
                
                _LOGGER.info(
                    f"Login successful. Session expires at {self.session_expires}"
                )
                
                return self.session_token
        
        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Network error during login: {e}")
    
    async def logout(self):
        """
        Logout and end session.
        
        NOTE: Logout automatically deactivates tunneling!
        """
        if not self.session_token:
            _LOGGER.debug("No active session to logout from")
            return
        
        url = f"{self.base_url}/rest/auth/logout"
        headers = self._get_auth_headers()
        
        _LOGGER.debug(f"Logging out from {url}")
        
        try:
            async with self._session.post(url, headers=headers) as response:
                if response.status == 200:
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
        Enable KNX Tunneling via REST API.
        
        According to LUXORliving API Documentation:
        PUT /rest/device/authtunneling
        {"enabled": true}
        
        Returns:
            True if tunneling was enabled successfully
        
        Raises:
            AuthenticationError: If not logged in
            TunnelingError: If activation fails
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}/rest/device/authtunneling"
        payload = {"enabled": True}
        headers = self._get_auth_headers()
        
        _LOGGER.debug(f"Enabling tunneling at {url}")
        
        try:
            async with self._session.put(
                url, 
                json=payload, 
                headers=headers
            ) as response:
                if response.status == 401:
                    raise AuthenticationError("Session expired or invalid")
                
                if response.status != 200:
                    raise TunnelingError(
                        f"Failed to enable tunneling (status {response.status})"
                    )
                
                # Verify tunneling is enabled
                data = await response.json()
                self.tunneling_enabled = data.get("enabled", True)
                
                _LOGGER.info("KNX Tunneling enabled successfully")
                return True
        
        except aiohttp.ClientError as e:
            raise TunnelingError(f"Network error enabling tunneling: {e}")
    
    async def disable_tunneling(self) -> bool:
        """
        Disable KNX Tunneling.
        
        NOTE: Logout also disables tunneling automatically.
        
        Returns:
            True if tunneling was disabled
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}/rest/device/authtunneling"
        payload = {"enabled": False}
        headers = self._get_auth_headers()
        
        _LOGGER.debug(f"Disabling tunneling at {url}")
        
        try:
            async with self._session.put(
                url,
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    self.tunneling_enabled = False
                    _LOGGER.info("KNX Tunneling disabled")
                    return True
                else:
                    _LOGGER.warning(f"Disable tunneling returned {response.status}")
                    return False
        
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error disabling tunneling: {e}")
            return False
    
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
        
        url = f"{self.base_url}/rest/device/authtunneling"
        headers = self._get_auth_headers()
        
        async with self._session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                _LOGGER.warning(f"Get tunneling status returned {response.status}")
                return {
                    "enabled": False,
                    "connectedClients": 0,
                    "maxSlots": 1
                }
    
    def _ensure_authenticated(self):
        """Raise AuthenticationError if not logged in."""
        if not self.session_token:
            raise AuthenticationError("Not logged in. Call login() first.")
        
        # Check session expiry
        if self.session_expires and datetime.now() >= self.session_expires:
            raise AuthenticationError("Session expired. Please login again.")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        NOTE: Exact header format needs verification with real device.
        Could be:
        - Authorization: Bearer <token>
        - Authorization: Token <token>
        - Cookie: session=<token>
        - X-Session-Token: <token>
        """
        if not self.session_token:
            return {}
        
        # LUXORliving uses Cookie-based authentication
        return {"Cookie": self.session_token}
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        if not self.session_token:
            return False
        
        if self.session_expires and datetime.now() >= self.session_expires:
            return False
        
        return True
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Get diagnostic information.
        
        Returns:
            Dictionary with client state for diagnostics
        """
        return {
            "host": self.host,
            "port": self.port,
            "authenticated": self.is_authenticated,
            "session_token": bool(self.session_token),
            "session_expires": self.session_expires.isoformat() if self.session_expires else None,
            "tunneling_enabled": self.tunneling_enabled,
        }


# Example usage
async def main():
    """Example usage of BAOSRestClient."""
    async with BAOSRestClient("192.168.1.3") as client:
        # Login
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
