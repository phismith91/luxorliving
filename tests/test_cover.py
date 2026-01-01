"""Tests for LUXORliving cover platform."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.cover import (
    async_setup_entry,
    LuxorCover,
)


class MockDevice:
    """Mock device for testing."""

    def __init__(self):
        self.name = "J8 1"
        self.serial_number = "XYZ789"
        self.app_id = "18520"
        self.actuators = []


class MockActuator:
    """Mock actuator for testing."""

    def __init__(self, name="Rolladen Wohnzimmer", channel=1):
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
def shutter_device():
    """Create mock J8 shutter device (no tilt)."""
    device = MockDevice()
    actuator = MockActuator()
    actuator.datapoints = [
        MockDatapoint("UpDown", 6147),
        MockDatapoint("StepStop", 6403),
        MockDatapoint("Höhe%", 6659),
        MockDatapoint("StatusHöhe%", 7171),
    ]
    device.actuators = [actuator]
    return device


@pytest.fixture
def blind_device():
    """Create mock J8 blind device (with tilt)."""
    device = MockDevice()
    actuator = MockActuator(name="Jalousie Schlafzimmer")
    actuator.datapoints = [
        MockDatapoint("UpDown", 6147),
        MockDatapoint("StepStop", 6403),
        MockDatapoint("Höhe%", 6659),
        MockDatapoint("StatusHöhe%", 7171),
        MockDatapoint("Lamelle%", 6915),
        MockDatapoint("StatusLamelle%", 7427),
        MockDatapoint("SicherheitRegen", 10952),
    ]
    device.actuators = [actuator]
    return device


class TestLuxorCover:
    """Test LuxorCover class."""

    def test_init_shutter(self, mock_coordinator, mock_knx_gateway, shutter_device):
        """Test cover entity initialization for shutter (no tilt)."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=shutter_device,
            actuator=shutter_device.actuators[0],
            entry_id="test_entry",
            has_tilt=False,
        )

        assert entity.name == "Rolladen Wohnzimmer"
        assert entity.unique_id == "luxor_XYZ789_1_cover"
        assert entity.device_class == CoverDeviceClass.SHUTTER
        assert entity.supported_features & CoverEntityFeature.OPEN
        assert entity.supported_features & CoverEntityFeature.CLOSE
        assert entity.supported_features & CoverEntityFeature.STOP
        assert entity.supported_features & CoverEntityFeature.SET_POSITION
        # No tilt features for shutter
        assert not (entity.supported_features & CoverEntityFeature.OPEN_TILT)

    def test_init_blind(self, mock_coordinator, mock_knx_gateway, blind_device):
        """Test cover entity initialization for blind (with tilt)."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=blind_device,
            actuator=blind_device.actuators[0],
            entry_id="test_entry",
            has_tilt=True,
        )

        assert entity.name == "Jalousie Schlafzimmer"
        assert entity.device_class == CoverDeviceClass.BLIND
        assert entity.supported_features & CoverEntityFeature.OPEN_TILT
        assert entity.supported_features & CoverEntityFeature.CLOSE_TILT
        assert entity.supported_features & CoverEntityFeature.SET_TILT_POSITION

    def test_datapoint_mapping(self, mock_coordinator, mock_knx_gateway, blind_device):
        """Test datapoint role to address mapping."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=blind_device,
            actuator=blind_device.actuators[0],
            entry_id="test_entry",
            has_tilt=True,
        )

        assert entity._datapoints["UpDown"] == 6147
        assert entity._datapoints["StepStop"] == 6403
        assert entity._datapoints["Höhe%"] == 6659
        assert entity._datapoints["StatusHöhe%"] == 7171
        assert entity._datapoints["Lamelle%"] == 6915
        assert entity._datapoints["StatusLamelle%"] == 7427

    @pytest.mark.asyncio
    async def test_update_position(
        self, mock_coordinator, mock_knx_gateway, blind_device
    ):
        """Test position update from KNX."""
        mock_knx_gateway.read_group_address.side_effect = [
            50,  # Position: 50%
            75,  # Tilt: 75%
        ]

        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=blind_device,
            actuator=blind_device.actuators[0],
            entry_id="test_entry",
            has_tilt=True,
        )

        await entity._update_position()

        assert entity.current_cover_position == 50
        assert entity.current_cover_tilt_position == 75
        assert entity.is_closed is False

    @pytest.mark.asyncio
    async def test_open_cover(self, mock_coordinator, mock_knx_gateway, shutter_device):
        """Test opening cover."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=shutter_device,
            actuator=shutter_device.actuators[0],
            entry_id="test_entry",
            has_tilt=False,
        )

        await entity.async_open_cover()

        # Should write 0 (UP) to UpDown address (6147)
        mock_knx_gateway.write_group_address.assert_called_once_with(6147, 0)

    @pytest.mark.asyncio
    async def test_close_cover(
        self, mock_coordinator, mock_knx_gateway, shutter_device
    ):
        """Test closing cover."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=shutter_device,
            actuator=shutter_device.actuators[0],
            entry_id="test_entry",
            has_tilt=False,
        )

        await entity.async_close_cover()

        # Should write 1 (DOWN) to UpDown address (6147)
        mock_knx_gateway.write_group_address.assert_called_once_with(6147, 1)

    @pytest.mark.asyncio
    async def test_stop_cover(self, mock_coordinator, mock_knx_gateway, shutter_device):
        """Test stopping cover."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=shutter_device,
            actuator=shutter_device.actuators[0],
            entry_id="test_entry",
            has_tilt=False,
        )

        await entity.async_stop_cover()

        # Should write 0 (STOP) to StepStop address (6403)
        mock_knx_gateway.write_group_address.assert_called_once_with(6403, 0)

    @pytest.mark.asyncio
    async def test_set_cover_position(
        self, mock_coordinator, mock_knx_gateway, shutter_device
    ):
        """Test setting cover position."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=shutter_device,
            actuator=shutter_device.actuators[0],
            entry_id="test_entry",
            has_tilt=False,
        )

        await entity.async_set_cover_position(**{ATTR_POSITION: 75})

        # Should write 75 to Höhe% address (6659)
        mock_knx_gateway.write_group_address.assert_called_once_with(6659, 75)
        assert entity.current_cover_position == 75
        assert entity.is_closed is False

    @pytest.mark.asyncio
    async def test_open_tilt(self, mock_coordinator, mock_knx_gateway, blind_device):
        """Test opening tilt."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=blind_device,
            actuator=blind_device.actuators[0],
            entry_id="test_entry",
            has_tilt=True,
        )

        await entity.async_open_cover_tilt()

        # Should write 100 to Lamelle% address (6915)
        mock_knx_gateway.write_group_address.assert_called_once_with(6915, 100)

    @pytest.mark.asyncio
    async def test_close_tilt(self, mock_coordinator, mock_knx_gateway, blind_device):
        """Test closing tilt."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=blind_device,
            actuator=blind_device.actuators[0],
            entry_id="test_entry",
            has_tilt=True,
        )

        await entity.async_close_cover_tilt()

        # Should write 0 to Lamelle% address (6915)
        mock_knx_gateway.write_group_address.assert_called_once_with(6915, 0)

    @pytest.mark.asyncio
    async def test_set_tilt_position(
        self, mock_coordinator, mock_knx_gateway, blind_device
    ):
        """Test setting tilt position."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=blind_device,
            actuator=blind_device.actuators[0],
            entry_id="test_entry",
            has_tilt=True,
        )

        await entity.async_set_cover_tilt_position(**{ATTR_TILT_POSITION: 60})

        # Should write 60 to Lamelle% address (6915)
        mock_knx_gateway.write_group_address.assert_called_once_with(6915, 60)
        assert entity.current_cover_tilt_position == 60

    def test_available_when_connected(
        self, mock_coordinator, mock_knx_gateway, shutter_device
    ):
        """Test entity availability when gateway is connected."""
        mock_knx_gateway.connected = True
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=shutter_device,
            actuator=shutter_device.actuators[0],
            entry_id="test_entry",
            has_tilt=False,
        )

        assert entity.available is True

    def test_unavailable_when_disconnected(
        self, mock_coordinator, mock_knx_gateway, shutter_device
    ):
        """Test entity availability when gateway is disconnected."""
        mock_knx_gateway.connected = False
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            device=shutter_device,
            actuator=shutter_device.actuators[0],
            entry_id="test_entry",
            has_tilt=False,
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
    async def test_setup_with_shutter_device(
        self, mock_hass, mock_coordinator, mock_knx_gateway, shutter_device
    ):
        """Test setup with J8 shutter device."""
        from unittest.mock import Mock
        
        mock_coordinator.project.devices = [shutter_device]

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
        assert isinstance(entities[0], LuxorCover)
        assert entities[0].name == "Rolladen Wohnzimmer"
        assert entities[0].device_class == CoverDeviceClass.SHUTTER

    @pytest.mark.asyncio
    async def test_setup_with_blind_device(
        self, mock_hass, mock_coordinator, mock_knx_gateway, blind_device
    ):
        """Test setup with J8 blind device."""
        from unittest.mock import Mock
        
        mock_coordinator.project.devices = [blind_device]

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
        assert isinstance(entities[0], LuxorCover)
        assert entities[0].device_class == CoverDeviceClass.BLIND
        assert entities[0].supported_features & CoverEntityFeature.OPEN_TILT

    @pytest.mark.asyncio
    async def test_setup_without_cover_device(
        self, mock_hass, mock_coordinator, mock_knx_gateway
    ):
        """Test setup without cover devices."""
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

        mock_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_ignores_non_cover_devices(
        self, mock_hass, mock_coordinator, mock_knx_gateway
    ):
        """Test setup ignores devices that are not J8/J4 cover actuators."""
        from unittest.mock import Mock
        
        wrong_device = MockDevice()
        wrong_device.app_id = "18502"  # H6 heating actuator, not cover
        actuator = MockActuator()
        actuator.datapoints = [
            MockDatapoint("UpDown", 6147),
            MockDatapoint("StepStop", 6403),
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
    async def test_setup_requires_updown_or_stepstop(
        self, mock_hass, mock_coordinator, mock_knx_gateway
    ):
        """Test setup requires UpDown or StepStop datapoints."""
        from unittest.mock import Mock
        
        incomplete_device = MockDevice()
        incomplete_device.app_id = "18520"
        actuator = MockActuator()
        # No UpDown or StepStop
        actuator.datapoints = [
            MockDatapoint("Höhe%", 6659),
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
