"""API client for Theben LUXORliving."""
import asyncio
import logging
from typing import Any

import aiohttp

from .const import (
    API_ENDPOINT_CONTROL,
    API_ENDPOINT_DEVICES,
    API_ENDPOINT_STATUS,
    DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class LuxorLivingApiError(Exception):
    """Base exception for LUXORliving API errors."""


class LuxorLivingConnectionError(LuxorLivingApiError):
    """Exception for connection errors."""


class LuxorLivingAuthenticationError(LuxorLivingApiError):
    """Exception for authentication errors."""


class LuxorLivingApi:
    """API client for Theben LUXORliving system."""

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the API client.
        
        Args:
            host: The hostname or IP address of the LUXORliving system
            port: The port number
            session: aiohttp client session
            timeout: Request timeout in seconds
        """
        self._host = host
        self._port = port
        self._session = session
        self._timeout = timeout
        self._base_url = f"http://{host}:{port}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Optional data to send
            
        Returns:
            API response as dictionary
            
        Raises:
            LuxorLivingConnectionError: If connection fails
            LuxorLivingApiError: If API returns an error
        """
        url = f"{self._base_url}{endpoint}"
        
        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.request(
                    method,
                    url,
                    json=data,
                ) as response:
                    response.raise_for_status()
                    return await response.json()
                    
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout connecting to LUXORliving at %s", url)
            raise LuxorLivingConnectionError(
                f"Timeout connecting to {url}"
            ) from err
            
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to LUXORliving at %s: %s", url, err)
            raise LuxorLivingConnectionError(
                f"Error connecting to {url}: {err}"
            ) from err
            
        except Exception as err:
            _LOGGER.error("Unexpected error communicating with LUXORliving: %s", err)
            raise LuxorLivingApiError(
                f"Unexpected error: {err}"
            ) from err

    async def test_connection(self) -> bool:
        """Test the connection to the LUXORliving system.
        
        Returns:
            True if connection is successful
            
        Raises:
            LuxorLivingConnectionError: If connection fails
        """
        try:
            await self._request("GET", API_ENDPOINT_STATUS)
            _LOGGER.debug("Successfully connected to LUXORliving at %s", self._base_url)
            return True
        except LuxorLivingConnectionError:
            _LOGGER.error("Failed to connect to LUXORliving at %s", self._base_url)
            raise

    async def get_devices(self) -> dict[str, Any]:
        """Get all devices from the LUXORliving system.
        
        Returns:
            Dictionary with device information
        """
        _LOGGER.debug("Fetching devices from LUXORliving")
        return await self._request("GET", API_ENDPOINT_DEVICES)

    async def get_status(self) -> dict[str, Any]:
        """Get system status from the LUXORliving system.
        
        Returns:
            Dictionary with system status
        """
        _LOGGER.debug("Fetching status from LUXORliving")
        return await self._request("GET", API_ENDPOINT_STATUS)

    async def set_device_state(
        self,
        device_id: str,
        state: bool,
        brightness: int | None = None,
    ) -> dict[str, Any]:
        """Set device state.
        
        Args:
            device_id: The device identifier
            state: On/off state
            brightness: Optional brightness level (0-100)
            
        Returns:
            API response
        """
        data = {
            "device_id": device_id,
            "state": state,
        }
        
        if brightness is not None:
            data["brightness"] = brightness
            
        _LOGGER.debug("Setting device %s state to %s", device_id, state)
        return await self._request("POST", API_ENDPOINT_CONTROL, data)
