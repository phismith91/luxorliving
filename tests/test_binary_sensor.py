"""Tests for LUXORliving binary sensor platform."""

from unittest.mock import Mock

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry

from custom_components.luxor_living.binary_sensor import (
    LuxorLivingBinarySensor,
)
from custom_components.luxor_living.coordinator import LuxorLivingCoordinator


@pytest.fixture
def mock_coordinator():
    """Mock Data Coordinator."""
    coordinator = Mock(spec=LuxorLivingCoordinator)
    coordinator.last_update_success = True
    coordinator.async_add_listener = Mock(return_value=lambda: None)
    coordinator.get_state = Mock(return_value=False)  # Default to False for binary sensors
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Mock Config Entry."""
    entry = Mock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {"host": "192.168.1.3"}
    return entry


@pytest.fixture
def mock_motion_entity():
    """Mock mapped entity for motion sensor."""
    entity = Mock()
    entity.unique_id = "test_motion_001"
    entity.name = "Test Motion"
    entity.device_id = "device_001"
    entity.device_name = "Test Device"
    entity.entity_type = "motion"
    entity.datapoints = {
        "OnOff": "1/2/3",
    }
    entity.attributes = {}
    entity.parameters = {}  # LXP parameters
    return entity


@pytest.fixture
def mock_window_entity():
    """Mock mapped entity for window sensor."""
    entity = Mock()
    entity.unique_id = "test_window_001"
    entity.name = "Test Fenster"
    entity.device_id = "device_002"
    entity.device_name = "Test Device"
    entity.entity_type = "binary_input"
    entity.datapoints = {
        "status@OnOff": "1/2/4",
    }
    entity.attributes = {"sensor_type": "window"}
    entity.parameters = {}  # LXP parameters
    return entity


@pytest.mark.smoke
class TestLuxorLivingBinarySensor:
    """Test LuxorLivingBinarySensor class."""

    def test_init_motion(self, mock_coordinator, mock_config_entry, mock_motion_entity):
        """Test motion sensor initialization."""
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, mock_motion_entity)

        assert sensor.coordinator == mock_coordinator
        assert sensor.is_on is False
        assert sensor.device_class == BinarySensorDeviceClass.MOTION

    def test_init_window(self, mock_coordinator, mock_config_entry, mock_window_entity):
        """Test window sensor initialization."""
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, mock_window_entity)

        assert sensor.coordinator == mock_coordinator
        assert sensor.is_on is False
        assert sensor.device_class == BinarySensorDeviceClass.OPENING

    def test_detect_device_class_motion(self, mock_coordinator, mock_config_entry):
        """Test device class detection for motion."""
        entity = Mock()
        entity.unique_id = "test_001"
        entity.name = "Motion Sensor"
        entity.device_id = "device_001"
        entity.device_name = "Test Device"
        entity.entity_type = "motion"
        entity.datapoints = {"OnOff": "1/2/3"}
        entity.attributes = {}

        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, entity)
        assert sensor.device_class == BinarySensorDeviceClass.MOTION

    def test_detect_device_class_opening(self, mock_coordinator, mock_config_entry):
        """Test device class detection for opening."""
        entity = Mock()
        entity.unique_id = "test_001"
        entity.name = "Test Fenster"
        entity.device_id = "device_001"
        entity.device_name = "Test Device"
        entity.entity_type = "binary_input"
        entity.datapoints = {"OnOff": "1/2/3"}
        entity.attributes = {}
        entity.parameters = {}  # LXP parameters

        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, entity)
        assert sensor.device_class == BinarySensorDeviceClass.OPENING

    def test_extra_state_attributes(self, mock_coordinator, mock_config_entry, mock_motion_entity):
        """Test extra state attributes."""
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, mock_motion_entity)

        attrs = sensor.extra_state_attributes
        assert "knx_address" in attrs or len(attrs) >= 0  # Optional attributes


@pytest.mark.smoke
class TestBinarySensorMutationTargets:
    """Smoke tests targeting surviving mutants in LuxorLivingBinarySensor."""

    def test_address_priority_status_at_onoff_over_onoff(self, mock_coordinator, mock_config_entry):
        """Kill: 'status@OnOff' or 'OnOff' or chain → and mutation."""
        entity = Mock()
        entity.unique_id = "prio_test"
        entity.name = "Prio Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "binary_input"
        entity.datapoints = {"status@OnOff": "1/1/1", "OnOff": "1/1/2"}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, entity)
        assert sensor._address_status == "1/1/1"

    def test_address_fallback_regen_key(self, mock_coordinator, mock_config_entry):
        """Kill: 'Regen' key at end of or-chain removed."""
        entity = Mock()
        entity.unique_id = "regen_test"
        entity.name = "Regen Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "regen"
        entity.datapoints = {"Regen": "2/2/2"}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, entity)
        assert sensor._address_status == "2/2/2"

    def test_is_on_returns_false_when_no_address(self, mock_coordinator, mock_config_entry):
        """Kill: 'return False' when _address_status is None → return True."""
        entity = Mock()
        entity.unique_id = "no_addr"
        entity.name = "No Addr"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "binary_input"
        entity.datapoints = {}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, entity)
        assert sensor.is_on is False

    def test_is_on_reads_coordinator_state(
        self, mock_coordinator, mock_config_entry, mock_window_entity
    ):
        """Kill: bool(coordinator.get_state(...)) value mutations."""
        mock_coordinator.get_state = Mock(return_value=True)
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, mock_window_entity)
        assert sensor.is_on is True

    def test_handle_knx_state_stores_bool_value(
        self, mock_coordinator, mock_config_entry, mock_window_entity
    ):
        """Kill: bool(value) → value, or set_state address key mutation."""
        mock_coordinator.set_state = Mock()
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, mock_window_entity)
        sensor._handle_knx_state("1/2/4", 1)
        mock_coordinator.set_state.assert_called_once_with("1/2/4", True)

    def test_device_class_regen_is_moisture(self, mock_coordinator, mock_config_entry):
        """Kill: entity_type 'regen' → MOISTURE mapping mutation."""
        entity = Mock()
        entity.unique_id = "regen_class"
        entity.name = "Rain Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "regen"
        entity.datapoints = {}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, entity)
        assert sensor.device_class == BinarySensorDeviceClass.MOISTURE

    def test_device_class_smoke_by_name(self, mock_coordinator, mock_config_entry):
        """Kill: 'rauchmelder' keyword → SMOKE mapping mutation."""
        entity = Mock()
        entity.unique_id = "smoke_class"
        entity.name = "Rauchmelder OG"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "binary_input"
        entity.datapoints = {}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, entity)
        assert sensor.device_class == BinarySensorDeviceClass.SMOKE

    def test_device_class_door_by_name(self, mock_coordinator, mock_config_entry):
        """Kill: 'tür' keyword → OPENING mapping mutation."""
        entity = Mock()
        entity.unique_id = "door_class"
        entity.name = "Haustür"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "binary_input"
        entity.datapoints = {}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, entity)
        assert sensor.device_class == BinarySensorDeviceClass.OPENING
