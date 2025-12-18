"""LXP Parser for LUXORliving project files."""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

NAMESPACE = "{http://www.theben.de/LUXORplug/2016/12}"


@dataclass
class LXPDatapoint:
    """Represents a datapoint in the LXP file."""

    address: int
    role: str
    id: str


@dataclass
class LXPSensor:
    """Represents a sensor in the LXP file."""

    name: str
    channel: int
    id: str
    sensor_type: int
    datapoints: list[LXPDatapoint]


@dataclass
class LXPActuator:
    """Represents an actuator in the LXP file."""

    name: str
    channel: int
    id: str
    on_icon: str
    off_icon: str
    use_case: int
    datapoints: list[LXPDatapoint]


@dataclass
class LXPDevice:
    """Represents a device in the LXP file."""

    serial_number: str
    name: str
    app_id: str
    address: str
    id: str
    sensors: list[LXPSensor]
    actuators: list[LXPActuator]


@dataclass
class LXPProject:
    """Represents a complete LXP project."""

    name: str
    gateway_address: str
    gateway_port: int
    devices: list[LXPDevice]


class LXPParser:
    """Parser for LUXORliving .lxp XML files."""

    def __init__(self, file_path: str | Path) -> None:
        """Initialize the parser."""
        self.file_path = Path(file_path)
        self.tree: ET.ElementTree | None = None
        self.root: ET.Element | None = None

    def parse(self) -> LXPProject:
        """Parse the LXP file and return a project object."""
        _LOGGER.info("Parsing LXP file: %s", self.file_path)

        # Parse XML
        self.tree = ET.parse(self.file_path)
        self.root = self.tree.getroot()

        # Extract project info
        project_name = self.root.get("name", "Unknown Project")
        _LOGGER.debug("Project name: %s", project_name)

        # Extract gateway info
        adapter = self.root.find(f"{NAMESPACE}adapter")
        gateway_address = "192.168.1.3"  # Default
        gateway_port = 3671  # KNX/IP default

        if adapter is not None:
            addr_str = adapter.get("address", "192.168.1.3:3671")
            if ":" in addr_str:
                gateway_address, port_str = addr_str.split(":")
                gateway_port = int(port_str)
            else:
                gateway_address = addr_str

        _LOGGER.debug("Gateway: %s:%d", gateway_address, gateway_port)

        # Parse devices
        devices = self._parse_devices()
        _LOGGER.info(
            "Parsed %d devices from %s",
            len(devices),
            self.file_path.name,
        )

        return LXPProject(
            name=project_name,
            gateway_address=gateway_address,
            gateway_port=gateway_port,
            devices=devices,
        )

    def _parse_devices(self) -> list[LXPDevice]:
        """Parse all devices from the LXP file."""
        devices: list[LXPDevice] = []

        devices_elem = self.root.find(f"{NAMESPACE}devices")
        if devices_elem is None:
            _LOGGER.warning("No devices element found")
            return devices

        for device_elem in devices_elem.findall(f"{NAMESPACE}device"):
            device = self._parse_device(device_elem)
            if device:
                devices.append(device)

        return devices

    def _parse_device(self, device_elem: ET.Element) -> LXPDevice | None:
        """Parse a single device element."""
        serial = device_elem.get("serialNumber", "")
        name = device_elem.get("name", "")
        app_id = device_elem.get("appId", "")
        address = device_elem.get("address", "")
        dev_id = device_elem.get("id", "")

        if not name:
            _LOGGER.warning("Device without name found, skipping")
            return None

        _LOGGER.debug("Parsing device: %s (%s)", name, serial)

        # Parse sensors
        sensors = []
        for sensor_elem in device_elem.findall(f"{NAMESPACE}sensor"):
            sensor = self._parse_sensor(sensor_elem)
            if sensor and sensor.datapoints:  # Only include sensors with datapoints
                sensors.append(sensor)

        # Parse actuators
        actuators = []
        for actuator_elem in device_elem.findall(f"{NAMESPACE}actuator"):
            actuator = self._parse_actuator(actuator_elem)
            if actuator and actuator.datapoints:  # Only include actuators with datapoints
                actuators.append(actuator)

        return LXPDevice(
            serial_number=serial,
            name=name,
            app_id=app_id,
            address=address,
            id=dev_id,
            sensors=sensors,
            actuators=actuators,
        )

    def _parse_sensor(self, sensor_elem: ET.Element) -> LXPSensor | None:
        """Parse a sensor element."""
        name = sensor_elem.get("name", "")
        channel = int(sensor_elem.get("channel", "0"))
        sensor_id = sensor_elem.get("id", "")
        affected = sensor_elem.get("affected", "0") == "1"

        # Skip unaffected sensors
        if not affected:
            return None

        # Get sensor type from parameter
        sensor_type = 0
        for param in sensor_elem.findall(f"{NAMESPACE}parameter"):
            if param.get("name") == "sensorTyp":
                sensor_type = int(param.get("value", "0"))
                break

        # Parse datapoints
        datapoints = []
        for dp_elem in sensor_elem.findall(f"{NAMESPACE}datapoint"):
            datapoint = self._parse_datapoint(dp_elem)
            if datapoint:
                datapoints.append(datapoint)

        return LXPSensor(
            name=name,
            channel=channel,
            id=sensor_id,
            sensor_type=sensor_type,
            datapoints=datapoints,
        )

    def _parse_actuator(self, actuator_elem: ET.Element) -> LXPActuator | None:
        """Parse an actuator element."""
        name = actuator_elem.get("name", "")
        channel = int(actuator_elem.get("channel", "0"))
        actuator_id = actuator_elem.get("id", "")
        affected = actuator_elem.get("affected", "0") == "1"
        on_icon = actuator_elem.get("onIcon", "Default_ON")
        off_icon = actuator_elem.get("offIcon", "Default_OFF")

        # Skip unaffected actuators
        if not affected:
            return None

        # Get use case from parameter
        use_case = 0
        for param in actuator_elem.findall(f"{NAMESPACE}parameter"):
            if param.get("name") == "useCase":
                use_case = int(param.get("value", "0"))
                break

        # Parse datapoints
        datapoints = []
        for dp_elem in actuator_elem.findall(f"{NAMESPACE}datapoint"):
            datapoint = self._parse_datapoint(dp_elem)
            if datapoint:
                datapoints.append(datapoint)

        return LXPActuator(
            name=name,
            channel=channel,
            id=actuator_id,
            on_icon=on_icon,
            off_icon=off_icon,
            use_case=use_case,
            datapoints=datapoints,
        )

    def _parse_datapoint(self, dp_elem: ET.Element) -> LXPDatapoint | None:
        """Parse a datapoint element."""
        address_str = dp_elem.get("address", "")
        role = dp_elem.get("role", "")
        dp_id = dp_elem.get("id", "")

        if not address_str or not role:
            return None

        try:
            address = int(address_str)
        except ValueError:
            _LOGGER.warning("Invalid datapoint address: %s", address_str)
            return None

        return LXPDatapoint(
            address=address,
            role=role,
            id=dp_id,
        )
