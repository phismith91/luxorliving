"""The LUXORliving integration."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .circuit_breaker import get_knx_circuit_breaker, get_rest_api_circuit_breaker
from .lxp_parser import get_lxp_cache_stats

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_LXP_FILE,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SIMULATION_MODE,
    CONF_USERNAME,
    DATA_KNX_GATEWAY,
    DEFAULT_CONNECTION_TYPE,
    DEFAULT_HTTP_PORT,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import LuxorLivingCoordinator
from .entity_mapper import EntityMapper
from .overrides import load_overrides
from .knx_gateway import LuxorKNXGateway
from .lxp_parser import LXPParser

_LOGGER = logging.getLogger(__name__)

# Only include implemented platforms
PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]


class LuxorLivingHealthView(HomeAssistantView):
    """Health check endpoint for LUXORliving integration."""

    url = "/api/luxor_living/health"
    name = "api:luxor_living:health"
    requires_auth = False  # Allow unauthenticated access for monitoring

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the health check view."""
        self.hass = hass

    async def get(self, request):
        """Handle GET request to health endpoint."""
        try:
            # Get integration data
            domain_data = self.hass.data.get(DOMAIN, {})

            health_data = {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "integration": {
                    "name": "LUXORliving",
                    "version": "0.5.0",
                    "domain": DOMAIN,
                },
                "entries": {},
                "system": {
                    "cache": get_lxp_cache_stats(),
                    "circuit_breakers": {
                        "rest_api": get_rest_api_circuit_breaker().get_stats(),
                        "knx_connection": get_knx_circuit_breaker().get_stats(),
                    }
                }
            }

            # Check each config entry
            for entry_id, entry_data in domain_data.items():
                # Skip non-entry data (like _health_registered)
                if not isinstance(entry_data, dict):
                    continue

                entry_health = {
                    "connected": False,
                    "simulation_mode": False,
                    "entity_count": 0,
                    "discovered_sensors": 0,
                    "known_addresses": 0,
                }

                # Check KNX gateway status
                knx_gateway = entry_data.get(DATA_KNX_GATEWAY)
                if knx_gateway:
                    entry_health["connected"] = knx_gateway.is_connected()
                    entry_health["simulation_mode"] = knx_gateway.simulation_mode

                    # Get entity count from mapper
                    mapper = entry_data.get("mapper")
                    if mapper:
                        entry_health["entity_count"] = len(mapper.entities)

                    # Get discovered sensors count
                    config = entry_data.get("config", {})
                    discovered_sensors = config.get("discovered_sensors", {})
                    entry_health["discovered_sensors"] = len(discovered_sensors)

                    # Get known addresses count
                    if hasattr(knx_gateway, '_known_addresses'):
                        entry_health["known_addresses"] = len(knx_gateway._known_addresses)

                health_data["entries"][entry_id] = entry_health

                # If any entry is not connected (and not in simulation), mark as unhealthy
                if not entry_health["connected"] and not entry_health["simulation_mode"]:
                    health_data["status"] = "unhealthy"

            # Check circuit breaker states
            rest_cb = health_data["system"]["circuit_breakers"]["rest_api"]
            knx_cb = health_data["system"]["circuit_breakers"]["knx_connection"]

            if rest_cb["state"] == "open" or knx_cb["state"] == "open":
                health_data["status"] = "degraded"

            return self.json(health_data)

        except Exception as err:
            _LOGGER.exception("Health check failed")
            from homeassistant.core import HomeAssistant
            from aiohttp import web
            return web.json_response({
                "status": "error",
                "error": str(err),
                "timestamp": asyncio.get_event_loop().time(),
            }, status=500)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LUXORliving from a config entry."""
    _LOGGER.debug("LUXORliving setup started")

    # Register health check endpoint (only once per integration)
    if not hasattr(hass.data.get(DOMAIN, {}), "_health_registered"):
        hass.http.register_view(LuxorLivingHealthView(hass))
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["_health_registered"] = True
        _LOGGER.debug("Health check endpoint registered at /api/luxor_living/health")

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
    simulation_mode = entry.options.get(CONF_SIMULATION_MODE, entry.data.get(CONF_SIMULATION_MODE, False))
    discovery_timeout = entry.options.get(CONF_DISCOVERY_TIMEOUT, entry.data.get(CONF_DISCOVERY_TIMEOUT, DEFAULT_DISCOVERY_TIMEOUT))

    if not lxp_file:
        _LOGGER.error("No LXP file configured - setup cannot continue")
        return False

    # Parse LXP file
    lxp_path = Path(lxp_file).expanduser()

    if lxp_path and lxp_path.exists():
        _LOGGER.info("Parsing LXP file: %s", lxp_path)
        try:
            # Optional: include_unaffected controlled via overrides 'include_unaffected'
            config_dir = Path(hass.config.path(""))
            overrides = load_overrides(config_dir)
            include_unaffected = bool(overrides.get("include_unaffected", False))

            project = await LXPParser.parse_cached(str(lxp_path), include_unaffected=include_unaffected)

            # Create entity mapper
            mapper = EntityMapper(project, overrides=overrides)
            entity_count = len(mapper.entities)
            _LOGGER.warning("Mapped %d entities from LXP project", entity_count)

            # Store mapper and config in integration data
            hass.data[DOMAIN][entry.entry_id]["mapper"] = mapper
            hass.data[DOMAIN][entry.entry_id]["config"] = entry.data
            hass.data[DOMAIN][entry.entry_id]["overrides"] = overrides
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
        discovery_timeout=discovery_timeout,
    )

    # Load previously discovered sensors from config entry
    discovered_sensors = entry.data.get("discovered_sensors", {})
    if discovered_sensors:
        knx_gateway.load_discovered_sensors(discovered_sensors)
        _LOGGER.info("Loaded %d discovered sensors from config", len(discovered_sensors))

    # Register discovery callback to persist new sensors (with debouncing)
    _reload_scheduled = False

    def _on_sensor_discovered(sensor_info: dict) -> None:
        """Persist newly discovered sensor to config entry."""
        nonlocal _reload_scheduled
        
        _LOGGER.info("New sensor discovered: %s", sensor_info["address"])
        
        # Update config entry data
        new_data = {**entry.data}
        new_data.setdefault("discovered_sensors", {})
        new_data["discovered_sensors"][sensor_info["address"]] = sensor_info
        hass.config_entries.async_update_entry(entry, data=new_data)
        
        # Trigger sensor platform reload only once (debounced by gateway)
        if not _reload_scheduled:
            _reload_scheduled = True
            hass.async_create_task(
                hass.config_entries.async_reload(entry.entry_id)
            )
            # Reset flag after a delay
            async def reset_flag():
                await asyncio.sleep(5)  # Allow time for reload to complete
                nonlocal _reload_scheduled
                _reload_scheduled = False
            hass.async_create_task(reset_flag())

    knx_gateway.register_discovery_callback(_on_sensor_discovered)

    # Collect all known LXP addresses and sensor types from EntityMapper
    known_addresses = set()
    sensor_types = {}  # {address: sensor_type}
    
    if mapper:
        for entity in mapper.entities:
            # Add all datapoint addresses from entity
            for role, address in entity.datapoints.items():
                if isinstance(address, int):
                    # Convert int address to group address string
                    ga_str = f"{(address >> 11) & 0x1F}/{(address >> 8) & 0x07}/{address & 0xFF}"
                    known_addresses.add(ga_str)
                    
                    # Map sensor roles to types for logging
                    role_to_type = {
                        "Temperature": "temperature",
                        "Temperatur": "temperature",
                        "Humidity": "humidity",
                        "Brightness": "illuminance",
                        "HelligkeitMitte": "illuminance",
                        "HelligkeitLinks": "illuminance",
                        "HelligkeitRechts": "illuminance",
                        "Pressure": "pressure",
                        "WindSpeed": "wind_speed",
                        "Windgeschwindigkeit": "wind_speed",
                    }
                    if role in role_to_type:
                        sensor_types[ga_str] = role_to_type[role]
                        
                elif isinstance(address, str):
                    known_addresses.add(address)
                    
        knx_gateway.set_known_addresses(known_addresses)
        knx_gateway.set_sensor_types(sensor_types)
        _LOGGER.info("Excluded %d known LXP addresses from auto-discovery", len(known_addresses))
        _LOGGER.info("Registered %d sensor type mappings for accurate logging", len(sensor_types))

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

    # Initialize Data Coordinator with scan interval from options
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    coordinator = LuxorLivingCoordinator(hass, knx_gateway, scan_interval)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in integration data
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register device with configuration URL
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Theben",
        model="LUXORliving",
        name="LUXORliving Gateway",
        configuration_url="https://github.com/phismith91/luxorliving/blob/main/docs/README.md",
    )

    # Register reload service
    async def async_reload_entry(call: ServiceCall) -> None:
        """Reload the config entry."""
        await hass.config_entries.async_reload(entry.entry_id)

    hass.services.async_register(DOMAIN, "reload", async_reload_entry)

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    _LOGGER.info("Options updated, reloading entry")
    await hass.config_entries.async_reload(entry.entry_id)


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
