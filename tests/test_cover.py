"""Tests for LUXORliving cover platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.const import DATA_KNX_GATEWAY, DOMAIN
from custom_components.luxor_living.cover import (
    LuxorCover,
    async_setup_entry,
)
from custom_components.luxor_living.integration_state import (
    IntegrationState,
    register_integration_state,
)


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    return MagicMock()


@pytest.fixture
def mock_knx_gateway():
    """Create mock KNX gateway."""
    gateway = MagicMock()
    gateway.connected = True
    gateway.read_group_address = AsyncMock()
    gateway.write_group_address = AsyncMock()
    return gateway


@pytest.fixture
def mock_mapper():
    """Create mock entity mapper."""
    mapper = MagicMock()
    mapper.get_entities_by_platform = MagicMock(return_value=[])
    return mapper


@pytest.fixture
def shutter_mapped_entity():
    """Create a mapped shutter entity (no tilt)."""
    return {
        "unique_id": "luxor_DEF456_1_cover",
        "name": "Wohnzimmer Rollladen",
        "device_id": "DEF456",
        "device_name": "J8 1",
        "device_model": "J8 Shutter Actuator (App ID 18520)",
        "datapoints": [
            {"role": "UpDown", "address": 8454},
            {"role": "StepStop", "address": 8198},
            {"role": "Höhe%", "address": 8966},
            {"role": "StatusHöhe%", "address": 8710},
        ],
    }


@pytest.fixture
def blind_mapped_entity():
    """Create a mapped blind entity (with tilt)."""
    return {
        "unique_id": "luxor_DEF456_2_cover",
        "name": "Wohnzimmer Jalousie",
        "device_id": "DEF456",
        "device_name": "J8 1",
        "device_model": "J8 Shutter Actuator (App ID 18520)",
        "datapoints": [
            {"role": "UpDown", "address": 8454},
            {"role": "StepStop", "address": 8198},
            {"role": "Höhe%", "address": 8966},
            {"role": "StatusHöhe%", "address": 8710},
            {"role": "Lamelle%", "address": 9222},
            {"role": "StatusLamelle%", "address": 9476},
        ],
    }


class TestLuxorCover:
    """Test LuxorCover class."""

    def test_init_shutter(self, mock_coordinator, mock_knx_gateway, shutter_mapped_entity):
        """Test shutter initialization."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=shutter_mapped_entity,
            entry_id="test_entry",
        )

        assert entity.name == "Wohnzimmer Rollladen"
        assert entity.unique_id == "luxor_DEF456_1_cover"
        assert entity.device_class == CoverDeviceClass.SHUTTER
        assert entity.supported_features & CoverEntityFeature.SET_POSITION

    def test_init_blind(self, mock_coordinator, mock_knx_gateway, blind_mapped_entity):
        """Test blind initialization."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=blind_mapped_entity,
            entry_id="test_entry",
        )

        assert entity.name == "Wohnzimmer Jalousie"
        assert entity.unique_id == "luxor_DEF456_2_cover"
        assert entity.device_class == CoverDeviceClass.BLIND
        assert entity.supported_features & CoverEntityFeature.SET_TILT_POSITION

    def test_datapoint_mapping(self, mock_coordinator, mock_knx_gateway, shutter_mapped_entity):
        """Test datapoint address mapping."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=shutter_mapped_entity,
            entry_id="test_entry",
        )

        assert entity._datapoints["UpDown"] == 8454
        assert entity._datapoints["StepStop"] == 8198
        assert entity._datapoints["Höhe%"] == 8966
        assert entity._datapoints["StatusHöhe%"] == 8710

    @pytest.mark.asyncio
    async def test_update_position(self, mock_coordinator, mock_knx_gateway, shutter_mapped_entity):
        """Test position update from KNX."""
        mock_knx_gateway.read_group_address.side_effect = [75]  # Position: 75%

        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=shutter_mapped_entity,
            entry_id="test_entry",
        )
        entity.async_write_ha_state = MagicMock()

        await entity._update_position()

        assert entity.current_cover_position == 75
        assert entity.is_closed is False

    @pytest.mark.asyncio
    async def test_open_cover(self, mock_coordinator, mock_knx_gateway, shutter_mapped_entity):
        """Test opening cover."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=shutter_mapped_entity,
            entry_id="test_entry",
        )

        await entity.async_open_cover()

        # Should write UP command (0) to UpDown address
        mock_knx_gateway.write_group_address.assert_called_once_with(8454, 0)

    @pytest.mark.asyncio
    async def test_close_cover(self, mock_coordinator, mock_knx_gateway, shutter_mapped_entity):
        """Test closing cover."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=shutter_mapped_entity,
            entry_id="test_entry",
        )

        await entity.async_close_cover()

        # Should write DOWN command (1) to UpDown address
        mock_knx_gateway.write_group_address.assert_called_once_with(8454, 1)

    @pytest.mark.asyncio
    async def test_stop_cover(self, mock_coordinator, mock_knx_gateway, shutter_mapped_entity):
        """Test stopping cover."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=shutter_mapped_entity,
            entry_id="test_entry",
        )

        await entity.async_stop_cover()

        # Should write STOP command (0) to StepStop address
        mock_knx_gateway.write_group_address.assert_called_once_with(8198, 0)

    @pytest.mark.asyncio
    async def test_set_cover_position(
        self, mock_coordinator, mock_knx_gateway, shutter_mapped_entity
    ):
        """Test setting cover position."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=shutter_mapped_entity,
            entry_id="test_entry",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_set_cover_position(**{ATTR_POSITION: 50})

        # Should write to Höhe% address (8966) with value 50
        mock_knx_gateway.write_group_address.assert_called_once_with(8966, 50)
        assert entity.current_cover_position == 50

    @pytest.mark.asyncio
    async def test_open_tilt(self, mock_coordinator, mock_knx_gateway, blind_mapped_entity):
        """Test opening blind tilt."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=blind_mapped_entity,
            entry_id="test_entry",
        )

        await entity.async_open_cover_tilt()

        # Should write 100 to Lamelle% address
        mock_knx_gateway.write_group_address.assert_called_once_with(9222, 100)

    @pytest.mark.asyncio
    async def test_close_tilt(self, mock_coordinator, mock_knx_gateway, blind_mapped_entity):
        """Test closing blind tilt."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=blind_mapped_entity,
            entry_id="test_entry",
        )

        await entity.async_close_cover_tilt()

        # Should write 0 to Lamelle% address
        mock_knx_gateway.write_group_address.assert_called_once_with(9222, 0)

    @pytest.mark.asyncio
    async def test_set_tilt_position(self, mock_coordinator, mock_knx_gateway, blind_mapped_entity):
        """Test setting tilt position."""
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=blind_mapped_entity,
            entry_id="test_entry",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_set_cover_tilt_position(**{ATTR_TILT_POSITION: 60})

        # Should write to Lamelle% address (9222) with value 60
        mock_knx_gateway.write_group_address.assert_called_once_with(9222, 60)
        assert entity.current_cover_tilt_position == 60

    def test_available_when_connected(
        self, mock_coordinator, mock_knx_gateway, shutter_mapped_entity
    ):
        """Test entity availability when gateway is connected."""
        mock_knx_gateway.connected = True
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=shutter_mapped_entity,
            entry_id="test_entry",
        )

        assert entity.available is True

    def test_unavailable_when_disconnected(
        self, mock_coordinator, mock_knx_gateway, shutter_mapped_entity
    ):
        """Test entity availability when gateway is disconnected."""
        mock_knx_gateway.connected = False
        entity = LuxorCover(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=shutter_mapped_entity,
            entry_id="test_entry",
        )

        assert entity.available is False


class TestAsyncSetupEntry:
    """Test async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_setup_with_shutter_device(
        self, mock_coordinator, mock_knx_gateway, mock_mapper, shutter_mapped_entity
    ):
        """Test setup with shutter cover entity."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        mock_mapper.get_entities_by_platform.return_value = [shutter_mapped_entity]

        # Register type-safe integration state
        state = IntegrationState(
            mapper=mock_mapper,
            config={},
            overrides={},
            knx_gateway=mock_knx_gateway,
            coordinator=mock_coordinator,
            entry=entry,
        )
        register_integration_state(entry.entry_id, state)
        
        hass.data = {
            DOMAIN: {
                "test_entry": {
                    "coordinator": mock_coordinator,
                    "mapper": mock_mapper,
                    DATA_KNX_GATEWAY: mock_knx_gateway,
                }
            }
        }

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # Verify mapper was called
        mock_mapper.get_entities_by_platform.assert_called_once_with(Platform.COVER)
        # Verify entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], LuxorCover)

    @pytest.mark.asyncio
    async def test_setup_with_blind_device(
        self, mock_coordinator, mock_knx_gateway, mock_mapper, blind_mapped_entity
    ):
        """Test setup with blind cover entity."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        mock_mapper.get_entities_by_platform.return_value = [blind_mapped_entity]

        # Register type-safe integration state
        state = IntegrationState(
            mapper=mock_mapper,
            config={},
            overrides={},
            knx_gateway=mock_knx_gateway,
            coordinator=mock_coordinator,
            entry=entry,
        )
        register_integration_state(entry.entry_id, state)
        
        hass.data = {
            DOMAIN: {
                "test_entry": {
                    "coordinator": mock_coordinator,
                    "mapper": mock_mapper,
                    DATA_KNX_GATEWAY: mock_knx_gateway,
                }
            }
        }

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # Verify entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], LuxorCover)

    @pytest.mark.asyncio
    async def test_setup_without_cover_device(
        self, mock_coordinator, mock_knx_gateway, mock_mapper
    ):
        """Test setup without cover entities."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        mock_mapper.get_entities_by_platform.return_value = []

        # Register type-safe integration state
        state = IntegrationState(
            mapper=mock_mapper,
            config={},
            overrides={},
            knx_gateway=mock_knx_gateway,
            coordinator=mock_coordinator,
            entry=entry,
        )
        register_integration_state(entry.entry_id, state)
        
        hass.data = {
            DOMAIN: {
                "test_entry": {
                    "coordinator": mock_coordinator,
                    "mapper": mock_mapper,
                    DATA_KNX_GATEWAY: mock_knx_gateway,
                }
            }
        }

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # Verify no entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 0

    @pytest.mark.asyncio
    async def test_setup_ignores_non_cover_devices(
        self, mock_coordinator, mock_knx_gateway, mock_mapper
    ):
        """Test setup ignores non-cover devices."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        # Empty list means no covers found
        mock_mapper.get_entities_by_platform.return_value = []

        # Register type-safe integration state
        state = IntegrationState(
            mapper=mock_mapper,
            config={},
            overrides={},
            knx_gateway=mock_knx_gateway,
            coordinator=mock_coordinator,
            entry=entry,
        )
        register_integration_state(entry.entry_id, state)
        
        hass.data = {
            DOMAIN: {
                "test_entry": {
                    "coordinator": mock_coordinator,
                    "mapper": mock_mapper,
                    DATA_KNX_GATEWAY: mock_knx_gateway,
                }
            }
        }

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # No entities should be added
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 0

    @pytest.mark.asyncio
    async def test_setup_requires_updown_or_stepstop(
        self, mock_coordinator, mock_knx_gateway, mock_mapper
    ):
        """Test setup with invalid cover device (no UpDown or StepStop)."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        # Return empty list (mapper would filter out invalid devices)
        mock_mapper.get_entities_by_platform.return_value = []

        # Register type-safe integration state
        state = IntegrationState(
            mapper=mock_mapper,
            config={},
            overrides={},
            knx_gateway=mock_knx_gateway,
            coordinator=mock_coordinator,
            entry=entry,
        )
        register_integration_state(entry.entry_id, state)
        
        hass.data = {
            DOMAIN: {
                "test_entry": {
                    "coordinator": mock_coordinator,
                    "mapper": mock_mapper,
                    DATA_KNX_GATEWAY: mock_knx_gateway,
                }
            }
        }

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # No entities should be added
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 0
