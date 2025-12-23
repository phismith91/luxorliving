"""The LUXORliving integration."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_LXP_FILE,
    CONF_CONNECTION_TYPE,
    CONF_SIMULATION_MODE,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_CONNECTION_TYPE,
    DEFAULT_HTTP_PORT,
    DATA_KNX_GATEWAY,
)
from .lxp_parser import LXPParser
from .entity_mapper import EntityMapper
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)

# Only include implemented platforms
PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LUXORliving from a config entry."""
    _LOGGER.debug("LUXORliving setup started")
    
    # Store integration data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    
    # Get configuration
    lxp_file = entry.data.get(CONF_LXP_FILE)
    host = entry.data.get(CONF_HOST, "localhost")
    port = DEFAULT_PORT  # Always use KNX/IP default port 3671
    username = entry.data.get(CONF_USERNAME, "admin")
    password = entry.data.get(CONF_PASSWORD, "admin")
    connection_type = entry.data.get(CONF_CONNECTION_TYPE, DEFAULT_CONNECTION_TYPE)
    simulation_mode = entry.data.get(CONF_SIMULATION_MODE, False)
    
    if not lxp_file:
        _LOGGER.error("No LXP file configured - setup cannot continue")
        return False
    
    # Parse LXP file
    lxp_path = Path(lxp_file).expanduser()
    
    if lxp_path and lxp_path.exists():
        _LOGGER.info("Parsing LXP file: %s", lxp_path)
        try:
            parser = LXPParser(str(lxp_path))
            project = await parser.parse()
            
            # Create entity mapper
            mapper = EntityMapper(project)
            entity_count = len(mapper.entities)
            _LOGGER.warning("Mapped %d entities from LXP project", entity_count)
            
            # Store mapper and config in integration data
            hass.data[DOMAIN][entry.entry_id]["mapper"] = mapper
            hass.data[DOMAIN][entry.entry_id]["config"] = entry.data
        except FileNotFoundError as err:
            _LOGGER.error("LXP file not found: %s", lxp_path)
            return False
        except Exception as err:
            _LOGGER.exception("Failed to parse LXP file %s", lxp_path)
            return False
    else:
        _LOGGER.error("LXP file not found: %s - cannot load entities", lxp_file)
        return False
    
    # Initialize KNX Gateway with REST API credentials
    knx_gateway = LuxorKNXGateway(
        hass=hass,
        host=host,
        port=port,
        username=username,
        password=password,
        http_port=DEFAULT_HTTP_PORT,
        connection_type=connection_type,
        simulation_mode=simulation_mode,
    )
    
    # Connect to gateway
    if not await knx_gateway.async_setup():
        _LOGGER.error("Failed to connect to KNX gateway")
        # Continue anyway in simulation mode
        if not simulation_mode:
            return False
    
    # Note: Datapoint mapping is now loaded in knx_gateway.async_setup()
    # via _async_load_datapoint_mapping() which fetches from REST API
    
    # Store gateway in integration data
    hass.data[DOMAIN][entry.entry_id][DATA_KNX_GATEWAY] = knx_gateway

    # Provide GA→labels to gateway for log enrichment (Name + ID)
    try:
        ga_label_map = mapper.get_group_address_label_map()
        ia_label_map = mapper.get_individual_address_label_map()
        knx_gateway.set_group_address_labels(ga_label_map)
        knx_gateway.set_individual_address_labels(ia_label_map)
    except (AttributeError, KeyError) as err:
        _LOGGER.debug("Could not build GA/IA label maps: %s", err)
    
    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading LUXORliving integration")
    
    # Disconnect KNX gateway
    knx_gateway = hass.data[DOMAIN][entry.entry_id].get(DATA_KNX_GATEWAY)
    if knx_gateway:
        await knx_gateway.async_disconnect()
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
