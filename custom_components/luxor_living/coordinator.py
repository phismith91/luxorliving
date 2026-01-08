"""Data coordinator for LUXORliving integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .knx_gateway import LuxorKNXGateway
from .rest_client import AuthenticationError

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

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
        entry: ConfigEntry,
        scan_interval: int = 30,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            gateway: LuxorKNXGateway instance
            entry: Config entry for this integration
            scan_interval: Update interval in seconds (default: 30)
        """
        super().__init__(
            hass,
            _LOGGER,
            name="Luxor Living",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.gateway = gateway
        self.entry = entry
        self._state_cache: dict[str, Any] = {}
        self._scan_interval = scan_interval
        self._auth_failures = 0

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the KNX gateway.

        This method is required to be async by the DataUpdateCoordinator base class,
        even though it currently doesn't perform any async operations.

        Currently, state updates come from KNX telegrams via listeners in the gateway,
        not from polling. This method serves as a placeholder for future polling
        implementation when batch read requests are supported.

        Returns:
            Dictionary containing current state of all entities

        Raises:
            UpdateFailed: If data cannot be fetched
        """
        try:
            # Fetch current state of all known group addresses
            state_updates: dict[str, Any] = {}

            # For now, coordinator just returns the existing cache
            # Real state updates come from KNX telegrams via listeners
            # The coordinator is a placeholder for future polling implementation
            # when Home Assistant adds group read request support to XKNX

            # Update cache
            self._state_cache.update(state_updates)

            # Reset auth failure counter on successful update
            self._auth_failures = 0

            return self._state_cache

        except AuthenticationError as err:
            self._auth_failures += 1
            _LOGGER.warning(
                "Authentication error during update (attempt %d): %s",
                self._auth_failures,
                err,
            )

            # Trigger re-authentication flow after 3 consecutive failures
            if self._auth_failures >= 3:
                _LOGGER.error("Multiple authentication failures, creating repair issue")
                from .repairs import create_auth_repair_issue

                await create_auth_repair_issue(self.hass, self.entry, str(err))

            raise UpdateFailed(f"Authentication error: {err}") from err

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
