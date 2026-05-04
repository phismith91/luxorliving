"""Platform detection for KNX datapoint roles.

This module is responsible for detecting the appropriate Home Assistant platform
from KNX datapoint roles (e.g., "OnOff" → Light, "Temperature" → Sensor).

Extracted from EntityMapper to follow Single Responsibility Principle.
"""

from __future__ import annotations

from typing import Optional

from homeassistant.const import Platform


class PlatformDetector:
    """Detects Home Assistant platform from KNX datapoint role.

    This class provides mapping from KNX datapoint roles to Home Assistant
    platforms, units of measurement, and device classes.

    Example:
        detector = PlatformDetector()
        platform = detector.detect_platform("OnOff")  # Platform.LIGHT
        unit = detector.get_unit("Temperature")  # "°C"
        device_class = detector.get_device_class("Temperature")  # "temperature"
    """

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
        "StepStop": None,  # Paired with UpDown
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

    def detect_platform(self, role: str) -> Optional[Platform]:
        """Detect Home Assistant platform from KNX datapoint role.

        Args:
            role: KNX datapoint role (e.g., "OnOff", "Temperature", "Dimmen%")

        Returns:
            Platform enum if role maps to a platform, None otherwise.
            None is returned for:
            - Status-only roles (e.g., "StatusOnOff", "status@OnOff")
            - Paired roles (e.g., "DimmenRel", "StepStop")
            - Special roles (e.g., "ZentralAus", "Panik")
            - Unknown roles

        Example:
            >>> detector = PlatformDetector()
            >>> detector.detect_platform("OnOff")
            <Platform.LIGHT: 'light'>
            >>> detector.detect_platform("Temperature")
            <Platform.SENSOR: 'sensor'>
            >>> detector.detect_platform("StatusOnOff")
            None
        """
        return self.ROLE_TO_PLATFORM.get(role)

    def get_unit(self, role: str) -> Optional[str]:
        """Get unit of measurement for sensor role.

        Args:
            role: KNX datapoint role (e.g., "Temperature", "Humidity")

        Returns:
            Unit of measurement string or None if role has no unit.

        Example:
            >>> detector = PlatformDetector()
            >>> detector.get_unit("Temperature")
            '°C'
            >>> detector.get_unit("Humidity")
            '%'
            >>> detector.get_unit("OnOff")
            None
        """
        return self.ROLE_TO_UNIT.get(role)

    def get_device_class(self, role: str) -> Optional[str]:
        """Get Home Assistant device class for sensor role.

        Args:
            role: KNX datapoint role (e.g., "Temperature", "Humidity")

        Returns:
            Device class string or None if role has no device class.

        Example:
            >>> detector = PlatformDetector()
            >>> detector.get_device_class("Temperature")
            'temperature'
            >>> detector.get_device_class("Brightness")
            'illuminance'
            >>> detector.get_device_class("CO2")
            None
        """
        return self.ROLE_TO_DEVICE_CLASS.get(role)
