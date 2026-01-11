"""Unit tests for PlatformDetector module."""

import pytest
from homeassistant.const import Platform

from custom_components.luxor_living.platform_detector import PlatformDetector


class TestPlatformDetection:
    """Test platform detection from KNX roles."""

    def test_onoff_maps_to_light(self):
        """OnOff role maps to Light platform."""
        detector = PlatformDetector()
        assert detector.detect_platform("OnOff") == Platform.LIGHT

    def test_schalten_onoff_maps_to_light(self):
        """SchaltenOnOff (German) maps to Light platform."""
        detector = PlatformDetector()
        assert detector.detect_platform("SchaltenOnOff") == Platform.LIGHT

    def test_dimmen_maps_to_light(self):
        """Dimmen% role maps to Light platform."""
        detector = PlatformDetector()
        assert detector.detect_platform("Dimmen%") == Platform.LIGHT

    def test_updown_maps_to_cover(self):
        """UpDown role maps to Cover platform."""
        detector = PlatformDetector()
        assert detector.detect_platform("UpDown") == Platform.COVER

    def test_temperature_maps_to_sensor(self):
        """Temperature role maps to Sensor platform."""
        detector = PlatformDetector()
        assert detector.detect_platform("Temperature") == Platform.SENSOR

    def test_humidity_maps_to_sensor(self):
        """Humidity role maps to Sensor platform."""
        detector = PlatformDetector()
        assert detector.detect_platform("Humidity") == Platform.SENSOR

    def test_setpoint_maps_to_climate(self):
        """Setpoint role maps to Climate platform."""
        detector = PlatformDetector()
        assert detector.detect_platform("Setpoint") == Platform.CLIMATE

    def test_masterslave_maps_to_binary_sensor(self):
        """MasterSlave role maps to Binary Sensor platform."""
        detector = PlatformDetector()
        assert detector.detect_platform("MasterSlave") == Platform.BINARY_SENSOR

    def test_status_role_returns_none(self):
        """Status-only roles return None (not a controllable entity)."""
        detector = PlatformDetector()
        assert detector.detect_platform("StatusOnOff") is None
        assert detector.detect_platform("status@OnOff") is None
        assert detector.detect_platform("status@Dim") is None
        assert detector.detect_platform("status@UpDown") is None

    def test_paired_role_returns_none(self):
        """Paired roles (dimming relative, stop/step) return None."""
        detector = PlatformDetector()
        assert detector.detect_platform("DimmenRel") is None
        assert detector.detect_platform("StopStep") is None

    def test_special_role_returns_none(self):
        """Special roles (central off, panic) return None."""
        detector = PlatformDetector()
        assert detector.detect_platform("ZentralAus") is None
        assert detector.detect_platform("Panik") is None

    def test_unknown_role_returns_none(self):
        """Unknown role returns None."""
        detector = PlatformDetector()
        assert detector.detect_platform("UnknownRole123") is None


class TestUnitOfMeasurement:
    """Test unit of measurement retrieval."""

    def test_temperature_returns_celsius(self):
        """Temperature role returns °C."""
        detector = PlatformDetector()
        assert detector.get_unit("Temperature") == "°C"

    def test_temperatur_german_returns_celsius(self):
        """Temperatur (German) returns °C."""
        detector = PlatformDetector()
        assert detector.get_unit("Temperatur") == "°C"

    def test_humidity_returns_percent(self):
        """Humidity role returns %."""
        detector = PlatformDetector()
        assert detector.get_unit("Humidity") == "%"

    def test_pressure_returns_hpa(self):
        """Pressure role returns hPa."""
        detector = PlatformDetector()
        assert detector.get_unit("Pressure") == "hPa"

    def test_co2_returns_ppm(self):
        """CO2 role returns ppm."""
        detector = PlatformDetector()
        assert detector.get_unit("CO2") == "ppm"

    def test_brightness_returns_lux(self):
        """Brightness role returns lx."""
        detector = PlatformDetector()
        assert detector.get_unit("Brightness") == "lx"

    def test_helligkeit_german_returns_lux(self):
        """HelligkeitMitte (German) returns lx."""
        detector = PlatformDetector()
        assert detector.get_unit("HelligkeitMitte") == "lx"

    def test_windspeed_returns_ms(self):
        """WindSpeed role returns m/s."""
        detector = PlatformDetector()
        assert detector.get_unit("WindSpeed") == "m/s"

    def test_windgeschwindigkeit_german_returns_kmh(self):
        """Windgeschwindigkeit (German) returns km/h."""
        detector = PlatformDetector()
        assert detector.get_unit("Windgeschwindigkeit") == "km/h"

    def test_rain_volume_returns_mm(self):
        """RainVolume role returns mm."""
        detector = PlatformDetector()
        assert detector.get_unit("RainVolume") == "mm"

    def test_unknown_role_returns_none(self):
        """Unknown role returns None for unit."""
        detector = PlatformDetector()
        assert detector.get_unit("UnknownSensorRole") is None


class TestDeviceClass:
    """Test device class retrieval for sensors."""

    def test_temperature_device_class(self):
        """Temperature role has 'temperature' device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("Temperature") == "temperature"

    def test_temperatur_german_device_class(self):
        """Temperatur (German) has 'temperature' device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("Temperatur") == "temperature"

    def test_humidity_device_class(self):
        """Humidity role has 'humidity' device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("Humidity") == "humidity"

    def test_pressure_device_class(self):
        """Pressure role has 'pressure' device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("Pressure") == "pressure"

    def test_brightness_device_class(self):
        """Brightness role has 'illuminance' device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("Brightness") == "illuminance"

    def test_helligkeit_german_device_class(self):
        """HelligkeitMitte (German) has 'illuminance' device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("HelligkeitMitte") == "illuminance"

    def test_rain_volume_device_class(self):
        """RainVolume role has 'precipitation' device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("RainVolume") == "precipitation"

    def test_co2_no_device_class(self):
        """CO2 role has no standard device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("CO2") is None

    def test_windspeed_no_device_class(self):
        """WindSpeed role has no standard device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("WindSpeed") is None

    def test_unknown_role_returns_none(self):
        """Unknown role returns None for device class."""
        detector = PlatformDetector()
        assert detector.get_device_class("UnknownSensorRole") is None
