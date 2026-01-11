"""Tests for OverrideHandler module (TDD approach)."""

import pytest
from homeassistant.const import Platform

from custom_components.luxor_living.mapped_entity import MappedEntity
from custom_components.luxor_living.override_handler import OverrideHandler


class TestOverrideHandlerCreation:
    """Test OverrideHandler creation and initialization."""

    def test_create_handler_with_empty_overrides(self):
        """OverrideHandler initializes with empty overrides."""
        handler = OverrideHandler({})
        assert handler is not None

    def test_create_handler_with_sensors_overrides(self):
        """OverrideHandler initializes with sensor overrides."""
        overrides = {"sensors": [{"role": "Temperature", "address": "1/2/3"}]}
        handler = OverrideHandler(overrides)
        assert handler is not None


class TestSensorOverrides:
    """Test sensor override application."""

    def test_apply_overrides_creates_sensor_entity(self):
        """Override creates new sensor entity with correct attributes."""
        overrides = {
            "sensors": [
                {
                    "role": "Temperature",
                    "address": "1/2/3",
                    "name": "Custom Temp Sensor",
                    "device_name": "Custom Device",
                    "device_id": "custom_device_1",
                }
            ]
        }
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        assert len(entities) == 1
        entity = entities[0]
        assert entity.platform == Platform.SENSOR
        assert entity.name == "Custom Temp Sensor"
        assert entity.device_name == "Custom Device"
        assert entity.device_id == "custom_device_1"
        assert entity.entity_type == "temperature"

    def test_apply_overrides_uses_default_device_name(self):
        """Override without device_name uses default 'Overrides'."""
        overrides = {
            "sensors": [{"role": "Temperature", "address": "1/2/3", "name": "Temp"}]
        }
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        assert entities[0].device_name == "Overrides"
        assert entities[0].device_id == "overrides"

    def test_apply_overrides_with_custom_unit(self):
        """Override with custom unit overrides default mapping."""
        overrides = {
            "sensors": [
                {
                    "role": "Temperature",
                    "address": "1/2/3",
                    "name": "Fahrenheit Temp",
                    "unit": "°F",
                }
            ]
        }
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        assert entities[0].attributes["unit_of_measurement"] == "°F"

    def test_apply_overrides_with_custom_device_class(self):
        """Override with custom device_class overrides default mapping."""
        overrides = {
            "sensors": [
                {
                    "role": "Temperature",
                    "address": "1/2/3",
                    "name": "Custom Temp",
                    "device_class": "custom_class",
                }
            ]
        }
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        assert entities[0].attributes["device_class"] == "custom_class"

    def test_apply_overrides_with_integer_address(self):
        """Override with integer address creates valid entity."""
        overrides = {"sensors": [{"role": "Temperature", "address": 2563, "name": "Temp"}]}
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        assert len(entities) == 1
        assert entities[0].datapoints["Temperature"] == 2563

    def test_apply_overrides_skips_invalid_address(self):
        """Override with invalid address is skipped."""
        overrides = {
            "sensors": [
                {"role": "Temperature", "address": "invalid/address", "name": "Temp"}
            ]
        }
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        assert len(entities) == 0

    def test_apply_overrides_skips_missing_role(self):
        """Override without role is skipped."""
        overrides = {"sensors": [{"address": "1/2/3", "name": "Temp"}]}
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        assert len(entities) == 0

    def test_apply_overrides_skips_missing_address(self):
        """Override without address is skipped."""
        overrides = {"sensors": [{"role": "Temperature", "name": "Temp"}]}
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        assert len(entities) == 0

    def test_apply_overrides_handles_multiple_sensors(self):
        """Multiple overrides create multiple entities."""
        overrides = {
            "sensors": [
                {"role": "Temperature", "address": "1/2/3", "name": "Temp 1"},
                {"role": "Humidity", "address": "1/2/4", "name": "Humidity 1"},
                {"role": "Brightness", "address": "1/2/5", "name": "Brightness 1"},
            ]
        }
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        assert len(entities) == 3
        assert entities[0].name == "Temp 1"
        assert entities[1].name == "Humidity 1"
        assert entities[2].name == "Brightness 1"


class TestAddressNormalization:
    """Test address normalization helper."""

    def test_normalize_address_with_string_format(self):
        """GA string '1/2/3' is normalized to integer."""
        handler = OverrideHandler({})

        result = handler._normalize_address("1/2/3")

        # 1/2/3 -> (1 << 11) | (2 << 8) | 3 = 2048 + 512 + 3 = 2563
        assert result == 2563

    def test_normalize_address_with_integer(self):
        """Integer address is returned as-is."""
        handler = OverrideHandler({})

        result = handler._normalize_address(2563)

        assert result == 2563

    def test_normalize_address_with_decimal_string(self):
        """Decimal string is converted to integer."""
        handler = OverrideHandler({})

        result = handler._normalize_address("2563")

        assert result == 2563

    def test_normalize_address_with_invalid_ga(self):
        """Invalid GA string returns None."""
        handler = OverrideHandler({})

        result = handler._normalize_address("1/2")

        assert result is None

    def test_normalize_address_with_non_numeric(self):
        """Non-numeric string returns None."""
        handler = OverrideHandler({})

        result = handler._normalize_address("invalid")

        assert result is None


class TestExceptionHandling:
    """Test error handling in override processing."""

    def test_apply_overrides_continues_on_error(self):
        """Override processing continues even if one override fails."""
        overrides = {
            "sensors": [
                {"role": "Temperature", "address": "1/2/3", "name": "Valid"},
                {"role": "Temperature", "address": None, "name": "Invalid"},  # Will fail
                {"role": "Humidity", "address": "1/2/4", "name": "Also Valid"},
            ]
        }
        handler = OverrideHandler(overrides)
        entities = []

        handler.apply_overrides(entities)

        # Only valid overrides are applied
        assert len(entities) == 2
        assert entities[0].name == "Valid"
        assert entities[1].name == "Also Valid"
