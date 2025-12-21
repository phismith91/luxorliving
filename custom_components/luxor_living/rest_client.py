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
    
    def __init__(self, host: str, port: int = 80):
        """
        Initialize REST API Client.
        
        Args:
            host: IP address of BAOS 777 device
            port: HTTP port (default: 80, per LUXORliving API docs)
        """
        self.host = host
        self.port = port
        # Use HTTP as documented, SSL context handles HTTPS redirects
        self.base_url = f"http://{host}:{port}"
        
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
                    raise AuthenticationError(
                        f"Login failed with status {response.status}"
                    )
                
                # Response is a plain cookie string, not JSON
                cookie = await response.text()
                cookie = cookie.strip()
                
                if not cookie:
                    raise AuthenticationError("No session cookie in response")
                
                self.session_token = cookie
                
                # Session timeout: 1 hour (API doesn't send expiresIn in plain cookie response)
                timeout_seconds = 3600
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
        _LOGGER.debug(f"Tunneling headers: {headers}")
        _LOGGER.debug(f"Session token: {self.session_token[:10]}..." if self.session_token else "No token")
        
        try:
            async with self._session.put(
                url, 
                json=payload, 
                headers=headers
            ) as response:
                _LOGGER.debug(f"Tunneling response status: {response.status}")
                _LOGGER.debug(f"Tunneling response headers: {response.headers}")
                
                if response.status == 401:
                    raise AuthenticationError("Session expired or invalid")
                
                if response.status == 403:
                    response_text = await response.text()
                    _LOGGER.error(f"403 Forbidden when enabling tunneling. Response: {response_text}")
                    raise TunnelingError(
                        f"Failed to enable tunneling: Forbidden (403). Check API permissions."
                    )
                
                # API Documentation Page 12: PUT /rest/device/authtunneling returns 204, not 200!
                if response.status not in (200, 204):
                    response_text = await response.text()
                    _LOGGER.error(f"Tunneling failed with {response.status}. Response: {response_text}")
                    raise TunnelingError(
                        f"Failed to enable tunneling (status {response.status})"
                    )
                
                # Success! With 204 (No Content) there's no response body
                if response.status == 204:
                    self.tunneling_enabled = True
                    _LOGGER.info("✅ KNX Tunneling enabled successfully (204 No Content)")
                    return True
                
                # With 200, verify from response body
                data = await response.json()
                self.tunneling_enabled = data.get("enabled", True)
                _LOGGER.info("✅ KNX Tunneling enabled successfully (200 OK)")
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
                if response.status in (200, 204):
                    self.tunneling_enabled = False
                    _LOGGER.info(f"KNX Tunneling disabled ({response.status})")
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
                    _LOGGER.error(f"Failed to fetch datapoints: {response.status} - {response_text}")
                    return None
                
                response_data = await response.json()
                
                # BAOS API returns {"datapoints": [{"id": 1, "url": "..."}]}
                if isinstance(response_data, dict) and "datapoints" in response_data:
                    datapoints = response_data["datapoints"]
                    _LOGGER.info(f"✅ Fetched {len(datapoints)} datapoint references from BAOS")
                    _LOGGER.debug(f"🔍 First 3 datapoints: {datapoints[:3]}")
                    return datapoints
                else:
                    _LOGGER.error(f"Unexpected API format: {type(response_data)}")
                    _LOGGER.debug(f"Response data: {response_data}")
                    return None
        
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Network error fetching datapoints: {e}")
            return None
    
    async def async_get_datapoint_value(self, datapoint_id: int, timeout: float = 2.0) -> Optional[Any]:
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
                        _LOGGER.error(f"Failed to fetch datapoint {datapoint_id}: {response.status} - {response_text}")
                        return None
                    
                    datapoint = await response.json()
                    value = datapoint.get("value")
                    _LOGGER.info(f"✅ Datapoint {datapoint_id} value: {value}")
                    return value
        
        except asyncio.TimeoutError:
            _LOGGER.warning(f"⏱️ Timeout fetching datapoint {datapoint_id} after {timeout}s")
            return None
        except aiohttp.ClientError as e:
            _LOGGER.warning(f"❌ Client error fetching datapoint {datapoint_id}: {e}")
            return None
        except Exception as e:
            _LOGGER.error(f"💥 Unexpected error fetching datapoint {datapoint_id}: {e}", exc_info=True)
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
            "Authorization": f"Token token={self.session_token}"
        }
        
        _LOGGER.debug(f"Auth headers: Cookie=user=%22...%22, Authorization=Token token=...")
        return headers
    
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
