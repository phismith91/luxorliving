"""DataUpdateCoordinator for Theben LUXORliving."""
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import LuxorLivingApi, LuxorLivingApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class LuxorLivingCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching LUXORliving data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: LuxorLivingApi,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator.
        
        Args:
            hass: Home Assistant instance
            api: LUXORliving API client
            update_interval: Update interval
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from LUXORliving API.
        
        Returns:
            Dictionary with device data
            
        Raises:
            UpdateFailed: If update fails
        """
        try:
            _LOGGER.debug("Updating LUXORliving data")
            
            # Fetch device data
            devices = await self.api.get_devices()
            
            # Fetch system status
            status = await self.api.get_status()
            
            return {
                "devices": devices,
                "status": status,
            }
            
        except LuxorLivingApiError as err:
            _LOGGER.error("Error fetching LUXORliving data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
