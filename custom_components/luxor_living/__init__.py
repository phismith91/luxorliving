"""The LUXORliving integration."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_LXP_FILE
from .lxp_parser import LXPParser
from .entity_mapper import EntityMapper

_LOGGER = logging.getLogger(__name__)

# Only include implemented platforms
PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LUXORliving from a config entry."""
    _LOGGER.warning("🔥🔥🔥 LUXOR SETUP STARTED 🔥🔥🔥")
    
    # Store integration data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    
    # Get LXP file path from config entry
    lxp_file = entry.data.get(CONF_LXP_FILE)
    
    if not lxp_file:
        _LOGGER.error("No LXP file configured - setup cannot continue")
        return False
    
    lxp_path = Path(lxp_file).expanduser()
    
    if lxp_path and lxp_path.exists():
        _LOGGER.info("Parsing LXP file: %s", lxp_path)
        parser = LXPParser(str(lxp_path))
        project = await parser.parse()
        
        # Create entity mapper
        mapper = EntityMapper(project)
        entity_count = len(mapper.entities)
        _LOGGER.warning("🔥 Mapped %d entities from LXP project", entity_count)
        
        # Store mapper and config in integration data
        hass.data[DOMAIN][entry.entry_id]["mapper"] = mapper
        hass.data[DOMAIN][entry.entry_id]["config"] = entry.data
    else:
        _LOGGER.error("LXP file not found: %s - cannot load entities", lxp_file)
        return False
    
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
