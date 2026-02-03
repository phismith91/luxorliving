"""REST API Client Datapoint Operations."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, cast

import aiohttp

if TYPE_CHECKING:
    from .rest_client import BAOSRestClient

_LOGGER = logging.getLogger(__name__)


class DatapointOperationsMixin:
    """Mixin for datapoint operations (get datapoints, details, values)."""

    async def async_get_datapoints(self: "BAOSRestClient") -> Optional[list]:
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

    async def async_get_datapoint_details(
        self: "BAOSRestClient", datapoint_id: int, timeout: float = 2.0
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

    async def async_get_datapoint_value(
        self: "BAOSRestClient", datapoint_id: int, timeout: float = 2.0
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
