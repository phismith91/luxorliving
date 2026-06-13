"""Diagnostics support for LUXORliving integration."""

from __future__ import annotations

from typing import Any, Mapping, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_LXP_FILE,
    CONF_PUSH_TOKEN,
    CONF_PUSH_WS_TOKEN,
    CONF_SIMULATION_MODE,
    DATA_KNX_GATEWAY,
    DOMAIN,
)

_REDACTED = "**REDACTED**"
_SENSITIVE_OPTION_KEYS = {CONF_PUSH_TOKEN, CONF_PUSH_WS_TOKEN}


def _redact_options(options: Mapping[str, Any]) -> dict[str, Any]:
    return {k: _REDACTED if k in _SENSITIVE_OPTION_KEYS else v for k, v in options.items()}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    Note: This function is async to comply with Home Assistant's diagnostics API,
    even though it only performs synchronous data aggregation. The async signature
    is required by the framework and allows for future async operations if needed.
    """
    # Respect user consent for diagnostics. If disabled, return a minimal payload.
    allow_diagnostics = entry.options.get("allow_diagnostics", False)
    if not allow_diagnostics:
        return {
            "config_entry": {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "version": entry.version,
                "domain": entry.domain,
                "state": entry.state.value if entry.state else "unknown",
                "options": _redact_options(entry.options),
            },
            "diagnostics_allowed": False,
        }

    # Read integration state from runtime_data (current pattern since refactor).
    # Fall back to hass.data for tests that still use the old pattern.
    state = getattr(entry, "runtime_data", None)
    if state is not None:
        knx_gateway = getattr(state, "knx_gateway", None)
        mapper = getattr(state, "mapper", None)
        coordinator = getattr(state, "coordinator", None)
        overrides = getattr(state, "overrides", {})
    else:
        try:
            data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        except (KeyError, AttributeError):
            data = {}
        knx_gateway = data.get(DATA_KNX_GATEWAY)
        mapper = data.get("mapper")
        coordinator = data.get("coordinator")
        overrides = data.get("overrides", {})

    diagnostics: dict[str, Any] = {
        "diagnostics_allowed": True,
        "config_entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "version": entry.version,
            "domain": entry.domain,
            "state": entry.state.value if entry.state else "unknown",
            "data": {
                CONF_HOST: entry.data.get(CONF_HOST),
                CONF_USERNAME: entry.data.get(CONF_USERNAME),
                CONF_PASSWORD: "**REDACTED**",
                CONF_CONNECTION_TYPE: entry.data.get(CONF_CONNECTION_TYPE),
                CONF_SIMULATION_MODE: entry.data.get(CONF_SIMULATION_MODE),
                CONF_LXP_FILE: "**REDACTED**",  # May contain sensitive paths
            },
            "options": _redact_options(entry.options),
        },
        "overrides": {
            "count": len(overrides),
            "include_unaffected": overrides.get("include_unaffected", False),
            "sensors": len(overrides.get("sensors", {})),
        },
    }

    # KNX Gateway info
    if knx_gateway:
        try:
            diagnostics["knx_gateway"] = {
                "connected": getattr(knx_gateway, "_connected", False),
                "tunneling_enabled": getattr(knx_gateway, "_tunneling_enabled", False),
                "simulation_mode": getattr(knx_gateway, "simulation_mode", False),
                "host": getattr(knx_gateway, "host", "unknown"),
            }

            # Datapoint mapping info (anonymized)
            if hasattr(knx_gateway, "_datapoint_mapping"):
                mapping = knx_gateway._datapoint_mapping
                diagnostics["knx_gateway"]["datapoint_count"] = len(mapping) if mapping else 0
        except Exception as err:
            diagnostics["knx_gateway"] = {"error": str(err)}

    # Entity mapper info
    if mapper:
        try:
            entities = getattr(mapper, "entities", [])
            entity_list: list[dict[str, Any]] = []
            diagnostics["entities"] = entity_list

            # Collect entity details (limit to 50 for performance)
            for entity in entities[:50]:
                # MappedEntity objects have attributes
                entity_info = {
                    "unique_id": getattr(entity, "unique_id", "unknown"),
                    "name": getattr(entity, "name", "unknown"),
                    "platform": str(getattr(entity, "platform", "unknown")),
                    "entity_type": getattr(entity, "entity_type", "unknown"),
                    "datapoints": getattr(entity, "datapoints", {}),
                    "device_name": getattr(entity, "device_name", "unknown"),
                    "attributes": getattr(entity, "attributes", {}),
                    "parameters": getattr(entity, "parameters", {}),  # LXP parameters
                }
                entity_list.append(entity_info)

            # Summary
            diagnostics["entity_summary"] = {
                "total": len(entities),
                "by_platform": {},
                "with_parameters": sum(1 for e in entities if getattr(e, "parameters", {})),
            }

            for entity in entities:
                platform = str(getattr(entity, "platform", "unknown"))
                diagnostics["entity_summary"]["by_platform"][platform] = (
                    diagnostics["entity_summary"]["by_platform"].get(platform, 0) + 1
                )

            # Devices info (from LXP project)
            if hasattr(mapper, "_project") and mapper._project:
                project = mapper._project
                devices = getattr(project, "devices", [])
                diagnostics["devices"] = {
                    "total": len(devices),
                    "details": [],
                }

                # Device details with actuator/sensor parameters
                for device in devices:
                    device_info: dict[str, Any] = {
                        "name": getattr(device, "name", "unknown"),
                        "serial_number": getattr(device, "serial_number", "unknown"),
                        "app_id": getattr(device, "app_id", "unknown"),
                        "address": getattr(device, "address", "unknown"),
                        "actuators": [],
                        "sensors": [],
                    }

                    # Actuator details with parameters
                    for actuator in getattr(device, "actuators", []):
                        actuator_info = {
                            "name": getattr(actuator, "name", "unknown"),
                            "channel": getattr(actuator, "channel", 0),
                            "use_case": getattr(actuator, "use_case", 0),
                            "on_icon": getattr(actuator, "on_icon", ""),
                            "off_icon": getattr(actuator, "off_icon", ""),
                            "parameters": getattr(actuator, "parameters", {}),
                        }
                        cast(list, device_info["actuators"]).append(actuator_info)

                    # Sensor details with parameters
                    for sensor in getattr(device, "sensors", []):
                        sensor_info = {
                            "name": getattr(sensor, "name", "unknown"),
                            "channel": getattr(sensor, "channel", 0),
                            "sensor_type": getattr(sensor, "sensor_type", 0),
                            "parameters": getattr(sensor, "parameters", {}),
                        }
                        cast(list, device_info["sensors"]).append(sensor_info)

                    diagnostics["devices"]["details"].append(device_info)
        except Exception as err:
            diagnostics["entities"] = {"error": str(err)}

    # Coordinator info
    if coordinator:
        try:
            diagnostics["coordinator"] = {
                "last_update_success": getattr(coordinator, "last_update_success", None),
                "last_exception": (
                    str(coordinator.last_exception)
                    if getattr(coordinator, "last_exception", None)
                    else None
                ),
                "update_interval_seconds": (
                    coordinator.update_interval.total_seconds()
                    if hasattr(coordinator, "update_interval")
                    else None
                ),
                "scan_interval_configured": getattr(coordinator, "_scan_interval", None),
            }
        except Exception as err:
            diagnostics["coordinator"] = {"error": str(err)}

    return diagnostics
