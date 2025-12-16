"""The Theben LUXORliving integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LuxorLivingApi
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import LuxorLivingCoordinator

_LOGGER = logging.getLogger(__name__)

# Convert platform names to Platform enum
PLATFORMS_ENUM = [Platform.LIGHT, Platform.SWITCH, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LUXORliving from a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        True if setup was successful
    """
    _LOGGER.debug("Setting up LUXORliving integration")
    
    # Get configuration
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT)
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    
    # Create API client
    session = async_get_clientsession(hass)
    api = LuxorLivingApi(host=host, port=port, session=session)
    
    # Create coordinator with configured scan interval
    coordinator = LuxorLivingCoordinator(
        hass=hass,
        api=api,
        update_interval=timedelta(seconds=scan_interval),
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_ENUM)
    
    _LOGGER.info("LUXORliving integration setup complete")
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        True if unload was successful
    """
    _LOGGER.debug("Unloading LUXORliving integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_ENUM)
    
    # Remove coordinator
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
    _LOGGER.info("LUXORliving integration unloaded")
    
    return unload_ok
