"""LXP Parser for LUXORliving project files."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

try:
    from defusedxml import ElementTree as ET
except ImportError:
    # Fallback to standard library with warning
    import warnings
    import xml.etree.ElementTree as ET

    warnings.warn(
        "defusedxml not available, using xml.etree.ElementTree. "
        "This may be vulnerable to XML attacks. Install defusedxml for production use.",
        UserWarning,
        stacklevel=2,
    )

_LOGGER = logging.getLogger(__name__)

NAMESPACE = "{http://www.theben.de/LUXORplug/2016/12}"


@dataclass
class CacheEntry:
    """Cache entry for parsed LXP projects."""

    project: LXPProject
    file_hash: str
    mtime: float
    access_count: int = 0
    created_at: float = 0.0


class LXPCache:
    """Cache for parsed LXP projects to avoid re-parsing on reloads."""

    def __init__(self, max_size: int = 10, ttl_seconds: int = 3600):
        """Initialize the cache.

        Args:
            max_size: Maximum number of cached projects
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _get_cache_key(self, file_path: Path, include_unaffected: bool) -> str:
        """Generate a unique cache key for the file and parsing options."""
        return f"{file_path}:{include_unaffected}"

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of the file content."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._calculate_file_hash_sync, file_path)

    def _calculate_file_hash_sync(self, file_path: Path) -> str:
        """Calculate SHA256 hash of the file content (synchronous)."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired."""
        import time

        return (time.time() - entry.created_at) > self._ttl_seconds

    def _evict_oldest(self):
        """Evict the oldest cache entry when max size is reached."""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]
        _LOGGER.debug("Evicted oldest cache entry: %s", oldest_key)

    async def get_or_parse(self, file_path: Path, include_unaffected: bool = False) -> LXPProject:
        """Get cached project or parse and cache it.

        Args:
            file_path: Path to the LXP file
            include_unaffected: Whether to include unaffected sensors/actuators

        Returns:
            Parsed LXPProject
        """
        import time

        cache_key = self._get_cache_key(file_path, include_unaffected)

        # Check if we have a valid cached entry
        if cache_key in self._cache:
            entry = self._cache[cache_key]

            # Check if file has changed
            try:
                current_mtime = file_path.stat().st_mtime
                current_hash = await self._calculate_file_hash(file_path)

                if (
                    entry.mtime == current_mtime
                    and entry.file_hash == current_hash
                    and not self._is_expired(entry)
                ):

                    entry.access_count += 1
                    self._hits += 1
                    _LOGGER.debug(
                        "LXP Cache HIT for %s (access #%d)", file_path.name, entry.access_count
                    )
                    return entry.project
                else:
                    # File changed or expired, remove from cache
                    del self._cache[cache_key]
                    _LOGGER.debug("LXP Cache INVALIDATED for %s", file_path.name)
            except (OSError, IOError) as e:
                _LOGGER.warning("Error checking file %s: %s", file_path, e)
                # Remove from cache on error
                del self._cache[cache_key]

        # Cache miss - parse the file
        self._misses += 1
        _LOGGER.debug("LXP Cache MISS for %s", file_path.name)

        parser = LXPParser(file_path, include_unaffected=include_unaffected)
        project = await parser.parse()

        # Create cache entry
        file_hash = await self._calculate_file_hash(file_path)
        mtime = file_path.stat().st_mtime

        entry = CacheEntry(
            project=project,
            file_hash=file_hash,
            mtime=mtime,
            access_count=1,
            created_at=time.time(),
        )

        # Evict if cache is full
        if len(self._cache) >= self._max_size:
            self._evict_oldest()

        self._cache[cache_key] = entry
        _LOGGER.info("LXP Cache STORED for %s", file_path.name)

        return project

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        total_accesses = self._hits + self._misses
        hit_rate = (self._hits / total_accesses * 100) if total_accesses > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 1),
            "total_accesses": total_accesses,
        }

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        _LOGGER.info("LXP Cache cleared")


# Global cache instance
_lxp_cache = LXPCache()


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
    parameters: dict[str, str]


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
    parameters: dict[str, str]


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

    def __init__(self, file_path: str | Path, include_unaffected: bool = False) -> None:
        """Initialize the parser."""
        self.file_path = Path(file_path)
        self.tree: ET.ElementTree | None = None
        self.root: ET.Element | None = None
        # When true, sensors/actuators with affected="0" are also parsed (advanced/testing)
        self.include_unaffected = include_unaffected

    @staticmethod
    def _is_weather_station_device(name: str) -> bool:
        """Return True if the device name indicates a weather station.

        Matches German and English naming variants commonly used in LXP exports.
        """
        lower = name.lower()
        return "wetterstation" in lower or "weather station" in lower

    @classmethod
    async def parse_cached(
        cls, file_path: str | Path, include_unaffected: bool = False
    ) -> LXPProject:
        """Parse LXP file with caching for improved performance.

        This method uses the global LXP cache to avoid re-parsing unchanged files.
        Use this instead of creating a parser instance and calling parse() directly.

        Args:
            file_path: Path to the LXP file
            include_unaffected: Whether to include unaffected sensors/actuators

        Returns:
            Parsed LXPProject
        """
        return await _lxp_cache.get_or_parse(Path(file_path), include_unaffected)

    @classmethod
    def get_cache_stats(cls) -> Dict[str, int]:
        """Get LXP cache statistics."""
        return _lxp_cache.get_stats()

    @classmethod
    def clear_cache(cls):
        """Clear the LXP cache."""
        _lxp_cache.clear()

    async def parse(self) -> LXPProject:
        """Parse the LXP file and return a project object."""
        _LOGGER.info("Parsing LXP file: %s", self.file_path)

        # Parse XML asynchronously to avoid blocking the event loop
        self.tree = await asyncio.to_thread(ET.parse, self.file_path)
        if self.tree is None:
            raise ValueError(f"Failed to parse XML file: {self.file_path}")
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

        if self.root is None:
            _LOGGER.warning("No root element available")
            return devices

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

        # Decide whether to force-include unaffected elements for this device
        force_include_unaffected = self._is_weather_station_device(name)

        # Parse sensors
        sensors = []
        for sensor_elem in device_elem.findall(f"{NAMESPACE}sensor"):
            sensor = self._parse_sensor(
                sensor_elem, force_include_unaffected=force_include_unaffected
            )
            if sensor and sensor.datapoints:  # Only include sensors with datapoints
                sensors.append(sensor)

        # Parse actuators
        actuators = []
        for actuator_elem in device_elem.findall(f"{NAMESPACE}actuator"):
            actuator = self._parse_actuator(
                actuator_elem, force_include_unaffected=force_include_unaffected
            )
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

    def _parse_sensor(
        self, sensor_elem: ET.Element, *, force_include_unaffected: bool = False
    ) -> LXPSensor | None:
        """Parse a sensor element."""
        name = sensor_elem.get("name", "")
        name = self._clean_duplicate_names(name)  # Clean duplicate names
        channel = int(sensor_elem.get("channel", "0"))
        sensor_id = sensor_elem.get("id", "")
        affected = sensor_elem.get("affected", "0") == "1"

        # Skip unaffected sensors unless explicitly included or forced by device type
        if not affected and not (self.include_unaffected or force_include_unaffected):
            return None

        # Parse all parameters
        parameters = {}
        sensor_type = 0
        for param in sensor_elem.findall(f"{NAMESPACE}parameter"):
            param_name = param.get("name", "")
            param_value = param.get("value", "")
            if param_name:
                parameters[param_name] = param_value
                if param_name == "sensorTyp":
                    sensor_type = int(param_value) if param_value else 0

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
            parameters=parameters,
        )

    @staticmethod
    def _clean_duplicate_names(name: str) -> str:
        """Clean duplicate consecutive words in actuator/sensor names.

        Some LXP files have names like "S16-2 S16-2 C9 Bad 3 Heizung"
        where the device name appears twice. This removes consecutive duplicates.
        """
        if not name:
            return name

        words = name.split()
        if len(words) < 2:
            return name

        # Remove consecutive duplicates
        cleaned_words = [words[0]]
        for word in words[1:]:
            if word != cleaned_words[-1]:
                cleaned_words.append(word)

        return " ".join(cleaned_words)

    def _parse_actuator(
        self, actuator_elem: ET.Element, *, force_include_unaffected: bool = False
    ) -> LXPActuator | None:
        """Parse an actuator element."""
        name = actuator_elem.get("name", "")
        name = self._clean_duplicate_names(name)  # Clean duplicate names
        channel = int(actuator_elem.get("channel", "0"))
        channel = int(actuator_elem.get("channel", "0"))
        actuator_id = actuator_elem.get("id", "")
        affected = actuator_elem.get("affected", "0") == "1"
        on_icon = actuator_elem.get("onIcon", "Default_ON")
        off_icon = actuator_elem.get("offIcon", "Default_OFF")

        # Skip unaffected actuators unless explicitly included or forced by device type
        if not affected and not (self.include_unaffected or force_include_unaffected):
            return None

        # Parse all parameters
        parameters = {}
        use_case = 0
        for param in actuator_elem.findall(f"{NAMESPACE}parameter"):
            param_name = param.get("name", "")
            param_value = param.get("value", "")
            if param_name:
                parameters[param_name] = param_value
                if param_name == "useCase":
                    use_case = int(param_value) if param_value else 0

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
            parameters=parameters,
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


# Global LXP cache instance
_lxp_cache = LXPCache(max_size=10, ttl_seconds=3600)


def get_lxp_cache_stats() -> Dict[str, int]:
    """Get global LXP cache statistics for health monitoring."""
    return _lxp_cache.get_stats()


# Global LXP cache instance
_lxp_cache = LXPCache(max_size=10, ttl_seconds=3600)


def get_lxp_cache_stats() -> Dict[str, int]:
    """Get LXP cache statistics for health monitoring."""
    return _lxp_cache.get_stats()
