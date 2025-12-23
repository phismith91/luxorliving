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
        mapped_entity: dict[str, Any],
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: Data coordinator instance
            config_entry: Config entry for this integration
            mapped_entity: Entity mapping dictionary containing:
                - name: Entity name
                - room: Room name
                - function: Function name
                - group_address: KNX group address
                - dpt: Data Point Type
        """
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._mapped_entity = mapped_entity
        self._attr_unique_id: str = self._create_unique_id(mapped_entity)
        self._attr_translation_key: str | None = None

    def _create_unique_id(self, mapped_entity: dict[str, Any]) -> str:
        """Create unique ID for this entity.

        Args:
            mapped_entity: Entity mapping dictionary

        Returns:
            Unique ID combining device identifier and entity name
        """
        device_id = self._config_entry.entry_id
        room = mapped_entity.get("room", "unknown")
        function = mapped_entity.get("function", "unknown")
        name = mapped_entity.get("name", "unknown")

        return f"{DOMAIN}_{device_id}_{room}_{function}_{name}".replace(" ", "_").lower()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for the gateway.

        Returns:
            DeviceInfo for BAOS 777 gateway
        """
        host = self._config_entry.data.get(CONF_HOST, "unknown")

        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="Luxor Living Gateway",
            manufacturer="Theben",
            model="BAOS 777",
            hw_version="1.0",
            sw_version="7.x",
            configuration_url=f"http://{host}:80",
        )

    @property
    def name(self) -> str:
        """Return entity name."""
        return self._mapped_entity.get("name", "Unknown")

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
