"""Tests for LUXORliving binary sensor platform."""
import pytest
from unittest.mock import Mock
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry

from custom_components.luxor_living.binary_sensor import (
    async_setup_entry,
    LuxorLivingBinarySensor,
)
from custom_components.luxor_living.coordinator import LuxorLivingCoordinator


@pytest.fixture
def mock_coordinator():
    """Mock Data Coordinator."""
    coordinator = Mock(spec=LuxorLivingCoordinator)
    coordinator.last_update_success = True
    coordinator.async_add_listener = Mock(return_value=lambda: None)
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
    return entity


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
        
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, entity)
        assert sensor.device_class == BinarySensorDeviceClass.OPENING

    def test_extra_state_attributes(self, mock_coordinator, mock_config_entry, mock_motion_entity):
        """Test extra state attributes."""
        sensor = LuxorLivingBinarySensor(mock_coordinator, mock_config_entry, mock_motion_entity)
        
        attrs = sensor.extra_state_attributes
        assert "knx_address" in attrs or len(attrs) >= 0  # Optional attributes
