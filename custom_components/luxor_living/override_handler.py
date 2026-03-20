"""OverrideHandler module for managing sensor overrides in LUXORliving.

This module handles user-defined sensor overrides from luxor_living_overrides.yaml.
Extracted from EntityMapper to improve separation of concerns.
"""

import logging
from typing import Any

from homeassistant.const import Platform

from .mapped_entity import MappedEntity

_LOGGER = logging.getLogger(__name__)


class OverrideHandler:
    """Handles application of user-defined sensor overrides.

    This class processes override configurations and creates sensor entities
    for user-customized datapoints. Supports:
    - Custom sensor names
    - Custom device names/IDs
    - Custom units of measurement
    - Custom device classes
    - Address normalization (GA string "1/2/3" → integer encoding)

    Example:
        overrides = {
            "sensors": [
                {
                    "role": "Temperature",
                    "address": "1/2/3",
                    "name": "Custom Temp Sensor",
                    "unit": "°F",
                    "device_class": "temperature"
                }
            ]
        }
        handler = OverrideHandler(overrides)
        entities = []
        handler.apply_overrides(entities)
    """

    # Role to unit mapping (copied from PlatformDetector for now)
    ROLE_TO_UNIT = {
        "Temperature": "°C",
        "Temperatur": "°C",
        "Humidity": "%",
        "Luftfeuchte": "%",
        "Pressure": "hPa",
        "Luftdruck": "hPa",
        "CO2": "ppm",
        "Brightness": "lx",
        "Helligkeit": "lx",
        "WindSpeed": "m/s",
        "Windgeschwindigkeit": "km/h",
        "RainVolume": "mm",
    }

    # Role to device class mapping (copied from PlatformDetector for now)
    ROLE_TO_DEVICE_CLASS = {
        "Temperature": "temperature",
        "Temperatur": "temperature",
        "Humidity": "humidity",
        "Luftfeuchte": "humidity",
        "Pressure": "pressure",
        "Luftdruck": "pressure",
        "Brightness": "illuminance",
        "Helligkeit": "illuminance",
        "RainVolume": "precipitation",
    }

    def __init__(self, overrides: dict[str, Any]) -> None:
        """Initialize OverrideHandler with override configuration.

        Args:
            overrides: Dictionary from luxor_living_overrides.yaml
                Expected format: {"sensors": [...]}
        """
        self._overrides = overrides

    def apply_overrides(self, entities: list[MappedEntity]) -> None:
        """Apply sensor overrides from configuration.

        Creates new MappedEntity instances for each valid override and appends
        to the entities list. Invalid overrides are logged and skipped.

        Args:
            entities: List to append override entities to (modified in-place)
        """
        sensors = self._overrides.get("sensors", [])
        if not sensors:
            return

        for ov in sensors:
            try:
                role = ov.get("role")
                address = ov.get("address")
                name = ov.get("name") or role
                device_name = ov.get("device_name") or ov.get("device") or "Overrides"
                device_id = ov.get("device_id") or "overrides"

                if not role or not address:
                    _LOGGER.warning("Override entry missing role/address: %s", ov)
                    continue

                # Normalize address to int
                addr_int = self._normalize_address(address)
                if addr_int is None:
                    _LOGGER.warning("Invalid override address: %s", address)
                    continue

                # Map sensor role
                # Allow override of unit/device_class
                unit = ov.get("unit") if ov.get("unit") else self.ROLE_TO_UNIT.get(role)
                device_class = (
                    ov.get("device_class")
                    if ov.get("device_class")
                    else self.ROLE_TO_DEVICE_CLASS.get(role)
                )

                entity = MappedEntity(
                    platform=Platform.SENSOR,
                    unique_id=f"{device_id}_{addr_int}",
                    name=name,
                    device_name=device_name,
                    device_id=device_id,
                    entity_type=role.lower(),
                    datapoints={role: addr_int},
                    attributes={
                        "device_class": device_class,
                        "unit_of_measurement": unit,
                        "channel": ov.get("channel"),
                        "serial_number": ov.get("serial_number"),
                        "knx_address": ov.get("individual_address"),
                    },
                    parameters={},  # No LXP parameters for overrides
                )

                entities.append(entity)
                _LOGGER.debug("Applied override sensor '%s' (%s) at %s", name, role, address)
            except Exception as err:
                _LOGGER.error("Failed to apply override %s: %s", ov, err)

    @staticmethod
    def _normalize_address(addr: Any) -> int | None:
        """Convert GA string 'M/L/G' or int-like to int encoding used in LXP.

        Supports three formats:
        - Integer: 2563 → 2563
        - Decimal string: "2563" → 2563
        - GA string: "1/2/3" → (1 << 11) | (2 << 8) | 3 = 2563

        Args:
            addr: Address in various formats (int, str)

        Returns:
            Integer-encoded address or None if invalid

        Example:
            >>> OverrideHandler._normalize_address("1/2/3")
            2563
            >>> OverrideHandler._normalize_address(2563)
            2563
        """
        try:
            if isinstance(addr, int):
                return addr
            s = str(addr).strip()
            if "/" in s:
                parts = s.split("/")
                if len(parts) != 3:
                    return None
                m, l, g = (int(p) for p in parts)
                return (m << 11) | (l << 8) | g
            # Decimal string
            return int(s)
        except (ValueError, IndexError, TypeError):
            return None
