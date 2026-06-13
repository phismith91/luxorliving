"""The LUXORliving integration."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_DISCOVERY_TIMEOUT,
    CONF_LXP_FILE,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SIMULATION_MODE,
    CONF_USERNAME,
    DEFAULT_CONNECTION_TYPE,
    DEFAULT_DISCOVERY_TIMEOUT,
    DEFAULT_HTTP_PORT,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import LuxorLivingCoordinator
from .entity_mapper import EntityMapper
from .health_view import LuxorLivingHealthView
from .integration_state import IntegrationState
from .knx_gateway import LuxorKNXGateway
from .lxp_parser import LXPParser
from .overrides import load_overrides
from .push_view import LuxorLivingPushView

_LOGGER = logging.getLogger(__name__)

# Only include implemented platforms
PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.COVER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LUXORliving from a config entry."""
    _LOGGER.debug("LUXORliving setup started")

    # Register health check endpoint (only once per integration)
    if not hass.data.get(DOMAIN, {}).get("_health_registered"):
        hass.http.register_view(LuxorLivingHealthView(hass))
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["_health_registered"] = True
        _LOGGER.debug("Health check endpoint registered at /api/luxor_living/health")

    # Register push endpoint (webhook / websocket forwarder) (only once)
    if not hass.data.get(DOMAIN, {}).get("_push_registered"):
        hass.http.register_view(LuxorLivingPushView(hass))
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["_push_registered"] = True
        _LOGGER.debug("Push endpoint registered at /api/luxor_living/push")

    # Get configuration
    lxp_file = entry.data.get(CONF_LXP_FILE)
    host = entry.data.get(CONF_HOST, "localhost")
    port = DEFAULT_PORT  # Always use KNX/IP default port 3671
    username = entry.data.get(CONF_USERNAME, "admin")
    password = entry.data.get(CONF_PASSWORD, "admin")
    connection_type = entry.data.get(CONF_CONNECTION_TYPE, DEFAULT_CONNECTION_TYPE)
    simulation_mode = entry.options.get(
        CONF_SIMULATION_MODE, entry.data.get(CONF_SIMULATION_MODE, False)
    )
    discovery_timeout = entry.options.get(
        CONF_DISCOVERY_TIMEOUT, entry.data.get(CONF_DISCOVERY_TIMEOUT, DEFAULT_DISCOVERY_TIMEOUT)
    )

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
            overrides = await hass.async_add_executor_job(load_overrides, config_dir)
            include_unaffected = bool(overrides.get("include_unaffected", False))

            project = await LXPParser.parse_cached(
                str(lxp_path), include_unaffected=include_unaffected
            )

            # Create entity mapper
            mapper = EntityMapper(project, overrides=overrides)
            entity_count = len(mapper.entities)
            _LOGGER.warning("Mapped %d entities from LXP project", entity_count)

            # Create type-safe integration state
            state = IntegrationState(
                mapper=mapper,
                config=dict(entry.data),
                overrides=overrides,
                entry=entry,
            )

            # Store state on config entry (HA runtime_data pattern)
            entry.runtime_data = state
        except FileNotFoundError:
            _LOGGER.error("LXP file not found: %s", lxp_path)
            return False
        except Exception:
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
            hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))

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
        # In simulation mode we continue; otherwise raise ConfigEntryNotReady so
        # Home Assistant retries setup automatically (e.g. after a brief outage)
        # instead of leaving the integration permanently failed.
        if not simulation_mode:
            raise ConfigEntryNotReady(f"Unable to connect to KNX gateway at {host}")

    # Note: Datapoint mapping is now loaded in knx_gateway.async_setup()
    # via _async_load_datapoint_mapping() which fetches from REST API

    # Store gateway in integration state (type-safe)
    state = entry.runtime_data
    state.knx_gateway = knx_gateway

    # If configured, start WebSocket push client
    push_ws_url = entry.options.get("push_ws_url", entry.data.get("push_ws_url"))
    push_ws_token = entry.options.get("push_ws_token", entry.data.get("push_ws_token"))
    if push_ws_url:
        try:
            from .push_client import PushClient

            push_client = PushClient(hass, entry.entry_id, push_ws_url, push_ws_token)
            push_client.start()
            state.push_client = push_client
            _LOGGER.info("Started push client for entry %s -> %s", entry.entry_id, push_ws_url)
        except Exception as err:
            _LOGGER.exception("Failed to start push client: %s", err)

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
    coordinator = LuxorLivingCoordinator(hass, knx_gateway, entry, scan_interval)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in integration state (type-safe)
    state = entry.runtime_data
    state.coordinator = coordinator

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

    # Register list entities service
    async def async_list_entities(call: ServiceCall) -> None:
        """List entity IDs for the integration."""
        platform_filter = call.data.get("platform")
        entities = []

        # Get all entities from mapper
        mapper = entry.runtime_data.mapper
        if mapper:
            for entity in mapper.entities:
                if platform_filter and entity.platform.value != platform_filter:
                    continue
                entities.append(
                    {
                        "entity_id": f"{entity.platform.value}.{entity.unique_id}",
                        "name": entity.name,
                        "device_name": entity.device_name,
                        "platform": entity.platform.value,
                    }
                )

        # Send as persistent notification
        message = "**LUXORliving Entities**\n\n"
        if platform_filter:
            message += f"Filtered by platform: {platform_filter}\n\n"

        for entity in sorted(entities, key=lambda x: x["entity_id"]):
            message += f"- `{entity['entity_id']}`: {entity['name']} ({entity['device_name']})\n"

        if not entities:
            message += "No entities found."

        await hass.services.async_call(
            "persistent_notification",
            "create",
            {"title": "LUXORliving Entity List", "message": message},
        )

    hass.services.async_register(DOMAIN, "list_entities", async_list_entities)

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

    # Disconnect KNX gateway using type-safe state
    state = entry.runtime_data
    if state.knx_gateway:
        await state.knx_gateway.async_disconnect()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Stop push client if running
        try:
            if state.push_client:
                await state.push_client.stop()
        except Exception as err:
            _LOGGER.debug("Error stopping push client during unload: %s", err)

    return bool(unload_ok)
