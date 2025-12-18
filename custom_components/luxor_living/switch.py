"""Switch platform for LUXORliving integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up LUXORliving switches from a config entry."""
    _LOGGER.info("Setting up LUXORliving switches")
    
    # TODO: Parse LXP file and create switch entities
    entities = []
    
    async_add_entities(entities)


class LuxorLivingSwitch(SwitchEntity):
    """Representation of a LUXORliving switch."""

    _attr_has_entity_name = True

    def __init__(self, device_id: str, name: str) -> None:
        """Initialize the switch."""
        self._attr_unique_id = device_id
        self._attr_name = name
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        # TODO: Send KNX telegram
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        # TODO: Send KNX telegram
        self._attr_is_on = False
        self.async_write_ha_state()
