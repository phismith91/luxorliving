"""The LUXORliving integration."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .lxp_parser import LXPParser
from .entity_mapper import EntityMapper

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.COVER,
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LUXORliving from a config entry."""
    _LOGGER.info("Setting up LUXORliving integration")
    
    # Store integration data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    
    # TODO: Get LXP file path from config entry
    # For now, use a hardcoded test file
    test_file_paths = [
        Path.home() / "Nextcloud/Projekte_Rechner/Madeira/Schmidt_Madeira_V0.8.lxp",
        Path.home() / "Nextcloud/Projekte_Rechner/Madeira/Madeira.lxp",
        Path(__file__).parent.parent.parent / "Familie Schmidt_0.9.lxp",
    ]
    
    test_file = None
    for path in test_file_paths:
        if path.exists():
            test_file = path
            break
    
    if test_file:
        _LOGGER.info("Parsing LXP file: %s", test_file)
        parser = LXPParser(str(test_file))
        project = parser.parse()
        
        # Create entity mapper
        mapper = EntityMapper(project)
        entity_count = len(mapper.entities)
        _LOGGER.info("Mapped %d entities from LXP project", entity_count)
        
        # Store mapper in integration data
        hass.data[DOMAIN][entry.entry_id]["mapper"] = mapper
    else:
        _LOGGER.warning("LXP file not found: %s - running without entities", test_file)
    
    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading LUXORliving integration")
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
