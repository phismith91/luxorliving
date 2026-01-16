"""MappedEntity dataclass for representing mapped Home Assistant entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.const import Platform


@dataclass
class MappedEntity:
    """Represents a mapped Home Assistant entity.

    Extracted to separate module to avoid circular imports
    when used by both EntityMapper and OverrideHandler.
    """

    platform: Platform
    unique_id: str
    name: str
    device_name: str
    device_id: str
    entity_type: str  # light, switch, binary_sensor, etc.
    datapoints: dict[str, int]  # role -> address mapping
    attributes: dict[str, Any]  # Additional attributes
    parameters: dict[str, str]  # LXP parameters (timers, flags, etc.)
