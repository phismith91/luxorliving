"""Light platform for Theben LUXORliving."""
import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LuxorLivingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving light entities.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: LuxorLivingCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Parse devices from coordinator data
    entities = []
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data.get("devices", {})
        
        # This is a placeholder - adjust based on actual API response structure
        for device_id, device_data in devices.items():
            if device_data.get("type") == "light":
                entities.append(
                    LuxorLivingLight(coordinator, entry, device_id, device_data)
                )
    
    async_add_entities(entities)
    _LOGGER.debug("Added %d light entities", len(entities))


class LuxorLivingLight(CoordinatorEntity[LuxorLivingCoordinator], LightEntity):
    """Representation of a LUXORliving light."""

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        entry: ConfigEntry,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the light.
        
        Args:
            coordinator: Data update coordinator
            entry: Config entry
            device_id: Device identifier
            device_data: Device data from API
        """
        super().__init__(coordinator)
        
        self._device_id = device_id
        self._attr_unique_id = f"{entry.entry_id}_{device_id}"
        self._attr_name = device_data.get("name", f"Light {device_id}")
        self._attr_has_entity_name = True
        
        # Set device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": self._attr_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }
        
        # Determine supported color modes
        if device_data.get("dimmable", False):
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        if self.coordinator.data and "devices" in self.coordinator.data:
            device = self.coordinator.data["devices"].get(self._device_id, {})
            return device.get("state", False)
        return False

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        if self.coordinator.data and "devices" in self.coordinator.data:
            device = self.coordinator.data["devices"].get(self._device_id, {})
            if "brightness" in device:
                # Convert from 0-100 to 0-255
                return int(device["brightness"] * 255 / 100)
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light.
        
        Args:
            **kwargs: Additional arguments
        """
        brightness = None
        if ATTR_BRIGHTNESS in kwargs:
            # Convert from 0-255 to 0-100
            brightness = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
        
        await self.coordinator.api.set_device_state(
            device_id=self._device_id,
            state=True,
            brightness=brightness,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light.
        
        Args:
            **kwargs: Additional arguments
        """
        await self.coordinator.api.set_device_state(
            device_id=self._device_id,
            state=False,
        )
        await self.coordinator.async_request_refresh()
