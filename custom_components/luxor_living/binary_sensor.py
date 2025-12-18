"""Binary sensor platform for LUXORliving integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity_mapper import EntityMapper

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving binary sensors from a config entry."""
    _LOGGER.info("Setting up LUXORliving binary sensors")
    
    # Get mapper from integration data
    mapper: EntityMapper = hass.data[DOMAIN][entry.entry_id].get("mapper")
    
    if not mapper:
        _LOGGER.warning("No mapper found, skipping binary sensor setup")
        return
    
    # Get all binary sensor entities
    sensor_entities = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
    _LOGGER.info("Creating %d binary sensor entities", len(sensor_entities))
    
    entities = []
    for mapped_entity in sensor_entities:
        entity = LuxorLivingBinarySensor(mapped_entity)
        entities.append(entity)
    
    async_add_entities(entities)


class LuxorLivingBinarySensor(BinarySensorEntity):
    """Representation of a LUXORliving binary sensor."""

    _attr_has_entity_name = True

    def __init__(self, mapped_entity: Any) -> None:
        """Initialize the binary sensor."""
        self._mapped = mapped_entity
        self._attr_unique_id = mapped_entity.unique_id
        self._attr_name = mapped_entity.name
        self._attr_is_on = False
        
        # Determine device class based on entity type
        if mapped_entity.entity_type == "motion":
            self._attr_device_class = BinarySensorDeviceClass.MOTION
        elif "rauchmelder" in mapped_entity.name.lower():
            self._attr_device_class = BinarySensorDeviceClass.SMOKE
        elif "fenster" in mapped_entity.name.lower() or "tür" in mapped_entity.name.lower():
            self._attr_device_class = BinarySensorDeviceClass.OPENING
        else:
            self._attr_device_class = None
        
        # Store datapoint addresses
        self._address_status = (
            mapped_entity.datapoints.get("status@OnOff")
            or mapped_entity.datapoints.get("OnOff")
            or mapped_entity.datapoints.get("SchaltenOnOff")
        )
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mapped_entity.device_id)},
            "name": mapped_entity.device_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        return {
            "knx_address": self._address_status,
            "sensor_type": self._mapped.attributes.get("sensor_type"),
        }
