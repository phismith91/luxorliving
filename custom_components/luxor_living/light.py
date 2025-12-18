"""Light platform for LUXORliving integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving lights from a config entry."""
    _LOGGER.info("Setting up LUXORliving lights")
    
    # TODO: Parse LXP file and create light entities
    # For now, create empty list
    entities = []
    
    async_add_entities(entities)


class LuxorLivingLight(LightEntity):
    """Representation of a LUXORliving light."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, device_id: str, name: str) -> None:
        """Initialize the light."""
        self._attr_unique_id = device_id
        self._attr_name = name
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        # TODO: Send KNX telegram
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        # TODO: Send KNX telegram
        self._attr_is_on = False
        self.async_write_ha_state()
