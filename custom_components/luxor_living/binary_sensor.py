"""Binary sensor platform for LUXORliving integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up LUXORliving binary sensors from a config entry."""
    _LOGGER.info("Setting up LUXORliving binary sensors")
    
    # TODO: Parse LXP file and create binary sensor entities
    entities = []
    
    async_add_entities(entities)
