"""Cover platform for LUXORliving integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving covers from a config entry."""
    _LOGGER.info("Setting up LUXORliving covers")

    # TODO: Parse LXP file and create cover entities
    entities: list = []

    async_add_entities(entities)
