"""Tests for LUXORliving climate platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.const import ATTR_TEMPERATURE, Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.climate import (
    LuxorClimate,
    async_setup_entry,
)
from custom_components.luxor_living.const import DATA_KNX_GATEWAY, DOMAIN
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
def climate_mapped_entity():
    """Create a mapped climate entity (from EntityMapper)."""
    return {
        "unique_id": "luxor_ABC123_1_climate",
        "name": "FBH Wohnzimmer",
        "device_id": "ABC123",
        "device_name": "H6 1",
        "device_model": "H6 Heating Actuator (App ID 18502)",
        "datapoints": [
            {"role": "Istwert", "address": 8454},
            {"role": "Sollwert", "address": 8198},
            {"role": "StatusSollwert", "address": 8966},
            {"role": "Stellgrösse", "address": 8710},
            {"role": "WindowContact", "address": 9222},
            {"role": "UmschaltenHeitzenKühlen", "address": 10247},
        ],
    }


class TestLuxorClimate:
    """Test LuxorClimate class."""

    def test_init(self, mock_coordinator, mock_knx_gateway, climate_mapped_entity):
        """Test climate entity initialization."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )

        assert entity.name == "FBH Wohnzimmer"
        assert entity.unique_id == "luxor_ABC123_1_climate"
        assert entity.temperature_unit == UnitOfTemperature.CELSIUS
        assert HVACMode.HEAT in entity.hvac_modes
        assert HVACMode.OFF in entity.hvac_modes

    def test_datapoint_mapping(self, mock_coordinator, mock_knx_gateway, climate_mapped_entity):
        """Test datapoint address mapping."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )

        assert entity._datapoints["Istwert"] == 8454
        assert entity._datapoints["Sollwert"] == 8198
        assert entity._datapoints["StatusSollwert"] == 8966
        assert entity._datapoints["Stellgrösse"] == 8710
        assert entity._datapoints["WindowContact"] == 9222

    @pytest.mark.asyncio
    async def test_update_temperature(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
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
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )
        entity.async_write_ha_state = MagicMock()

        await entity._update_temperature()

        assert entity.current_temperature == 21.5
        assert entity.target_temperature == 20.0
        assert entity._window_contact_open is False

    @pytest.mark.asyncio
    async def test_set_temperature(self, mock_coordinator, mock_knx_gateway, climate_mapped_entity):
        """Test setting target temperature."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_set_temperature(**{ATTR_TEMPERATURE: 22.5})

        # Should write to Sollwert address (8198) with value 2250 (22.5 * 100)
        mock_knx_gateway.write_group_address.assert_called_once_with(8198, 2250)
        assert entity.target_temperature == 22.5

    @pytest.mark.asyncio
    async def test_set_hvac_mode_heat(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
    ):
        """Test setting HVAC mode to HEAT."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )
        entity._attr_target_temperature = 21.0
        entity.async_write_ha_state = MagicMock()

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        assert entity.hvac_mode == HVACMode.HEAT
        mock_knx_gateway.write_group_address.assert_called_once_with(8198, 2100)

    @pytest.mark.asyncio
    async def test_set_hvac_mode_off(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
    ):
        """Test setting HVAC mode to OFF."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_set_hvac_mode(HVACMode.OFF)

        assert entity.hvac_mode == HVACMode.OFF
        # Should set temperature to minimum (5.0°C)
        mock_knx_gateway.write_group_address.assert_called_once_with(8198, 500)

    def test_available_when_connected(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
    ):
        """Test entity availability when gateway is connected."""
        mock_knx_gateway.connected = True
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )

        assert entity.available is True

    def test_unavailable_when_disconnected(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
    ):
        """Test entity availability when gateway is disconnected."""
        mock_knx_gateway.connected = False
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )

        assert entity.available is False


class TestAsyncSetupEntry:
    """Test async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_setup_with_heating_entities(
        self, mock_coordinator, mock_knx_gateway, mock_mapper, climate_mapped_entity
    ):
        """Test setup with climate entities from mapper."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        mock_mapper.get_entities_by_platform.return_value = [climate_mapped_entity]

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

        # Keep legacy dict storage
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
        mock_mapper.get_entities_by_platform.assert_called_once_with(Platform.CLIMATE)
        # Verify entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], LuxorClimate)

    @pytest.mark.asyncio
    async def test_setup_without_heating_device(
        self, mock_coordinator, mock_knx_gateway, mock_mapper
    ):
        """Test setup without climate entities."""
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
    async def test_setup_requires_mapper(self, mock_coordinator, mock_knx_gateway):
        """Test setup fails without mapper (state not registered)."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        # Don't register state - test error handling when state not found
        hass.data = {}

        mock_add_entities = MagicMock()

        # Should log error and return early
        await async_setup_entry(hass, entry, mock_add_entities)

        # No entities should be added - function returns early without calling add_entities
        mock_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_requires_coordinator(self, mock_mapper, mock_knx_gateway):
        """Test setup fails without coordinator (state not registered)."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        # Don't register state - test error handling when state not found
        hass.data = {}

        mock_add_entities = MagicMock()

        # Should log error and return early
        await async_setup_entry(hass, entry, mock_add_entities)

        # No entities should be added
        mock_add_entities.assert_not_called()

        # No entities should be added - function returns early without calling add_entities
        mock_add_entities.assert_not_called()
