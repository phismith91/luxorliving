"""Entity mapper for LUXORliving integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.const import Platform
from xknx.telegram.address import GroupAddress

from .const import DOMAIN
from .lxp_parser import LXPActuator, LXPDevice, LXPProject, LXPSensor
from .mapped_entity import MappedEntity
from .override_handler import OverrideHandler
from .platform_detector import PlatformDetector

_LOGGER = logging.getLogger(__name__)


class EntityMapper:
    """Maps LXP devices to Home Assistant entities.

    Uses dependency injection to delegate platform detection and override handling
    to specialized modules:
    - PlatformDetector: Determines HA platform from KNX role
    - OverrideHandler: Applies user-defined sensor overrides

    This design reduces EntityMapper from 523 to ~250 LOC by removing duplicate logic.
    """

    def __init__(
        self,
        project: LXPProject,
        overrides: dict[str, Any] | None = None,
        platform_detector: PlatformDetector | None = None,
        override_handler: OverrideHandler | None = None,
    ) -> None:
        """Initialize the mapper with optional dependency injection.

        Args:
            project: LXP project to map
            overrides: Override configuration dict
            platform_detector: Custom platform detector (default: new instance)
            override_handler: Custom override handler (default: new instance)
        """
        self.project = project
        self.entities: list[MappedEntity] = []
        self._overrides = overrides or {}

        # Dependency injection - use provided instances or create defaults
        self.platform_detector = platform_detector or PlatformDetector()
        self.override_handler = override_handler or OverrideHandler(self._overrides)

        # Automatically map all entities on init
        self.map_all()

    def map_all(self) -> list[MappedEntity]:
        """Map all devices to entities."""
        _LOGGER.info("Mapping %d devices to entities", len(self.project.devices))

        for device in self.project.devices:
            self._map_device(device)

        # Apply overrides via dependency injection
        try:
            self.override_handler.apply_overrides(self.entities)
        except Exception as err:
            _LOGGER.error("Failed applying overrides: %s", err)

        # Add health monitoring entity
        health_entity = MappedEntity(
            platform=Platform.BINARY_SENSOR,
            unique_id=f"{DOMAIN}_health",
            name="System Health",
            device_name="LUXORliving",
            device_id=f"{DOMAIN}_system",
            entity_type="health",
            datapoints={},
            attributes={},
            parameters={},
        )
        self.entities.append(health_entity)

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
        control_address = (
            datapoints.get("OnOff")
            or datapoints.get("SchaltenOnOff")
            or datapoints.get("UpDown")
            or datapoints.get("Dimmen%")
            or list(datapoints.values())[0]
            if datapoints
            else "unknown"
        )
        unique_id = f"{device.id}_{control_address}"

        # Generate friendly name
        name = actuator.name or f"{device.name} Ch{actuator.channel}"

        # Remove device name prefix if present to avoid duplication
        if name.startswith(device.name + " "):
            name = name[len(device.name) + 1 :]

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

        # Use PlatformDetector to find matching sensor role
        detected_role = None
        for role in datapoints.keys():
            if self.platform_detector.detect_platform(role) == Platform.SENSOR:
                detected_role = role
                break

        if detected_role:
            platform = Platform.SENSOR
            entity_type = detected_role.lower()
            device_class = self.platform_detector.get_device_class(detected_role)
            unit_of_measurement = self.platform_detector.get_unit(detected_role)

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

        # Remove device name prefix if present to avoid duplication
        if name.startswith(device.name + " "):
            name = name[len(device.name) + 1 :]

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
            entity_type=entity_type,  # type: ignore
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
        """Determine the platform based on datapoint roles.

        Delegates to PlatformDetector for role-to-platform mapping.
        """
        # Priority order for role detection
        control_roles = ["OnOff", "SchaltenOnOff", "Dimmen%", "UpDown"]

        for role in control_roles:
            if role in datapoints:
                return self.platform_detector.detect_platform(role)

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

        Uses PlatformDetector for role-to-attributes mapping.
        """
        # Role -> entity_name_suffix mapping (uses PlatformDetector for class/unit)
        wetterstation_roles = {
            "Temperatur": "Außentemperatur",
            "Windgeschwindigkeit": "Windgeschwindigkeit",
            "HelligkeitMitte": "Helligkeit Mitte",
            "HelligkeitLinks": "Helligkeit Links",
            "HelligkeitRechts": "Helligkeit Rechts",
            "Regen": "Regen",  # Binary/status
        }

        for role, name_suffix in wetterstation_roles.items():
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

            # Use PlatformDetector for device class and unit
            dev_class = self.platform_detector.get_device_class(role)
            unit = self.platform_detector.get_unit(role)

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
