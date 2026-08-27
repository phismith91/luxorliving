"""Tests for LUXORliving climate platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.const import ATTR_TEMPERATURE, Platform, UnitOfTemperature

from custom_components.luxor_living.climate import (
    LuxorClimate,
    async_setup_entry,
)
from custom_components.luxor_living.const import DATA_KNX_GATEWAY, DOMAIN
from custom_components.luxor_living.integration_state import IntegrationState
from custom_components.luxor_living.mapped_entity import MappedEntity


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_knx_gateway():
    """Create mock KNX gateway."""
    gateway = MagicMock()
    gateway.connected = True
    gateway.async_read_group_address = AsyncMock(return_value=True)
    gateway.async_send_telegram = AsyncMock(return_value=True)
    gateway.register_listener = MagicMock()
    gateway.unregister_listener = MagicMock()
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
    return MappedEntity(
        platform=Platform.CLIMATE,
        unique_id="luxor_ABC123_1_climate",
        name="FBH Wohnzimmer",
        device_name="H6 1",
        device_id="ABC123",
        entity_type="climate",
        datapoints={
            "Istwert": 8454,
            "Sollwert": 8198,
            "StatusSollwert": 8966,
            "Stellgrösse": 8710,
            "WindowContact": 9222,
            "UmschaltenHeitzenKühlen": 10247,
        },
        attributes={},
        parameters={},
    )


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
        """Test temperature update triggers KNX read requests for correct addresses."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )

        await entity._update_temperature()

        # Istwert (8454), StatusSollwert preferred over Sollwert (8966), WindowContact (9222)
        mock_knx_gateway.async_read_group_address.assert_any_call(8454)
        mock_knx_gateway.async_read_group_address.assert_any_call(8966)
        mock_knx_gateway.async_read_group_address.assert_any_call(9222)

    @pytest.mark.asyncio
    async def test_async_update_requests_coordinator_refresh_without_knx_reads(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
    ):
        """Manual entity refresh should not generate extra KNX reads."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )

        await entity.async_update()

        mock_coordinator.async_request_refresh.assert_awaited_once()
        mock_knx_gateway.async_read_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_listeners_registered_on_added_to_hass(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
    ):
        """Test KNX listeners are registered in async_added_to_hass, not __init__."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )

        mock_knx_gateway.register_listener.assert_not_called()

        await entity.async_added_to_hass()

        mock_knx_gateway.register_listener.assert_called()

    @pytest.mark.asyncio
    async def test_listeners_unregistered_on_remove(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
    ):
        """Test KNX listeners are cleaned up in async_will_remove_from_hass."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )
        await entity.async_added_to_hass()
        registered_count = mock_knx_gateway.register_listener.call_count

        await entity.async_will_remove_from_hass()

        assert mock_knx_gateway.unregister_listener.call_count == registered_count
        assert entity._knx_listener_refs == []

    @pytest.mark.asyncio
    async def test_handle_temperature_update(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
    ):
        """Test temperature state is updated via listener callback (DPT 9.001 float)."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )
        entity.async_write_ha_state = MagicMock()

        entity._handle_temperature_update(8454, 21.5)
        entity._handle_setpoint_update(8966, 20.0)
        entity._handle_window_contact_update(9222, False)

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

        # Should send DPT 9.001 temperature value to Sollwert address (8198)
        mock_knx_gateway.async_send_telegram.assert_called_once_with(8198, 22.5, "temperature")
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
        mock_knx_gateway.async_send_telegram.assert_called_once_with(8198, 21.0, "temperature")

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
        mock_knx_gateway.async_send_telegram.assert_called_once_with(8198, 5.0, "temperature")

    @pytest.mark.asyncio
    async def test_off_then_heat_restores_previous_setpoint(
        self, mock_coordinator, mock_knx_gateway, climate_mapped_entity
    ):
        """OFF must not clobber the stored setpoint; HEAT restores it (not 5°C)."""
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )
        entity.async_write_ha_state = MagicMock()
        entity._attr_target_temperature = 22.0

        await entity.async_set_hvac_mode(HVACMode.OFF)
        mock_knx_gateway.async_send_telegram.reset_mock()

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        # Must restore 22.0, NOT the 5.0 that OFF sent to the bus
        mock_knx_gateway.async_send_telegram.assert_called_once_with(8198, 22.0, "temperature")
        assert entity.target_temperature == 22.0

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
        entry.runtime_data = state

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
        entry.runtime_data = state

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
        """Test setup skips entities when mapper is None."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.runtime_data = MagicMock()
        entry.runtime_data.mapper = None
        entry.runtime_data.coordinator = mock_coordinator
        entry.runtime_data.knx_gateway = mock_knx_gateway

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # No entities should be added - function returns early without calling add_entities
        mock_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_requires_coordinator(self, mock_mapper, mock_knx_gateway):
        """Test setup skips entities when coordinator is None."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.runtime_data = MagicMock()
        entry.runtime_data.mapper = mock_mapper
        entry.runtime_data.coordinator = None
        entry.runtime_data.knx_gateway = mock_knx_gateway

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        # No entities should be added - function returns early without calling add_entities
        mock_add_entities.assert_not_called()


class TestTargetDpKey:
    """Test _target_dp_key property for all RTR/actuator datapoint variants."""

    def _make_entity(self, mock_coordinator, mock_knx_gateway, datapoints: dict):
        entity_data = MappedEntity(
            platform=Platform.CLIMATE,
            unique_id="test_climate",
            name="Test",
            device_name="Device",
            device_id="dev",
            entity_type="climate",
            datapoints=datapoints,
            attributes={},
            parameters={},
        )
        return LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=entity_data,
            entry_id="entry",
        )

    def test_prefers_status_sollwert_over_sollwert(self, mock_coordinator, mock_knx_gateway):
        """StatusSollwert (actuator variant) takes highest priority."""
        entity = self._make_entity(
            mock_coordinator,
            mock_knx_gateway,
            {"Istwert": 8454, "Sollwert": 8198, "StatusSollwert": 8966},
        )
        assert entity._target_dp_key == "StatusSollwert"

    def test_prefers_status_at_sollwert_over_sollwert(self, mock_coordinator, mock_knx_gateway):
        """status@Sollwert (RTR sensor variant) is used when StatusSollwert absent."""
        entity = self._make_entity(
            mock_coordinator,
            mock_knx_gateway,
            {"Istwert": 8449, "Sollwert": 8193, "status@Sollwert": 8961},
        )
        assert entity._target_dp_key == "status@Sollwert"

    def test_falls_back_to_sollwert(self, mock_coordinator, mock_knx_gateway):
        """Sollwert is used when neither status variant is present."""
        entity = self._make_entity(
            mock_coordinator,
            mock_knx_gateway,
            {"Istwert": 8449, "Sollwert": 8193},
        )
        assert entity._target_dp_key == "Sollwert"

    @pytest.mark.asyncio
    async def test_rtr_listener_registered_on_status_at_sollwert(
        self, mock_coordinator, mock_knx_gateway
    ):
        """RTR entity registers listener on status@Sollwert address, not Sollwert."""
        entity = self._make_entity(
            mock_coordinator,
            mock_knx_gateway,
            {"Istwert": 8449, "Sollwert": 8193, "status@Sollwert": 8961},
        )
        await entity.async_added_to_hass()
        registered_addresses = [
            call[0][0] for call in mock_knx_gateway.register_listener.call_args_list
        ]
        assert 8961 in registered_addresses  # status@Sollwert
        assert (
            8193 not in registered_addresses
        )  # Sollwert not registered (status variant takes over)


@pytest.mark.smoke
class TestClimateAuditFix:
    """Test for audit-fix: skip initial read when gateway not connected."""

    @pytest.mark.asyncio
    async def test_async_added_to_hass_skips_initial_read_when_not_connected(
        self, climate_mapped_entity
    ):
        """Initial temperature read must be skipped when gateway is not yet connected."""
        from unittest.mock import AsyncMock, MagicMock

        from custom_components.luxor_living.climate import LuxorClimate

        gateway = MagicMock()
        gateway.connected = False
        gateway.async_read_group_address = AsyncMock()
        gateway.register_listener = MagicMock()
        gateway.simulation_mode = False

        entity = LuxorClimate(
            coordinator=MagicMock(),
            knx_gateway=gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="test_entry",
        )

        await entity.async_added_to_hass()

        gateway.async_read_group_address.assert_not_called()


class TestClimateMutationTargets:
    """Smoke tests targeting surviving mutants in LuxorClimate."""

    # ── __init__: attribute + device_info key mutations ───────────────────

    @pytest.mark.smoke
    def test_init_unique_id_stored(self, climate_mapped_entity):
        """Kill mutmut_5: _attr_unique_id = None."""
        from custom_components.luxor_living.climate import LuxorClimate

        entity = LuxorClimate(
            coordinator=MagicMock(),
            knx_gateway=MagicMock(),
            mapped_entity=climate_mapped_entity,
            entry_id="e1",
        )
        assert entity._attr_unique_id is not None
        assert entity._attr_unique_id == climate_mapped_entity.unique_id

    @pytest.mark.smoke
    def test_device_info_has_correct_keys(self, climate_mapped_entity):
        """Kill mutmut_10/15/20: dict key mutations ('IDENTIFIERS', 'XXThebenXX', etc.)."""
        from custom_components.luxor_living.climate import LuxorClimate

        entity = LuxorClimate(
            coordinator=MagicMock(),
            knx_gateway=MagicMock(),
            mapped_entity=climate_mapped_entity,
            entry_id="e1",
        )
        info = entity.device_info
        assert "identifiers" in info
        assert info.get("manufacturer") == "Theben"
        assert info.get("model") == "LUXORliving"

    # ── async_added_to_hass: datapoint key names ──────────────────────────

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_istwert_listener_registered(self, climate_mapped_entity):
        """Kill mutmut_1: 'Istwert' → 'XXIstwertXX'."""
        from unittest.mock import AsyncMock, MagicMock

        from custom_components.luxor_living.climate import LuxorClimate

        gateway = MagicMock()
        gateway.connected = True
        gateway.register_listener = MagicMock()
        gateway.async_read_group_address = AsyncMock()

        entity = LuxorClimate(
            coordinator=MagicMock(),
            knx_gateway=gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="e1",
        )
        await entity.async_added_to_hass()

        registered = [c[0][0] for c in gateway.register_listener.call_args_list]
        assert climate_mapped_entity.datapoints["Istwert"] in registered

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_target_setpoint_listener_registered(self, climate_mapped_entity):
        """Kill mutmut_15: addr = self._datapoints[target_dp_key] → None."""
        from unittest.mock import AsyncMock, MagicMock

        from custom_components.luxor_living.climate import LuxorClimate

        gateway = MagicMock()
        gateway.connected = True
        gateway.register_listener = MagicMock()
        gateway.async_read_group_address = AsyncMock()

        entity = LuxorClimate(
            coordinator=MagicMock(),
            knx_gateway=gateway,
            mapped_entity=climate_mapped_entity,
            entry_id="e1",
        )
        await entity.async_added_to_hass()

        registered = [c[0][0] for c in gateway.register_listener.call_args_list]
        # StatusSollwert is in fixture, must be registered
        assert climate_mapped_entity.datapoints["StatusSollwert"] in registered
