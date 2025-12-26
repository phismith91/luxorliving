"""Data coordinator for LUXORliving integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)


class LuxorLivingCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data coordinator for LUXORliving integration.

    Handles periodic updates from the KNX gateway and provides
    a single source of truth for all entities.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        gateway: LuxorKNXGateway,
        scan_interval: int = 30,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            gateway: LuxorKNXGateway instance
            scan_interval: Update interval in seconds (default: 30)
        """
        super().__init__(
            hass,
            _LOGGER,
            name="Luxor Living",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.gateway = gateway
        self._state_cache: dict[str, Any] = {}
        self._scan_interval = scan_interval

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the KNX gateway.

        Returns:
            Dictionary containing current state of all entities

        Raises:
            UpdateFailed: If data cannot be fetched
        """
        try:
            # Fetch current state of all known group addresses
            state_updates: dict[str, Any] = {}

            # For now, coordinator just returns an empty cache
            # Real state updates come from KNX telegrams via listeners
            # The coordinator is a placeholder for future polling implementation
            # when Home Assistant adds group read request support to XKNX

            # Update cache
            self._state_cache.update(state_updates)

            return self._state_cache

        except Exception as err:
            _LOGGER.error("Error updating LUXORliving data: %s", err)
            raise UpdateFailed(f"Error fetching LUXORliving data: {err}") from err

    def get_state(self, address: str) -> Any:
        """Get cached state for a group address.

        Args:
            address: Group address (e.g., "1/2/3")

        Returns:
            Cached state value or None
        """
        return self._state_cache.get(address)

    def set_state(self, address: str, value: Any) -> None:
        """Update cached state for a group address.

        Args:
            address: Group address (e.g., "1/2/3")
            value: New state value
        """
        self._state_cache[address] = value
        self.async_set_updated_data(self._state_cache)
