"""Light platform for LUXORliving integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
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
    """Set up LUXORliving lights from a config entry."""
    _LOGGER.info("Setting up LUXORliving lights")
    
    # Get mapper from integration data
    mapper: EntityMapper = hass.data[DOMAIN][entry.entry_id].get("mapper")
    
    if not mapper:
        _LOGGER.warning("No mapper found, skipping light setup")
        return
    
    # Get all light entities
    light_entities = mapper.get_entities_by_platform(Platform.LIGHT)
    _LOGGER.info("Creating %d light entities", len(light_entities))
    
    entities = []
    for mapped_entity in light_entities:
        if mapped_entity.entity_type == "dimmable_light":
            entity = LuxorLivingDimmableLight(mapped_entity)
        else:
            entity = LuxorLivingLight(mapped_entity)
        entities.append(entity)
    
    async_add_entities(entities)


class LuxorLivingLight(LightEntity):
    """Representation of a LUXORliving light."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, mapped_entity: Any) -> None:
        """Initialize the light."""
        self._mapped = mapped_entity
        self._attr_unique_id = mapped_entity.unique_id
        self._attr_name = mapped_entity.name
        self._attr_is_on = False
        
        # Store datapoint addresses
        self._address_on = mapped_entity.datapoints.get("OnOff") or mapped_entity.datapoints.get("SchaltenOnOff")
        self._address_status = mapped_entity.datapoints.get("StatusOnOff")
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mapped_entity.device_id)},
            "name": mapped_entity.device_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        # TODO: Send KNX telegram when KNX integration is ready
        # For now, just update state (simulation mode)
        _LOGGER.debug(
            "Turning on %s (address: %s)", self._attr_name, self._address_on
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        # TODO: Send KNX telegram when KNX integration is ready
        # For now, just update state (simulation mode)
        _LOGGER.debug(
            "Turning off %s (address: %s)", self._attr_name, self._address_on
        )
        self._attr_is_on = False
        self.async_write_ha_state()


class LuxorLivingDimmableLight(LuxorLivingLight):
    """Representation of a dimmable LUXORliving light."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, mapped_entity: Any) -> None:
        """Initialize the dimmable light."""
        super().__init__(mapped_entity)
        self._attr_brightness = 255
        
        # Additional datapoints for dimming
        self._address_dim = mapped_entity.datapoints.get("Dimmen%")
        self._address_dim_rel = mapped_entity.datapoints.get("DimmenRel")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        
        # TODO: Send KNX telegram for dimming
        _LOGGER.debug(
            "Turning on %s with brightness %d (address: %s)",
            self._attr_name,
            brightness,
            self._address_dim or self._address_on,
        )
        
        self._attr_is_on = True
        self._attr_brightness = brightness
        self.async_write_ha_state()
