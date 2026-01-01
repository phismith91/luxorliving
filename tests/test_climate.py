"""Tests for LUXORliving climate platform."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.climate import (
    async_setup_entry,
    LuxorClimate,
)


class MockDevice:
    """Mock device for testing."""

    def __init__(self):
        self.name = "H6 1"
        self.serial_number = "ABC123"
        self.app_id = "18502"
        self.actuators = []


class MockActuator:
    """Mock actuator for testing."""

    def __init__(self, name="FBH Wohnzimmer", channel=1):
        self.name = name
        self.channel = channel
        self.datapoints = []


class MockDatapoint:
    """Mock datapoint for testing."""

    def __init__(self, role, address):
        self.role = role
        self.address = address


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    project = MagicMock()
    coordinator.project = project
    return coordinator


@pytest.fixture
def mock_knx_gateway():
    """Create mock KNX gateway."""
    gateway = MagicMock()
    gateway.connected = True
    gateway.read_group_address = AsyncMock()
    gateway.write_group_address = AsyncMock()
    return gateway


@pytest.fixture
def heating_device():
    """Create mock H6 heating device."""
    device = MockDevice()
    actuator = MockActuator()
    actuator.datapoints = [
        MockDatapoint("Istwert", 8454),
        MockDatapoint("Sollwert", 8198),
        MockDatapoint("StatusSollwert", 8966),
        MockDatapoint("Stellgrösse", 8710),
        MockDatapoint("WindowContact", 9222),
        MockDatapoint("UmschaltenHeitzenKühlen", 10247),
    ]
    device.actuators = [actuator]
    return device


class TestLuxorClimate:
    """Test LuxorClimate class."""

    def test_init(self, mock_coordinator, mock_knx_gateway, heating_device):
        """Test climate entity initialization."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=heating_device,
            actuator=heating_device.actuators[0],
            entry_id="test_entry",
        )

        assert entity.name == "FBH Wohnzimmer"
        assert entity.unique_id == "luxor_ABC123_1_climate"
        assert entity.temperature_unit == UnitOfTemperature.CELSIUS
        assert HVACMode.HEAT in entity.hvac_modes
        assert HVACMode.OFF in entity.hvac_modes
        assert entity.supported_features & ClimateEntityFeature.TARGET_TEMPERATURE
        assert entity.target_temperature_step == 0.5
        assert entity.min_temp == 5.0
        assert entity.max_temp == 35.0

    def test_datapoint_mapping(self, mock_coordinator, mock_knx_gateway, heating_device):
        """Test datapoint role to address mapping."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=heating_device,
            actuator=heating_device.actuators[0],
            entry_id="test_entry",
        )

        assert entity._datapoints["Istwert"] == 8454
        assert entity._datapoints["Sollwert"] == 8198
        assert entity._datapoints["StatusSollwert"] == 8966
        assert entity._datapoints["Stellgrösse"] == 8710
        assert entity._datapoints["WindowContact"] == 9222

    @pytest.mark.asyncio
    async def test_update_temperature(
        self, mock_coordinator, mock_knx_gateway, heating_device
    ):
        """Test temperature update from KNX."""
        mock_knx_gateway.read_group_address.side_effect = [
            2150,  # Current temp: 21.5°C (2150 / 100)
            2000,  # Target temp: 20.0°C (2000 / 100)
            0,  # Window contact: closed
        ]

        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=heating_device,
            actuator=heating_device.actuators[0],
            entry_id="test_entry",
        )

        await entity._update_temperature()

        assert entity.current_temperature == 21.5
        assert entity.target_temperature == 20.0
        assert entity._window_contact_open is False

    @pytest.mark.asyncio
    async def test_set_temperature(
        self, mock_coordinator, mock_knx_gateway, heating_device
    ):
        """Test setting target temperature."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=heating_device,
            actuator=heating_device.actuators[0],
            entry_id="test_entry",
        )

        await entity.async_set_temperature(**{ATTR_TEMPERATURE: 22.5})

        # Should write to Sollwert address (8198) with value 2250 (22.5 * 100)
        mock_knx_gateway.write_group_address.assert_called_once_with(8198, 2250)
        assert entity.target_temperature == 22.5

    @pytest.mark.asyncio
    async def test_set_hvac_mode_heat(
        self, mock_coordinator, mock_knx_gateway, heating_device
    ):
        """Test setting HVAC mode to HEAT."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=heating_device,
            actuator=heating_device.actuators[0],
            entry_id="test_entry",
        )
        entity._attr_target_temperature = 21.0
        entity.async_write_ha_state = MagicMock()  # Mock state write

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        assert entity.hvac_mode == HVACMode.HEAT
        # Should restore temperature
        mock_knx_gateway.write_group_address.assert_called_once_with(8198, 2100)

    @pytest.mark.asyncio
    async def test_set_hvac_mode_off(
        self, mock_coordinator, mock_knx_gateway, heating_device
    ):
        """Test setting HVAC mode to OFF."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=heating_device,
            actuator=heating_device.actuators[0],
            entry_id="test_entry",
        )
        entity.async_write_ha_state = MagicMock()  # Mock state write

        await entity.async_set_hvac_mode(HVACMode.OFF)

        assert entity.hvac_mode == HVACMode.OFF
        # Should set temperature to minimum (5.0°C)
        mock_knx_gateway.write_group_address.assert_called_once_with(8198, 500)

    def test_available_when_connected(
        self, mock_coordinator, mock_knx_gateway, heating_device
    ):
        """Test entity availability when gateway is connected."""
        mock_knx_gateway.connected = True
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=heating_device,
            actuator=heating_device.actuators[0],
            entry_id="test_entry",
        )

        assert entity.available is True

    def test_unavailable_when_disconnected(
        self, mock_coordinator, mock_knx_gateway, heating_device
    ):
        """Test entity availability when gateway is disconnected."""
        mock_knx_gateway.connected = False
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=heating_device,
            actuator=heating_device.actuators[0],
            entry_id="test_entry",
        )

        assert entity.available is False


class TestAsyncSetupEntry:
    """Test async_setup_entry function."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = MagicMock()
        hass.data = {}
        return hass

    @pytest.mark.asyncio
    async def test_setup_with_heating_device(
        self, mock_hass, mock_coordinator, mock_knx_gateway, heating_device
    ):
        """Test setup with H6 heating device."""
        from unittest.mock import Mock
        
        mock_coordinator.project.devices = [heating_device]

        entry = MagicMock()
        entry.entry_id = "test_entry"

        mock_hass.data = {
            "luxor_living": {
                "test_entry": {
                    "coordinator": mock_coordinator,
                    "knx_gateway": mock_knx_gateway,
                }
            }
        }

        mock_add_entities = Mock()

        await async_setup_entry(mock_hass, entry, mock_add_entities)

        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], LuxorClimate)
        assert entities[0].name == "FBH Wohnzimmer"

    @pytest.mark.asyncio
    async def test_setup_without_heating_device(
        self, mock_hass, mock_coordinator, mock_knx_gateway
    ):
        """Test setup without heating devices."""
        from unittest.mock import Mock
        
        mock_coordinator.project.devices = []

        entry = MagicMock()
        entry.entry_id = "test_entry"

        mock_hass.data = {
            "luxor_living": {
                "test_entry": {
                    "coordinator": mock_coordinator,
                    "knx_gateway": mock_knx_gateway,
                }
            }
        }

        mock_add_entities = Mock()

        await async_setup_entry(mock_hass, entry, mock_add_entities)

        # Should not be called since no entities
        mock_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_ignores_non_heating_devices(
        self, mock_hass, mock_coordinator, mock_knx_gateway
    ):
        """Test setup ignores devices that are not H6 heating actuators."""
        from unittest.mock import Mock
        
        wrong_device = MockDevice()
        wrong_device.app_id = "18504"  # Not a heating actuator
        actuator = MockActuator()
        actuator.datapoints = [
            MockDatapoint("Istwert", 8454),
            MockDatapoint("Sollwert", 8198),
        ]
        wrong_device.actuators = [actuator]

        mock_coordinator.project.devices = [wrong_device]

        entry = MagicMock()
        entry.entry_id = "test_entry"

        mock_hass.data = {
            "luxor_living": {
                "test_entry": {
                    "coordinator": mock_coordinator,
                    "knx_gateway": mock_knx_gateway,
                }
            }
        }

        mock_add_entities = Mock()

        await async_setup_entry(mock_hass, entry, mock_add_entities)

        mock_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_requires_both_istwert_and_sollwert(
        self, mock_hass, mock_coordinator, mock_knx_gateway
    ):
        """Test setup requires both Istwert and Sollwert datapoints."""
        from unittest.mock import Mock
        
        incomplete_device = MockDevice()
        incomplete_device.app_id = "18502"
        actuator = MockActuator()
        # Only Istwert, missing Sollwert
        actuator.datapoints = [
            MockDatapoint("Istwert", 8454),
        ]
        incomplete_device.actuators = [actuator]

        mock_coordinator.project.devices = [incomplete_device]

        entry = MagicMock()
        entry.entry_id = "test_entry"

        mock_hass.data = {
            "luxor_living": {
                "test_entry": {
                    "coordinator": mock_coordinator,
                    "knx_gateway": mock_knx_gateway,
                }
            }
        }

        mock_add_entities = Mock()

        await async_setup_entry(mock_hass, entry, mock_add_entities)

        mock_add_entities.assert_not_called()
