"""KNX product database reader — appId-to-device lookup.

Maps LXP device appId (decimal integer) to canonical device names and
categories. The mapping is derived from the Theben ETS5 knxprod database
(Hardware.xml) and bundled as a static dict for zero-overhead lookup.
"""

from __future__ import annotations

# appId (decimal, as stored in LXP) → canonical device name
APP_ID_TO_DEVICE: dict[int, str] = {
    # Touch panels (input-only, no HA entities)
    1027: "T2.1",
    1029: "T4.1",
    1033: "T8.1",
    18434: "T2",
    18436: "T4",
    18440: "T8",
    # iON room controllers (RTR channels)
    1042: "iON2-4",
    1048: "iON8",
    # Switching actuators
    18468: "S4",
    18472: "S8",
    18473: "S16",
    18514: "S1",
    18515: "S1 secure ready",
    18498: "E1",
    18499: "E1 S RF",
    18530: "S1 RF",
    # Dimming actuators
    18544: "D1",
    18545: "D1 secure ready",
    18546: "D2",
    18548: "D4",
    18535: "D1 RF",
    18560: "D1 DALI",
    18561: "D1 DALI RF",
    18435: "D4 DALI",
    # Blind/shutter actuators
    18516: "J4",
    18513: "J4-6",
    18517: "J1",
    18519: "J1 secure ready",
    18520: "J8",
    18533: "J1 RF",
    # Heating actuators
    18502: "H6",
    18497: "H6 24V",
    18518: "H1",
    18532: "H1 RF",
    # Standalone thermostat
    18577: "R718",
    # Binary input modules
    18486: "B6",
    # Motion / presence detectors
    18512: "BI180",
    18485: "BI360",
    # Wireless push buttons / remotes (input-only)
    1557: "PB 4 RF",
    1573: "PS 1 RF",
    1621: "PJ 1 RF",
    1653: "PD 1 RF",
    1540: "T4 RF",
    # Not supported
    1170: "M130",
    18585: "M140",
    18482: "AC IR1",
    41154: "AC IR1",
    18536: "RF1",
}

# Device name → HA category
# "input_only"   → no HA entities created
# "unsupported"  → logged, no entities
# "switch"       → switch / light (heuristic decides)
# "light"        → light (dimmable)
# "cover"        → cover
# "climate"      → climate (actuator or thermostat)
# "binary_sensor"→ binary_sensor (contact / input)
# "motion"       → binary_sensor (motion)
DEVICE_CATEGORIES: dict[str, str] = {
    # Input-only
    "T2": "input_only",
    "T4": "input_only",
    "T8": "input_only",
    "T2.1": "input_only",
    "T4.1": "input_only",
    "T8.1": "input_only",
    "T4 RF": "input_only",
    "PB 4 RF": "input_only",
    "PS 1 RF": "input_only",
    "PJ 1 RF": "input_only",
    "PD 1 RF": "input_only",
    # Switches
    "S1": "switch",
    "S1 secure ready": "switch",
    "S1 RF": "switch",
    "S4": "switch",
    "S8": "switch",
    "S16": "switch",
    "E1": "switch",
    "E1 S RF": "switch",
    # Dimmers
    "D1": "light",
    "D1 secure ready": "light",
    "D1 RF": "light",
    "D1 DALI": "light",
    "D1 DALI RF": "light",
    "D2": "light",
    "D4": "light",
    "D4 DALI": "light",
    # Covers
    "J1": "cover",
    "J1 secure ready": "cover",
    "J1 RF": "cover",
    "J4": "cover",
    "J4-6": "cover",
    "J8": "cover",
    # Climate — actuators
    "H1": "climate",
    "H1 RF": "climate",
    "H6": "climate",
    "H6 24V": "climate",
    # Climate — thermostats
    "R718": "climate",
    "iON2-4": "climate",
    "iON8": "climate",
    # Binary input
    "B6": "binary_sensor",
    # Motion sensors
    "BI180": "motion",
    "BI360": "motion",
    # Not supported
    "M130": "unsupported",
    "M140": "unsupported",
    "AC IR1": "unsupported",
    "RF1": "unsupported",
}


def get_device_name(app_id: int | str) -> str | None:
    """Return canonical device name for the given appId, or None if unknown."""
    if app_id == "" or app_id is None:
        return None
    try:
        return APP_ID_TO_DEVICE.get(int(app_id))
    except (ValueError, TypeError):
        return None


def get_device_category(app_id: int | str) -> str | None:
    """Return HA category string for the given appId, or None if unknown."""
    name = get_device_name(app_id)
    if name is None:
        return None
    return DEVICE_CATEGORIES.get(name)
