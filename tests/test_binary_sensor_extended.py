"""Extended tests for binary_sensor.py covering uncovered branches."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.luxor_living.binary_sensor import LuxorLivingBinarySensor


def _make_mapped_entity(
    entity_type="binary_sensor",
    name="Test Sensor",
    datapoints=None,
    attributes=None,
):
    me = MagicMock()
    me.unique_id = f"test_{entity_type}"
    me.name = name
    me.device_name = "Test Device"
    me.device_id = "dev_001"
    me.entity_type = entity_type
    me.parameters = {}
    me.attributes = attributes or {}
    me.datapoints = datapoints or {}
    return me


def _make_sensor(entity_type="binary_sensor", name="Test Sensor", datapoints=None, attributes=None):
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    coordinator.async_request_refresh = AsyncMock()
    coordinator.get_state = MagicMock(return_value=True)

    entry = MagicMock()
    entry.runtime_data = MagicMock()
    entry.runtime_data.knx_gateway = MagicMock()
    entry.runtime_data.knx_gateway.connected = True
    entry.runtime_data.knx_gateway.simulation_mode = False

    mapped = _make_mapped_entity(entity_type, name, datapoints, attributes)
    entity = LuxorLivingBinarySensor(coordinator, entry, mapped)
    entity.async_write_ha_state = MagicMock()
    return entity


# ── __init__ ─────────────────────────────────────────────────────────────────


class TestInit:
    def test_health_entity_sets_diagnostic_category(self):
        entity = _make_sensor(entity_type="health", name="System Health")
        from homeassistant.helpers.entity import EntityCategory

        assert entity._attr_entity_category == EntityCategory.DIAGNOSTIC

    def test_health_entity_disabled_by_default(self):
        entity = _make_sensor(entity_type="health", name="System Health")
        assert entity._attr_entity_registry_enabled_default is False

    def test_non_health_entity_no_diagnostic_category(self):
        entity = _make_sensor(entity_type="motion")
        assert not hasattr(entity, "_attr_entity_category") or entity._attr_entity_category is None

    def test_address_from_status_onoff(self):
        entity = _make_sensor(datapoints={"status@OnOff": "1/0/0"})
        assert entity._address_status == "1/0/0"

    def test_address_from_onoff_fallback(self):
        entity = _make_sensor(datapoints={"OnOff": "1/0/1"})
        assert entity._address_status == "1/0/1"

    def test_address_from_schalten_fallback(self):
        entity = _make_sensor(datapoints={"SchaltenOnOff": "1/0/2"})
        assert entity._address_status == "1/0/2"

    def test_no_address_is_none(self):
        entity = _make_sensor(datapoints={})
        assert entity._address_status is None


# ── _detect_device_class ──────────────────────────────────────────────────────


class TestDetectDeviceClass:
    def test_motion_entity_type(self):
        entity = _make_sensor(entity_type="motion")
        assert entity._attr_device_class == BinarySensorDeviceClass.MOTION

    def test_health_entity_type(self):
        entity = _make_sensor(entity_type="health")
        assert entity._attr_device_class == BinarySensorDeviceClass.CONNECTIVITY

    def test_smoke_by_name_german(self):
        entity = _make_sensor(name="Rauchmelder Wohnzimmer")
        assert entity._attr_device_class == BinarySensorDeviceClass.SMOKE

    def test_smoke_by_name_english(self):
        entity = _make_sensor(name="Smoke Detector")
        assert entity._attr_device_class == BinarySensorDeviceClass.SMOKE

    def test_window_by_name_german(self):
        entity = _make_sensor(name="Fenster Küche")
        assert entity._attr_device_class == BinarySensorDeviceClass.OPENING

    def test_window_by_name_english(self):
        entity = _make_sensor(name="Window Kitchen")
        assert entity._attr_device_class == BinarySensorDeviceClass.OPENING

    def test_door_by_name_german(self):
        entity = _make_sensor(name="Tür Eingang")
        assert entity._attr_device_class == BinarySensorDeviceClass.OPENING

    def test_door_by_name_english(self):
        entity = _make_sensor(name="Front Door")
        assert entity._attr_device_class == BinarySensorDeviceClass.OPENING

    def test_motion_by_name_english(self):
        entity = _make_sensor(name="Motion Sensor")
        assert entity._attr_device_class == BinarySensorDeviceClass.MOTION

    def test_motion_by_name_german(self):
        entity = _make_sensor(name="Bewegungsmelder")
        assert entity._attr_device_class == BinarySensorDeviceClass.MOTION

    def test_vibration_by_name(self):
        entity = _make_sensor(name="Vibration Sensor")
        assert entity._attr_device_class == BinarySensorDeviceClass.VIBRATION

    def test_unknown_name_returns_none(self):
        entity = _make_sensor(entity_type="binary_sensor", name="Generic")
        assert entity._attr_device_class is None


# ── is_on ─────────────────────────────────────────────────────────────────────


class TestIsOn:
    def test_non_health_uses_coordinator_state(self):
        entity = _make_sensor(datapoints={"status@OnOff": "1/0/0"})
        entity.coordinator.get_state.return_value = True
        assert entity.is_on is True

    def test_non_health_uses_coordinator_state_false(self):
        entity = _make_sensor(datapoints={"status@OnOff": "1/0/0"})
        entity.coordinator.get_state.return_value = False
        assert entity.is_on is False

    def test_health_returns_true_when_connected(self):
        entity = _make_sensor(entity_type="health")
        gw = MagicMock()
        gw.connected = True
        gw.simulation_mode = False
        entry = MagicMock()
        entry.runtime_data = MagicMock()
        entry.runtime_data.knx_gateway = gw
        entity.hass = MagicMock()
        entity.hass.config_entries.async_entries.return_value = [entry]
        assert entity.is_on is True

    def test_health_returns_false_when_disconnected(self):
        entity = _make_sensor(entity_type="health")
        gw = MagicMock()
        gw.connected = False
        gw.simulation_mode = False
        entry = MagicMock()
        entry.runtime_data = MagicMock()
        entry.runtime_data.knx_gateway = gw
        entity.hass = MagicMock()
        entity.hass.config_entries.async_entries.return_value = [entry]
        assert entity.is_on is False

    def test_health_returns_true_in_simulation_even_disconnected(self):
        entity = _make_sensor(entity_type="health")
        gw = MagicMock()
        gw.connected = False
        gw.simulation_mode = True
        entry = MagicMock()
        entry.runtime_data = MagicMock()
        entry.runtime_data.knx_gateway = gw
        entity.hass = MagicMock()
        entity.hass.config_entries.async_entries.return_value = [entry]
        assert entity.is_on is True


# ── extra_state_attributes ────────────────────────────────────────────────────


class TestExtraStateAttributes:
    def test_knx_address_included_when_set(self):
        entity = _make_sensor(datapoints={"status@OnOff": "1/0/5"})
        attrs = entity.extra_state_attributes
        assert attrs["knx_address"] == "1/0/5"

    def test_no_knx_address_when_missing(self):
        entity = _make_sensor(datapoints={})
        attrs = entity.extra_state_attributes
        assert "knx_address" not in attrs

    def test_sensor_type_included_from_attributes(self):
        entity = _make_sensor(attributes={"sensor_type": "motion"})
        attrs = entity.extra_state_attributes
        assert attrs.get("sensor_type") == "motion"

    def test_no_sensor_type_when_not_in_attributes(self):
        entity = _make_sensor(attributes={})
        attrs = entity.extra_state_attributes
        assert "sensor_type" not in attrs

    def test_no_attributes_attr_on_mapped_entity(self):
        """Cover the hasattr False branch (178->184)."""
        entity = _make_sensor(attributes={})
        # Remove the attributes attribute entirely so hasattr returns False
        del entity._mapped_entity.attributes
        attrs = entity.extra_state_attributes
        assert "sensor_type" not in attrs
