"""Diagnostics support for LUXORliving integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_LXP_FILE,
    CONF_SIMULATION_MODE,
    DATA_KNX_GATEWAY,
    DOMAIN,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    try:
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    except (KeyError, AttributeError):
        data = {}
    
    knx_gateway = data.get(DATA_KNX_GATEWAY)
    mapper = data.get("mapper")
    coordinator = data.get("coordinator")
    overrides = data.get("overrides", {})

    diagnostics = {
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
            "options": entry.options,
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
            diagnostics["entities"] = []

            # Collect entity details (limit to 50 for performance)
            for entity in entities[:50]:
                # EntityConfig objects have attributes, not dict keys
                entity_info = {
                    "id": getattr(entity, "id", "unknown"),
                    "name": getattr(entity, "name", "unknown"),
                    "platform": getattr(entity, "platform", "unknown"),
                    "group_address": getattr(entity, "address", "unknown"),
                }
                diagnostics["entities"].append(entity_info)

            # Summary
            diagnostics["entity_summary"] = {
                "total": len(entities),
                "by_platform": {},
            }
            
            for entity in entities:
                platform = getattr(entity, "platform", "unknown")
                diagnostics["entity_summary"]["by_platform"][platform] = (
                    diagnostics["entity_summary"]["by_platform"].get(platform, 0) + 1
                )

            # Devices info (anonymized)
            if hasattr(mapper, "project") and mapper.project:
                devices = mapper.project.get("devices", [])
                diagnostics["devices"] = {
                    "total": len(devices),
                    "by_app_id": {},
                }

                # Count devices by app_id (device type)
                for device in devices:
                    app_id = device.get("app_id", "unknown")
                    diagnostics["devices"]["by_app_id"][app_id] = (
                        diagnostics["devices"]["by_app_id"].get(app_id, 0) + 1
                    )
        except Exception as err:
            diagnostics["entities"] = {"error": str(err)}

    # Coordinator info
    if coordinator:
        try:
            diagnostics["coordinator"] = {
                "last_update_success": getattr(coordinator, "last_update_success", None),
                "last_exception": str(coordinator.last_exception) if getattr(coordinator, "last_exception", None) else None,
                "update_interval_seconds": coordinator.update_interval.total_seconds() if hasattr(coordinator, "update_interval") else None,
                "scan_interval_configured": getattr(coordinator, "_scan_interval", None),
            }
        except Exception as err:
            diagnostics["coordinator"] = {"error": str(err)}

    return diagnostics
