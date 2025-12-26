"""Diagnostics support for LUXORliving integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_KNX_GATEWAY, DOMAIN


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
        },
        "config": {
            "host": entry.data.get("host"),
            "connection_type": entry.data.get("connection_type"),
            "simulation_mode": entry.data.get("simulation_mode", False),
            # Exclude sensitive data (username, password, lxp_file path)
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
            diagnostics["entities"] = {
                "total": len(getattr(mapper, "entities", [])),
                "by_platform": {},
            }

            # Count entities by platform
            for entity in getattr(mapper, "entities", []):
                platform = entity.get("platform", "unknown")
                diagnostics["entities"]["by_platform"][platform] = (
                    diagnostics["entities"]["by_platform"].get(platform, 0) + 1
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
                "update_interval": str(coordinator.update_interval) if hasattr(coordinator, "update_interval") else None,
            }
        except Exception as err:
            diagnostics["coordinator"] = {"error": str(err)}

    return diagnostics
