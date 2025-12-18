"""Sensor platform for LUXORliving integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
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
    """Set up LUXORliving sensors from a config entry."""
    _LOGGER.info("Setting up LUXORliving sensors")
    
    # TODO: Parse LXP file and create sensor entities
    entities = []
    
    async_add_entities(entities)
