"""Health check HTTP endpoint for LUXORliving integration."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .circuit_breaker import get_knx_circuit_breaker, get_rest_api_circuit_breaker
from .const import DATA_KNX_GATEWAY, DOMAIN
from .lxp_parser import get_lxp_cache_stats

_LOGGER = logging.getLogger(__name__)


def _get_manifest_version() -> str:
    """Return version from manifest.json, fallback to unknown."""
    manifest_path = Path(__file__).parent / "manifest.json"
    try:
        data = json.loads(manifest_path.read_text())
        if isinstance(data, dict):
            version = data.get("version")
            if isinstance(version, str):
                return version
        return "unknown"
    except FileNotFoundError:
        return "unknown"


_MANIFEST_VERSION = _get_manifest_version()


class LuxorLivingHealthView(HomeAssistantView):
    """Health check endpoint for LUXORliving integration."""

    url = "/api/luxor_living/health"
    name = "api:luxor_living:health"
    requires_auth = True

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
                "timestamp": asyncio.get_running_loop().time(),
                "integration": {
                    "name": "LUXORliving",
                    "version": _MANIFEST_VERSION,
                    "domain": DOMAIN,
                },
                "entries": {},
                "system": {
                    "cache": get_lxp_cache_stats(),
                    "circuit_breakers": {
                        "rest_api": get_rest_api_circuit_breaker().get_stats(),
                        "knx_connection": get_knx_circuit_breaker().get_stats(),
                    },
                },
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
                    if hasattr(knx_gateway, "_known_addresses"):
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
            from aiohttp import web

            return web.json_response(
                {
                    "status": "error",
                    "error": str(err),
                    "timestamp": asyncio.get_running_loop().time(),
                },
                status=500,
            )
