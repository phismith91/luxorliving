"""Entity mapper for LUXORliving integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.const import Platform

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
        # Climate-related (future)
        "Temperature": Platform.SENSOR,
        "Setpoint": Platform.CLIMATE,
        # Scene (future)
        "Scene": Platform.SCENE,
        # Generic
        "ZentralAus": None,  # Central off, not an entity
        "Panik": None,  # Panic mode, not an entity
    }

    def __init__(self, project: LXPProject) -> None:
        """Initialize the mapper."""
        self.project = project
        self.entities: list[MappedEntity] = []
        # Automatically map all entities on init
        self.map_all()

    def map_all(self) -> list[MappedEntity]:
        """Map all devices to entities."""
        _LOGGER.info("Mapping %d devices to entities", len(self.project.devices))

        for device in self.project.devices:
            self._map_device(device)

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
                {role: f"{addr} ({addr >> 11}/{(addr >> 8) & 0x7}/{addr & 0xFF})" 
                 for role, addr in datapoints.items()}
            )

        # Determine platform based on primary roles
        platform = self._determine_platform(datapoints)
        if platform is None:
            _LOGGER.debug(
                "Skipping actuator %s - no mappable roles", actuator.name
            )
            return

        # Determine entity type
        if platform == Platform.LIGHT:
            if "Dimmen%" in datapoints or "status@Dim" in datapoints:
                entity_type = "dimmable_light"
            else:
                entity_type = "light"
        else:
            entity_type = platform.value

        # Generate unique ID
        unique_id = f"{device.id}_{actuator.id}"

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
        )

        self.entities.append(entity)
        _LOGGER.debug(
            "Mapped %s actuator '%s' to %s", entity_type, name, platform
        )

    def _map_sensor(self, device: LXPDevice, sensor: LXPSensor) -> None:
        """Map a sensor to entities."""
        # Collect datapoints by role
        datapoints = {dp.role: dp.address for dp in sensor.datapoints}

        # Sensors are typically binary_sensors or switches
        # Determine based on roles
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
                platform = Platform.SWITCH
                entity_type = "switch"
        else:
            _LOGGER.debug("Skipping sensor %s - no mappable roles", sensor.name)
            return

        # Generate unique ID
        unique_id = f"{device.id}_{sensor.id}"

        # Generate friendly name
        name = sensor.name or f"{device.name} Ch{sensor.channel}"

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
                "channel": sensor.channel,
                "sensor_type": sensor.sensor_type,
                "serial_number": device.serial_number,
                "knx_address": device.address,
            },
        )

        self.entities.append(entity)
        _LOGGER.debug("Mapped sensor '%s' to %s", name, platform)

    def _determine_platform(self, datapoints: dict[str, int]) -> Platform | None:
        """Determine the platform based on datapoint roles."""
        # Priority order for role detection
        control_roles = ["OnOff", "SchaltenOnOff", "Dimmen%", "UpDown"]

        for role in control_roles:
            if role in datapoints:
                return self.ROLE_TO_PLATFORM.get(role)

        return None

    def get_entities_by_platform(
        self, platform: Platform
    ) -> list[MappedEntity]:
        """Get all entities for a specific platform."""
        return [e for e in self.entities if e.platform == platform]

    def get_entity_by_unique_id(self, unique_id: str) -> MappedEntity | None:
        """Get entity by unique ID."""
        for entity in self.entities:
            if entity.unique_id == unique_id:
                return entity
        return None
