"""The LUXORliving integration."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_LXP_FILE,
    CONF_CONNECTION_TYPE,
    CONF_SIMULATION_MODE,
    CONF_USERNAME,
    CONF_PASSWORD,
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


async def _async_build_datapoint_mapping_from_lxp(
    gateway: LuxorKNXGateway,
    mapper: EntityMapper
) -> None:
    """
    Build Datapoint ID → GroupAddress mapping from LXP file data.
    
    The LXP file contains datapoint IDs like '2304 (1/1/0)'.
    We extract these to build the mapping for REST API queries.
    """
    mapping_count = 0
    
    for entity_data in mapper.entities:
        # Get datapoints dictionary (e.g., {'StatusOnOff': '2304 (1/1/0)', ...})
        datapoints = entity_data.get("datapoints", {})
        
        for dp_name, dp_value in datapoints.items():
            if not dp_value or not isinstance(dp_value, str):
                continue
            
            # Parse format: "2304 (1/1/0)"
            try:
                parts = dp_value.split("(")
                if len(parts) != 2:
                    continue
                
                dp_id_str = parts[0].strip()
                group_addr = parts[1].rstrip(")").strip()
                
                dp_id = int(dp_id_str)
                
                # Store mapping: GroupAddress → Datapoint ID
                gateway._datapoint_mapping[group_addr] = dp_id
                mapping_count += 1
                
            except (ValueError, IndexError) as e:
                _LOGGER.debug(f"Failed to parse datapoint '{dp_value}': {e}")
                continue
    
    _LOGGER.info(f"✅ Built {mapping_count} GroupAddress → Datapoint-ID mappings from LXP file")
    if mapping_count > 0:
        sample = dict(list(gateway._datapoint_mapping.items())[:3])
        _LOGGER.debug(f"Sample mappings: {sample}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LUXORliving from a config entry."""
    _LOGGER.warning("🔥🔥🔥 LUXOR SETUP STARTED 🔥🔥🔥")
    
    # Store integration data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    
    # Get configuration
    lxp_file = entry.data.get(CONF_LXP_FILE)
    host = entry.data.get(CONF_HOST, "localhost")
    port = entry.data.get(CONF_PORT, 3671)
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
            _LOGGER.warning("🔥 Mapped %d entities from LXP project", entity_count)
            
            # Store mapper and config in integration data
            hass.data[DOMAIN][entry.entry_id]["mapper"] = mapper
            hass.data[DOMAIN][entry.entry_id]["config"] = entry.data
        except Exception as err:
            _LOGGER.exception("Failed to parse LXP file %s: %s", lxp_path, err)
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
    
    # Build Datapoint mapping from LXP data
    await _async_build_datapoint_mapping_from_lxp(knx_gateway, mapper)
    
    # Store gateway in integration data
    hass.data[DOMAIN][entry.entry_id][DATA_KNX_GATEWAY] = knx_gateway
    
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
