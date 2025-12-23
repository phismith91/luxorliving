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

from .coordinator import LuxorLivingCoordinator
from .entity import LuxorLivingEntity
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
    
    # Get coordinator and mapper from integration data
    coordinator: LuxorLivingCoordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
    mapper: EntityMapper = hass.data[DOMAIN][entry.entry_id].get("mapper")
    
    if not mapper:
        _LOGGER.warning("No mapper found, skipping binary sensor setup")
        return
    
    if not coordinator:
        _LOGGER.error("No coordinator found, skipping binary sensor setup")
        return
    
    # Get all binary sensor entities
    sensor_entities = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
    _LOGGER.info("Creating %d binary sensor entities", len(sensor_entities))
    
    entities: list[BinarySensorEntity] = []
    for mapped_entity in sensor_entities:
        entity = LuxorLivingBinarySensor(coordinator, entry, mapped_entity)
        entities.append(entity)
    
    async_add_entities(entities)


class LuxorLivingBinarySensor(LuxorLivingEntity, BinarySensorEntity):
    """Representation of a LUXORliving binary sensor."""

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        entry: ConfigEntry,
        mapped_entity: Any,
    ) -> None:
        """Initialize the binary sensor.
        
        Args:
            coordinator: Data coordinator instance
            entry: Config entry for this integration
            mapped_entity: Mapped entity data from LXP file
        """
        super().__init__(coordinator, entry, mapped_entity)
        
        self._attr_is_on = False
        
        # Determine device class based on entity type and name
        self._attr_device_class = self._detect_device_class(mapped_entity)
        
        # Store datapoint addresses
        self._address_status: str | None = (
            mapped_entity.datapoints.get("status@OnOff")
            or mapped_entity.datapoints.get("OnOff")
            or mapped_entity.datapoints.get("SchaltenOnOff")
        )
        
        _LOGGER.debug(
            "📊 Binary Sensor '%s' (class: %s) status address: %s",
            self.name,
            self._attr_device_class,
            self._address_status,
        )

    def _detect_device_class(self, mapped_entity: Any) -> BinarySensorDeviceClass | None:
        """Detect the device class based on entity type and name.
        
        Args:
            mapped_entity: Mapped entity data
            
        Returns:
            BinarySensorDeviceClass or None
        """
        entity_type = mapped_entity.entity_type.lower() if hasattr(mapped_entity, "entity_type") else ""
        entity_name = mapped_entity.name.lower() if hasattr(mapped_entity, "name") else ""
        
        # Check entity type first
        if entity_type == "motion":
            return BinarySensorDeviceClass.MOTION
        
        # Check name for keywords
        if "rauchmelder" in entity_name or "smoke" in entity_name:
            return BinarySensorDeviceClass.SMOKE
        if "fenster" in entity_name or "window" in entity_name:
            return BinarySensorDeviceClass.OPENING
        if "tür" in entity_name or "door" in entity_name:
            return BinarySensorDeviceClass.OPENING
        if "motion" in entity_name or "bewegung" in entity_name:
            return BinarySensorDeviceClass.MOTION
        if "vibration" in entity_name:
            return BinarySensorDeviceClass.VIBRATION
        
        # Default: no specific class
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes.
        
        Returns:
            Dictionary of extra state attributes
        """
        attrs: dict[str, Any] = {}
        
        if self._address_status:
            attrs["knx_address"] = str(self._address_status)
        
        if hasattr(self._mapped_entity, "attributes"):
            sensor_type = self._mapped_entity.attributes.get("sensor_type")
            if sensor_type:
                attrs["sensor_type"] = sensor_type
        
        return attrs
