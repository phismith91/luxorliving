"""Switch platform for Theben LUXORliving."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up LUXORliving switch entities.
    
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
            if device_data.get("type") == "switch":
                entities.append(
                    LuxorLivingSwitch(coordinator, entry, device_id, device_data)
                )
    
    async_add_entities(entities)
    _LOGGER.debug("Added %d switch entities", len(entities))


class LuxorLivingSwitch(CoordinatorEntity[LuxorLivingCoordinator], SwitchEntity):
    """Representation of a LUXORliving switch."""

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        entry: ConfigEntry,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the switch.
        
        Args:
            coordinator: Data update coordinator
            entry: Config entry
            device_id: Device identifier
            device_data: Device data from API
        """
        super().__init__(coordinator)
        
        self._device_id = device_id
        self._attr_unique_id = f"{entry.entry_id}_{device_id}"
        self._attr_name = device_data.get("name", f"Switch {device_id}")
        
        # Set device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": self._attr_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        if self.coordinator.data and "devices" in self.coordinator.data:
            device = self.coordinator.data["devices"].get(self._device_id, {})
            return device.get("state", False)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch.
        
        Args:
            **kwargs: Additional arguments
        """
        await self.coordinator.api.set_device_state(
            device_id=self._device_id,
            state=True,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch.
        
        Args:
            **kwargs: Additional arguments
        """
        await self.coordinator.api.set_device_state(
            device_id=self._device_id,
            state=False,
        )
        await self.coordinator.async_request_refresh()
