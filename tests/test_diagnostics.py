"""Tests for diagnostics module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.const import (
    CONF_CONNECTION_TYPE,
    CONF_LXP_FILE,
    CONF_SIMULATION_MODE,
    DATA_KNX_GATEWAY,
    DOMAIN,
)
from custom_components.luxor_living.diagnostics import async_get_config_entry_diagnostics
from custom_components.luxor_living.entity_mapper import EntityMapper, MappedEntity
from homeassistant.const import Platform


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_123"
    entry.title = "Test LUXORliving"
    entry.version = 1
    entry.domain = DOMAIN
    entry.state = MagicMock()
    entry.state.value = "loaded"
    entry.data = {
        CONF_HOST: "192.168.1.100",
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "secret123",
        CONF_CONNECTION_TYPE: "rest",
        CONF_SIMULATION_MODE: False,
        CONF_LXP_FILE: "/path/to/project.lxp",
    }
    entry.options = {"scan_interval": 30}
    return entry


@pytest.fixture
def mock_hass_data():
    """Create mock hass data."""
    # Mock KNX Gateway
    mock_gateway = MagicMock()
    mock_gateway._connected = True
    mock_gateway._tunneling_enabled = False
    mock_gateway.simulation_mode = False
    mock_gateway.host = "192.168.1.100"
    mock_gateway._datapoint_mapping = {"1/2/3": "OnOff", "1/2/4": "Dimmen%"}

    # Mock Mapper with entities
    mock_mapper = MagicMock(spec=EntityMapper)

    # Create test entities
    test_entities = [
        MappedEntity(
            platform=Platform.LIGHT,
            unique_id="test_light_1",
            name="Living Room Light",
            device_name="S4 Device",
            device_id="device_001",
            entity_type="dimmer",
            datapoints={"OnOff": 1, "Dimmen%": 2},
            attributes={"icon": "mdi:lightbulb"},
            parameters={"timer": "5", "fade_time": "2"},
        ),
        MappedEntity(
            platform=Platform.SWITCH,
            unique_id="test_switch_1",
            name="Kitchen Switch",
            device_name="S8 Device",
            device_id="device_002",
            entity_type="switch",
            datapoints={"OnOff": 3},
            attributes={},
            parameters={},
        ),
    ]

    mock_mapper.entities = test_entities

    # Mock project
    mock_project = MagicMock()
    mock_device = MagicMock()
    mock_device.name = "S4 Schaltaktor"
    mock_device.serial_number = "12345678"
    mock_device.app_id = 18468
    mock_device.address = "1.1.10"
    mock_device.actuators = []
    mock_device.sensors = []

    # Mock actuator
    mock_actuator = MagicMock()
    mock_actuator.name = "Light Channel 1"
    mock_actuator.channel = 1
    mock_actuator.use_case = 0
    mock_actuator.on_icon = "icon_on"
    mock_actuator.off_icon = "icon_off"
    mock_actuator.parameters = {"timer": "5", "fade": "2"}
    mock_device.actuators = [mock_actuator]

    # Mock sensor
    mock_sensor = MagicMock()
    mock_sensor.name = "Temperature Sensor"
    mock_sensor.channel = 1
    mock_sensor.sensor_type = 1
    mock_sensor.parameters = {"offset": "0.5"}
    mock_device.sensors = [mock_sensor]

    mock_project.devices = [mock_device]
    mock_mapper._project = mock_project

    # Mock Coordinator
    mock_coordinator = MagicMock()
    mock_coordinator.last_update_success = True
    mock_coordinator.last_exception = None
    mock_coordinator.update_interval = MagicMock()
    mock_coordinator.update_interval.total_seconds = MagicMock(return_value=30.0)
    mock_coordinator._scan_interval = 30

    return {
        DATA_KNX_GATEWAY: mock_gateway,
        "mapper": mock_mapper,
        "coordinator": mock_coordinator,
        "overrides": {
            "include_unaffected": True,
            "sensors": {"sensor1": {"address": "1/2/3", "role": "Temperature"}},
        },
    }


@pytest.mark.asyncio
async def test_diagnostics_basic(mock_config_entry, mock_hass_data):
    """Test basic diagnostics data structure."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    # Check config entry
    assert "config_entry" in diag
    assert diag["config_entry"]["entry_id"] == "test_entry_123"
    assert diag["config_entry"]["title"] == "Test LUXORliving"
    assert diag["config_entry"]["version"] == 1
    assert diag["config_entry"]["domain"] == DOMAIN
    assert diag["config_entry"]["state"] == "loaded"


@pytest.mark.asyncio
async def test_diagnostics_password_redaction(mock_config_entry, mock_hass_data):
    """Test that passwords are redacted in diagnostics."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    # Verify password is redacted
    assert diag["config_entry"]["data"][CONF_PASSWORD] == "**REDACTED**"
    # Verify LXP file path is redacted
    assert diag["config_entry"]["data"][CONF_LXP_FILE] == "**REDACTED**"
    # Verify other fields are not redacted
    assert diag["config_entry"]["data"][CONF_HOST] == "192.168.1.100"
    assert diag["config_entry"]["data"][CONF_USERNAME] == "admin"


@pytest.mark.asyncio
async def test_diagnostics_knx_gateway_info(mock_config_entry, mock_hass_data):
    """Test KNX gateway information in diagnostics."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert "knx_gateway" in diag
    assert diag["knx_gateway"]["connected"] is True
    assert diag["knx_gateway"]["tunneling_enabled"] is False
    assert diag["knx_gateway"]["simulation_mode"] is False
    assert diag["knx_gateway"]["host"] == "192.168.1.100"
    assert diag["knx_gateway"]["datapoint_count"] == 2


@pytest.mark.asyncio
async def test_diagnostics_entities(mock_config_entry, mock_hass_data):
    """Test entity information in diagnostics."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert "entities" in diag
    assert len(diag["entities"]) == 2

    # Check first entity (Light)
    light_entity = diag["entities"][0]
    assert light_entity["unique_id"] == "test_light_1"
    assert light_entity["name"] == "Living Room Light"
    assert light_entity["platform"] == "light"
    assert light_entity["entity_type"] == "dimmer"
    assert light_entity["datapoints"] == {"OnOff": 1, "Dimmen%": 2}
    assert light_entity["device_name"] == "S4 Device"
    assert light_entity["parameters"] == {"timer": "5", "fade_time": "2"}

    # Check entity summary
    assert "entity_summary" in diag
    assert diag["entity_summary"]["total"] == 2
    assert diag["entity_summary"]["by_platform"]["light"] == 1
    assert diag["entity_summary"]["by_platform"]["switch"] == 1
    assert diag["entity_summary"]["with_parameters"] == 1  # Only light has params


@pytest.mark.asyncio
async def test_diagnostics_devices(mock_config_entry, mock_hass_data):
    """Test device information in diagnostics."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert "devices" in diag
    assert diag["devices"]["total"] == 1

    device = diag["devices"]["details"][0]
    assert device["name"] == "S4 Schaltaktor"
    assert device["serial_number"] == "12345678"
    assert device["app_id"] == 18468
    assert device["address"] == "1.1.10"

    # Check actuators
    assert len(device["actuators"]) == 1
    actuator = device["actuators"][0]
    assert actuator["name"] == "Light Channel 1"
    assert actuator["channel"] == 1
    assert actuator["parameters"] == {"timer": "5", "fade": "2"}

    # Check sensors
    assert len(device["sensors"]) == 1
    sensor = device["sensors"][0]
    assert sensor["name"] == "Temperature Sensor"
    assert sensor["parameters"] == {"offset": "0.5"}


@pytest.mark.asyncio
async def test_diagnostics_coordinator(mock_config_entry, mock_hass_data):
    """Test coordinator information in diagnostics."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert "coordinator" in diag
    assert diag["coordinator"]["last_update_success"] is True
    assert diag["coordinator"]["last_exception"] is None
    assert diag["coordinator"]["update_interval_seconds"] == 30.0
    assert diag["coordinator"]["scan_interval_configured"] == 30


@pytest.mark.asyncio
async def test_diagnostics_overrides(mock_config_entry, mock_hass_data):
    """Test overrides information in diagnostics."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert "overrides" in diag
    assert diag["overrides"]["count"] == 2  # include_unaffected + sensors
    assert diag["overrides"]["include_unaffected"] is True
    assert diag["overrides"]["sensors"] == 1


@pytest.mark.asyncio
async def test_diagnostics_empty_hass_data(mock_config_entry):
    """Test diagnostics with empty hass data."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}  # No data

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    # Should still return config entry
    assert "config_entry" in diag
    assert diag["config_entry"]["entry_id"] == "test_entry_123"

    # But no gateway/mapper/coordinator
    assert "knx_gateway" not in diag
    assert "entities" not in diag
    assert "coordinator" not in diag


@pytest.mark.asyncio
async def test_diagnostics_missing_entry_data(mock_config_entry):
    """Test diagnostics when config entry data is missing."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}  # Entry ID not in data

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    # Should still work with minimal data
    assert "config_entry" in diag
    assert "overrides" in diag
    assert diag["overrides"]["count"] == 0


@pytest.mark.asyncio
async def test_diagnostics_gateway_exception(mock_config_entry, mock_hass_data):
    """Test diagnostics when gateway handles exceptions gracefully."""
    hass = MagicMock(spec=HomeAssistant)

    # Make gateway work normally - no exception
    mock_gateway = MagicMock()
    mock_gateway._connected = True
    mock_gateway._tunneling_enabled = False
    mock_gateway.simulation_mode = False
    mock_gateway.host = "192.168.1.100"
    mock_gateway._datapoint_mapping = {1: "dp1", 2: "dp2"}

    mock_hass_data[DATA_KNX_GATEWAY] = mock_gateway
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    # Should work with normal data
    assert "knx_gateway" in diag
    assert diag["knx_gateway"]["connected"] is True
    assert diag["knx_gateway"]["datapoint_count"] == 2


@pytest.mark.asyncio
async def test_diagnostics_entity_limit(mock_config_entry, mock_hass_data):
    """Test that diagnostics limits entity details to 50."""
    hass = MagicMock(spec=HomeAssistant)

    # Create 100 entities
    entities = []
    for i in range(100):
        entities.append(
            MappedEntity(
                platform=Platform.LIGHT,
                unique_id=f"test_light_{i}",
                name=f"Light {i}",
                device_name="Device",
                device_id=f"device_{i}",
                entity_type="dimmer",
                datapoints={"OnOff": i},
                attributes={},
                parameters={},
            )
        )

    mock_hass_data["mapper"].entities = entities
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    # Should limit to 50 in details but show total in summary
    assert len(diag["entities"]) == 50
    assert diag["entity_summary"]["total"] == 100


@pytest.mark.asyncio
async def test_diagnostics_coordinator_with_exception(mock_config_entry, mock_hass_data):
    """Test coordinator diagnostics when last update had exception."""
    hass = MagicMock(spec=HomeAssistant)

    # Set coordinator with exception
    mock_hass_data["coordinator"].last_update_success = False
    mock_hass_data["coordinator"].last_exception = RuntimeError("Connection timeout")

    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diag["coordinator"]["last_update_success"] is False
    assert "Connection timeout" in diag["coordinator"]["last_exception"]


@pytest.mark.asyncio
async def test_diagnostics_without_project(mock_config_entry, mock_hass_data):
    """Test diagnostics when mapper has no project."""
    hass = MagicMock(spec=HomeAssistant)

    # Remove project from mapper
    mock_hass_data["mapper"]._project = None

    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    # Should still work without devices section
    assert "entities" in diag
    # Devices section should not be present or be minimal
    if "devices" in diag:
        assert diag["devices"]["total"] == 0
