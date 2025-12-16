"""Sensor platform for Theben LUXORliving."""
import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
    """Set up LUXORliving sensor entities.
    
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
            if device_data.get("type") == "sensor":
                entities.append(
                    LuxorLivingSensor(coordinator, entry, device_id, device_data)
                )
    
    async_add_entities(entities)
    _LOGGER.debug("Added %d sensor entities", len(entities))


class LuxorLivingSensor(CoordinatorEntity[LuxorLivingCoordinator], SensorEntity):
    """Representation of a LUXORliving sensor."""

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        entry: ConfigEntry,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor.
        
        Args:
            coordinator: Data update coordinator
            entry: Config entry
            device_id: Device identifier
            device_data: Device data from API
        """
        super().__init__(coordinator)
        
        self._device_id = device_id
        self._attr_unique_id = f"{entry.entry_id}_{device_id}"
        self._attr_name = device_data.get("name", f"Sensor {device_id}")
        self._attr_has_entity_name = True
        
        # Set device class and unit based on sensor type
        sensor_type = device_data.get("sensor_type", "generic")
        if sensor_type == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif sensor_type == "humidity":
            self._attr_device_class = SensorDeviceClass.HUMIDITY
            self._attr_native_unit_of_measurement = "%"
        elif sensor_type == "illuminance":
            self._attr_device_class = SensorDeviceClass.ILLUMINANCE
            self._attr_native_unit_of_measurement = "lx"
        
        # Set device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": self._attr_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "devices" in self.coordinator.data:
            device = self.coordinator.data["devices"].get(self._device_id, {})
            return device.get("value")
        return None
