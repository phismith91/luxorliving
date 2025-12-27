"""Entity mapper for LUXORliving integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.const import Platform
from xknx.telegram.address import GroupAddress

from .lxp_parser import LXPActuator, LXPDevice, LXPProject, LXPSensor

_LOGGER = logging.getLogger(__name__)


@dataclass
class MappedEntity:
    """Represents a mapped Home Assistant entity."""

    platform: Platform
    unique_id: str
    name: str
    device_name: str
    device_id: str
    entity_type: str  # light, switch, binary_sensor, etc.
    datapoints: dict[str, int]  # role -> address mapping
    attributes: dict[str, Any]  # Additional attributes
    parameters: dict[str, str]  # LXP parameters (timers, flags, etc.)


class EntityMapper:
    """Maps LXP devices to Home Assistant entities."""

    # Mapping rules based on datapoint roles
    ROLE_TO_PLATFORM = {
        # Light-related roles
        "OnOff": Platform.LIGHT,
        "SchaltenOnOff": Platform.LIGHT,
        "StatusOnOff": None,  # Status only, paired with control
        "status@OnOff": None,  # Status only
        "Dimmen%": Platform.LIGHT,
        "DimmenRel": None,  # Relative dimming, paired with absolute
        "status@Dim": None,  # Status only
        # Cover-related roles
        "UpDown": Platform.COVER,
        "StopStep": None,  # Paired with UpDown
        "status@UpDown": None,  # Status only
        # Binary sensor roles
        "MasterSlave": Platform.BINARY_SENSOR,
        # Sensor roles (Temperature, Humidity, Pressure, etc.)
        "Temperature": Platform.SENSOR,
        "Humidity": Platform.SENSOR,
        "Pressure": Platform.SENSOR,
        "CO2": Platform.SENSOR,
        "Brightness": Platform.SENSOR,
        "WindSpeed": Platform.SENSOR,
        "RainVolume": Platform.SENSOR,
        "AirQuality": Platform.SENSOR,
        # Climate-related (future)
        "Setpoint": Platform.CLIMATE,
        # Scene (future)
        "Scene": Platform.SCENE,
        # Generic
        "ZentralAus": None,  # Central off, not an entity
        "Panik": None,  # Panic mode, not an entity
    }

    # Unit of measurement mapping for sensor roles
    ROLE_TO_UNIT = {
        "Temperature": "°C",
        "Temperatur": "°C",  # German variant
        "Humidity": "%",
        "Pressure": "hPa",
        "CO2": "ppm",
        "Brightness": "lx",
        "HelligkeitMitte": "lx",  # German variant
        "HelligkeitLinks": "lx",
        "HelligkeitRechts": "lx",
        "WindSpeed": "m/s",
        "Windgeschwindigkeit": "km/h",  # German variant, km/h as per Wetterstation
        "RainVolume": "mm",
        "AirQuality": "ppm",
    }

    # Sensor device class mapping
    ROLE_TO_DEVICE_CLASS = {
        "Temperature": "temperature",
        "Temperatur": "temperature",  # German variant
        "Humidity": "humidity",
        "Pressure": "pressure",
        "CO2": None,  # No standard device class for CO2
        "Brightness": "illuminance",
        "HelligkeitMitte": "illuminance",  # German variant
        "HelligkeitLinks": "illuminance",
        "HelligkeitRechts": "illuminance",
        "WindSpeed": None,  # No standard device class for wind speed
        "Windgeschwindigkeit": None,  # German variant
        "RainVolume": "precipitation",
        "AirQuality": None,
    }

    def __init__(self, project: LXPProject, overrides: dict[str, Any] | None = None) -> None:
        """Initialize the mapper."""
        self.project = project
        self.entities: list[MappedEntity] = []
        self._overrides = overrides or {}
        # Automatically map all entities on init
        self.map_all()

    def map_all(self) -> list[MappedEntity]:
        """Map all devices to entities."""
        _LOGGER.info("Mapping %d devices to entities", len(self.project.devices))

        for device in self.project.devices:
            self._map_device(device)

        # Apply overrides to add/adjust entities
        try:
            self._apply_overrides()
        except Exception as err:
            _LOGGER.error("Failed applying overrides: %s", err)

        _LOGGER.info("Mapped %d entities total", len(self.entities))
        return self.entities

    def _map_device(self, device: LXPDevice) -> None:
        """Map a single device to entities."""
        # Map actuators (lights, switches, covers)
        for actuator in device.actuators:
            self._map_actuator(device, actuator)

        # Map sensors (binary sensors)
        for sensor in device.sensors:
            self._map_sensor(device, sensor)

    def _map_actuator(self, device: LXPDevice, actuator: LXPActuator) -> None:
        """Map an actuator to entities."""
        # Collect datapoints by role
        datapoints = {dp.role: dp.address for dp in actuator.datapoints}

        # Debug: Log extracted datapoints
        if datapoints:
            _LOGGER.debug(
                "📋 Actuator '%s' datapoints: %s",
                actuator.name,
                {
                    role: f"{addr} ({addr >> 11}/{(addr >> 8) & 0x7}/{addr & 0xFF})"
                    for role, addr in datapoints.items()
                },
            )

        # Determine platform based on primary roles
        platform = self._determine_platform(datapoints)
        if platform is None:
            _LOGGER.debug("Skipping actuator %s - no mappable roles", actuator.name)
            return

        # Determine entity type
        if platform == Platform.LIGHT:
            if "Dimmen%" in datapoints or "status@Dim" in datapoints:
                entity_type = "dimmable_light"
            else:
                entity_type = "light"
        else:
            entity_type = platform.value

        # Generate unique ID - use control address to ensure uniqueness
        # Different actuators can have same name but different addresses
        control_address = datapoints.get("OnOff") or datapoints.get("SchaltenOnOff") or \
                         datapoints.get("UpDown") or datapoints.get("Dimmen%") or \
                         list(datapoints.values())[0] if datapoints else "unknown"
        unique_id = f"{device.id}_{control_address}"

        # Generate friendly name
        name = actuator.name or f"{device.name} Ch{actuator.channel}"

        # Create mapped entity
        entity = MappedEntity(
            platform=platform,
            unique_id=unique_id,
            name=name,
            device_name=device.name,
            device_id=device.id,
            entity_type=entity_type,
            datapoints=datapoints,
            attributes={
                "channel": actuator.channel,
                "on_icon": actuator.on_icon,
                "off_icon": actuator.off_icon,
                "use_case": actuator.use_case,
                "serial_number": device.serial_number,
                "knx_address": device.address,
            },
            parameters=actuator.parameters,
        )

        self.entities.append(entity)
        _LOGGER.debug("Mapped %s actuator '%s' to %s", entity_type, name, platform)

    def _map_sensor(self, device: LXPDevice, sensor: LXPSensor) -> None:
        """Map a sensor to entities."""
        # Collect datapoints by role
        datapoints = {dp.role: dp.address for dp in sensor.datapoints}

        if not datapoints:
            _LOGGER.debug("Skipping sensor %s - no datapoints", sensor.name)
            return

        # Special handling for Wetterstation: extract individual sensor entities
        if "wetterstation" in device.name.lower():
            self._map_wetterstation_sensor(device, sensor, datapoints)
            return

        # Determine platform based on sensor roles
        # Priority 1: Check for sensor types (Temperature, Humidity, etc.)
        platform = None
        entity_type = None
        device_class = None
        unit_of_measurement = None

        for role, unit_map in self.ROLE_TO_UNIT.items():
            if role in datapoints:
                platform = Platform.SENSOR
                entity_type = role.lower()
                device_class = self.ROLE_TO_DEVICE_CLASS.get(role)
                unit_of_measurement = self.ROLE_TO_UNIT.get(role)
                break

        # Priority 2: Check for binary control/status
        if platform is None:
            map_onoff_to_binary = bool(self._overrides.get("map_onoff_to_binary", False))
            if "status@OnOff" in datapoints and "OnOff" not in datapoints:
                # Pure status sensor -> binary_sensor
                platform = Platform.BINARY_SENSOR
                entity_type = "binary_sensor"
            elif "OnOff" in datapoints:
                # Control sensor -> could be switch or binary_sensor
                # For now, treat motion sensors as binary_sensor
                if "MasterSlave" in datapoints or sensor.sensor_type == 1:
                    platform = Platform.BINARY_SENSOR
                    entity_type = "motion"
                else:
                    # Regular switch sensor -> switch platform
                    if map_onoff_to_binary:
                        platform = Platform.BINARY_SENSOR
                        entity_type = "binary_sensor"
                    else:
                        platform = Platform.SWITCH
                        entity_type = "switch"

        if platform is None:
            _LOGGER.debug("Skipping sensor %s - no mappable roles", sensor.name)
            return

        # Generate unique ID - use the first datapoint address to ensure uniqueness
        # Different sensors can have same name but different addresses
        address = list(datapoints.values())[0] if datapoints else "unknown"
        unique_id = f"{device.id}_{address}"

        # Generate friendly name
        name = sensor.name or f"{device.name} Ch{sensor.channel}"

        # Create mapped entity with sensor-specific attributes
        attributes = {
            "channel": sensor.channel,
            "sensor_type": sensor.sensor_type,
            "serial_number": device.serial_number,
            "knx_address": device.address,
        }

        # Add sensor-specific attributes
        if device_class:
            attributes["device_class"] = device_class
        if unit_of_measurement:
            attributes["unit_of_measurement"] = unit_of_measurement

        entity = MappedEntity(
            platform=platform,
            unique_id=unique_id,
            name=name,
            device_name=device.name,
            device_id=device.id,
            entity_type=entity_type,
            datapoints=datapoints,
            attributes=attributes,
            parameters=sensor.parameters,
        )

        self.entities.append(entity)
        _LOGGER.debug(
            "Mapped sensor '%s' to %s (type=%s, unit=%s)",
            name,
            platform,
            entity_type,
            unit_of_measurement,
        )

    def _determine_platform(self, datapoints: dict[str, int]) -> Platform | None:
        """Determine the platform based on datapoint roles."""
        # Priority order for role detection
        control_roles = ["OnOff", "SchaltenOnOff", "Dimmen%", "UpDown"]

        for role in control_roles:
            if role in datapoints:
                return self.ROLE_TO_PLATFORM.get(role)

        return None

    def get_entities_by_platform(self, platform: Platform) -> list[MappedEntity]:
        """Get all entities for a specific platform."""
        return [e for e in self.entities if e.platform == platform]

    def get_entity_by_unique_id(self, unique_id: str) -> MappedEntity | None:
        """Get entity by unique ID."""
        for entity in self.entities:
            if entity.unique_id == unique_id:
                return entity
        return None

    def get_group_address_label_map(self) -> dict[str, list[str]]:
        """Build a map of KNX group address string → list of labels 'Name (ID)'.

        This is used to enrich KNX logs with human-friendly names.
        """
        ga_labels: dict[str, list[str]] = {}
        for entity in self.entities:
            label = f"{entity.name} ({entity.unique_id})"
            for role, addr in entity.datapoints.items():
                try:
                    ga_str = str(GroupAddress(addr))
                except Exception:
                    # Fallback: derive GA via bit masks (main/line/group)
                    ga_str = f"{addr >> 11}/{(addr >> 8) & 0x7}/{addr & 0xFF}"
                if ga_str not in ga_labels:
                    ga_labels[ga_str] = []
                if label not in ga_labels[ga_str]:
                    ga_labels[ga_str].append(label)
        return ga_labels

    def get_individual_address_label_map(self) -> dict[str, list[str]]:
        """Build a map of KNX individual address (IA) → labels 'DeviceName (DeviceID)'."""
        ia_labels: dict[str, list[str]] = {}
        for entity in self.entities:
            # Device-level label
            dev_label = f"{entity.device_name} ({entity.device_id})"
            ia = entity.attributes.get("knx_address")
            if not ia:
                continue
            ia_str = str(ia)
            if ia_str not in ia_labels:
                ia_labels[ia_str] = []
            if dev_label not in ia_labels[ia_str]:
                ia_labels[ia_str].append(dev_label)
        return ia_labels

    # --- Wetterstation special handling ---
    def _map_wetterstation_sensor(
        self, device: LXPDevice, sensor: LXPSensor, datapoints: dict[str, int]
    ) -> None:
        """Create individual sensor entities from Wetterstation datapoints.
        
        Wetterstation sensors have multiple roles (Temperatur, HelligkeitMitte, etc.)
        but are marked affected=0. We create separate entities for each role.
        """
        # Role -> (entity_name_suffix, device_class, unit)
        wetterstation_roles = {
            "Temperatur": ("Außentemperatur", "temperature", "°C"),
            "Windgeschwindigkeit": ("Windgeschwindigkeit", None, "km/h"),
            "HelligkeitMitte": ("Helligkeit Mitte", "illuminance", "lx"),
            "HelligkeitLinks": ("Helligkeit Links", "illuminance", "lx"),
            "HelligkeitRechts": ("Helligkeit Rechts", "illuminance", "lx"),
            "Regen": ("Regen", None, None),  # Binary/status
        }

        for role, (name_suffix, dev_class, unit) in wetterstation_roles.items():
            if role not in datapoints:
                continue

            addr = datapoints[role]
            unique_id = f"{device.id}_{addr}"

            # Check if already exists (avoid duplicates)
            if any(e.unique_id == unique_id for e in self.entities):
                continue

            # Skip non-sensor roles
            if role == "Regen":
                # Regen is binary (OnOff), skip for now
                continue

            entity = MappedEntity(
                platform=Platform.SENSOR,
                unique_id=unique_id,
                name=f"{device.name} {name_suffix}",
                device_name=device.name,
                device_id=device.id,
                entity_type=role.lower(),
                datapoints={role: addr},
                attributes={
                    "device_class": dev_class,
                    "unit_of_measurement": unit,
                    "channel": sensor.channel,
                    "sensor_type": sensor.sensor_type,
                    "serial_number": device.serial_number,
                    "knx_address": device.address,
                },
                parameters=sensor.parameters,
            )

            self.entities.append(entity)
            _LOGGER.debug(
                "Mapped Wetterstation sensor '%s' (%s) at address %s",
                entity.name,
                role,
                addr,
            )

    # --- Overrides support ---
    def _apply_overrides(self) -> None:
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
                device_class = ov.get("device_class") if ov.get("device_class") else self.ROLE_TO_DEVICE_CLASS.get(role)

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

                self.entities.append(entity)
                _LOGGER.debug("Applied override sensor '%s' (%s) at %s", name, role, address)
            except Exception as err:
                _LOGGER.error("Failed to apply override %s: %s", ov, err)

    @staticmethod
    def _normalize_address(addr: Any) -> int | None:
        """Convert GA string 'M/L/G' or int-like to int encoding used in LXP.
        Returns None if invalid.
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
        except Exception:
            return None
