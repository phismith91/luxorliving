"""Base entity for LUXORliving integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import LuxorLivingCoordinator
from .entity_mapper import MappedEntity

_LOGGER = logging.getLogger(__name__)


class LuxorLivingEntity(Entity):
    """Base entity for LUXORliving integration.

    Provides common functionality for all LUXORliving entities:
    - Device registry integration
    - Coordinator listener management
    - State synchronization
    """

    _attr_has_entity_name: bool = True

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        config_entry: ConfigEntry,
        mapped_entity: MappedEntity,
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: Data coordinator instance
            config_entry: Config entry for this integration
            mapped_entity: MappedEntity object containing entity information
        """
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._mapped_entity = mapped_entity
        # Use the unique_id from MappedEntity which is already guaranteed to be unique
        self._attr_unique_id: str = getattr(mapped_entity, "unique_id", "unknown")
        self._attr_translation_key: str | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this entity's device.

        Returns:
            DeviceInfo for the LXP device this entity belongs to.
            Creates individual devices for S16, B6, iON4, etc.
        """
        # Get device name and ID from the mapped entity
        device_name = getattr(self._mapped_entity, "device_name", "Unknown Device")
        device_id = getattr(self._mapped_entity, "device_id", "unknown")
        
        # Use device_id as the unique identifier (e.g., "_92a56b99254740dcbceaa3db595863b9" for S16-1)
        # This creates separate Home Assistant devices for each LXP device
        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="Theben",
            model="LUXORliving",
            hw_version="1.0",
            sw_version="1.0",
        )

    @property
    def name(self) -> str:
        """Return entity name."""
        return getattr(self._mapped_entity, "name", "Unknown")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant.

        Set up coordinator listener for data updates.
        """
        await super().async_added_to_hass()

        # Subscribe to coordinator updates
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

        # If coordinator hasn't fetched yet, do it now
        if self.coordinator.last_update_success is False:
            await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the entity state.

        Called by Home Assistant when needed. We use coordinator updates instead,
        but this ensures compatibility with manual refresh requests.
        """
        await self.coordinator.async_request_refresh()
