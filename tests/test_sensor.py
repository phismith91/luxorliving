"""Tests for LUXORliving sensor platform."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.const import DOMAIN
from custom_components.luxor_living.coordinator import LuxorLivingCoordinator
from custom_components.luxor_living.integration_state import IntegrationState
from custom_components.luxor_living.knx_gateway import LuxorKNXGateway
from custom_components.luxor_living.sensor import LuxorLivingSensor, async_setup_entry


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def mock_coordinator():
    """Mock Data Coordinator."""
    coordinator = Mock(spec=LuxorLivingCoordinator)
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
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
def mock_knx_gateway():
    """Mock KNX Gateway."""
    gateway = Mock(spec=LuxorKNXGateway)
    gateway.async_send_telegram = AsyncMock(return_value=True)
    gateway.async_read_group_value = AsyncMock(return_value=22.5)
    gateway.register_telegram_listener = Mock()
    gateway.unregister_telegram_listener = Mock()
    return gateway


@pytest.fixture
def mock_temperature_entity():
    """Mock mapped entity for temperature sensor."""
    entity = Mock()
    entity.unique_id = "test_temp_sensor_001"
    entity.name = "Test Temperature"
    entity.device_id = "device_001"
    entity.device_name = "Test Sensor Device"
    entity.entity_type = "temperature"
    entity.datapoints = {
        "Temperature": "1/2/3",
    }
    entity.attributes = {
        "channel": 1,
        "sensor_type": 2,
        "serial_number": "12345",
        "knx_address": "1.1.1",
        "device_class": "temperature",
        "unit_of_measurement": "°C",
    }
    entity.parameters = {}  # LXP parameters
    return entity


@pytest.fixture
def mock_humidity_entity():
    """Mock mapped entity for humidity sensor."""
    entity = Mock()
    entity.unique_id = "test_humid_sensor_001"
    entity.name = "Test Humidity"
    entity.device_id = "device_002"
    entity.device_name = "Test Sensor Device"
    entity.entity_type = "humidity"
    entity.datapoints = {
        "Humidity": "1/2/4",
    }
    entity.attributes = {
        "channel": 2,
        "sensor_type": 3,
        "serial_number": "12346",
        "knx_address": "1.1.1",
        "device_class": "humidity",
        "unit_of_measurement": "%",
    }
    entity.parameters = {}  # LXP parameters
    return entity


@pytest.mark.smoke
class TestLuxorLivingSensor:
    """Test LuxorLivingSensor entity."""

    def test_init(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Test sensor initialization."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )

        assert sensor.name == "Test Temperature"
        assert sensor.unique_id == "test_temp_sensor_001"
        assert sensor.native_unit_of_measurement == "°C"
        assert sensor.device_class == "temperature"
        assert sensor.native_value is None

    def test_init_humidity(
        self, mock_coordinator, mock_config_entry, mock_humidity_entity, mock_knx_gateway
    ):
        """Test humidity sensor initialization."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_humidity_entity, mock_knx_gateway
        )

        assert sensor.name == "Test Humidity"
        assert sensor.unique_id == "test_humid_sensor_001"
        assert sensor.native_unit_of_measurement == "%"
        assert sensor.device_class == "humidity"

    @pytest.mark.asyncio
    async def test_async_added_to_hass(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Test async added to Home Assistant."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )

        with patch.object(sensor, "async_write_ha_state"):
            await sensor.async_added_to_hass()

        # Verify initial state read request was sent
        mock_knx_gateway.async_read_group_address.assert_called_with("1/2/3", is_initial=True)

        # Verify telegram listener was registered
        mock_knx_gateway.register_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_added_to_hass_read_success(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Test reading initial state sends request."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )

        await sensor.async_added_to_hass()

        # Verify read request was sent
        mock_knx_gateway.async_read_group_address.assert_called_with("1/2/3", is_initial=True)

    @pytest.mark.asyncio
    async def test_async_will_remove_from_hass(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Test async will remove from Home Assistant."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )

        await sensor.async_will_remove_from_hass()

        # Verify telegram listener was unregistered
        mock_knx_gateway.unregister_listener.assert_called_once()

    def test_on_telegram_update(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Test handling incoming telegram."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )

        with patch.object(sensor, "async_write_ha_state") as mock_write:
            sensor._on_telegram("1/2/3", 23.5)

        assert sensor.native_value == 23.5
        mock_write.assert_called_once()

    def test_on_telegram_with_zero_value(
        self, mock_coordinator, mock_config_entry, mock_humidity_entity, mock_knx_gateway
    ):
        """Test handling incoming telegram with zero value."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_humidity_entity, mock_knx_gateway
        )

        with patch.object(sensor, "async_write_ha_state") as mock_write:
            sensor._on_telegram("1/2/4", 0)

        assert sensor.native_value == 0
        mock_write.assert_called_once()

    def test_on_telegram_tuple_value(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Test handling incoming telegram with tuple payload (2-byte DPT)."""
        from xknx.dpt import DPT2ByteFloat, DPTArray

        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )

        with patch.object(sensor, "async_write_ha_state") as mock_write:
            sensor._on_telegram("1/2/3", (5, 110))

        expected = DPT2ByteFloat().from_knx(DPTArray((5, 110)))
        assert sensor.native_value == expected
        mock_write.assert_called_once()


class TestAsyncSetupEntry:
    """Test async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_async_setup_entry_success(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_knx_gateway
    ):
        """Test successful sensor setup."""
        # Mock mapper
        mock_mapper = Mock()
        temp_entity = Mock()
        temp_entity.unique_id = "temp_001"
        temp_entity.name = "Temperature"
        temp_entity.device_id = "device_001"
        temp_entity.device_name = "Sensor"
        temp_entity.entity_type = "temperature"
        temp_entity.datapoints = {"Temperature": "1/2/3"}
        temp_entity.attributes = {
            "channel": 1,
            "sensor_type": 2,
            "serial_number": "123",
            "knx_address": "1.1.1",
            "device_class": "temperature",
            "unit_of_measurement": "°C",
        }
        temp_entity.parameters = {}  # LXP parameters
        mock_mapper.get_entities_by_platform.return_value = [temp_entity]

        # Mock KNX gateway discovered sensors
        mock_knx_gateway.get_discovered_sensors.return_value = {}

        # Create type-safe integration state
        state = IntegrationState(
            mapper=mock_mapper,
            config={},
            overrides={},
            knx_gateway=mock_knx_gateway,
            coordinator=mock_coordinator,
            entry=mock_config_entry,
        )
        mock_config_entry.runtime_data = state

        # Keep legacy dict storage for backward compatibility
        mock_hass.data[DOMAIN] = {}
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "coordinator": mock_coordinator,
            "mapper": mock_mapper,
            "knx_gateway": mock_knx_gateway,
        }

        # Setup async_add_entities callback
        async_add_entities = Mock()

        # Call setup
        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

        # Verify entities were added
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], LuxorLivingSensor)
        assert entities[0].name == "Temperature"

    @pytest.mark.asyncio
    async def test_async_setup_entry_no_entities(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_knx_gateway
    ):
        """Test setup with no sensor entities."""
        # Mock mapper with no sensor entities
        mock_mapper = Mock()
        mock_mapper.get_entities_by_platform.return_value = []

        # Mock KNX gateway discovered sensors
        mock_knx_gateway.get_discovered_sensors.return_value = {}

        # Create type-safe integration state with empty entities
        state = IntegrationState(
            mapper=mock_mapper,
            config={},
            overrides={},
            knx_gateway=mock_knx_gateway,
            coordinator=mock_coordinator,
            entry=mock_config_entry,
        )
        mock_config_entry.runtime_data = state

        # Keep legacy dict storage
        mock_hass.data[DOMAIN] = {}
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "coordinator": mock_coordinator,
            "mapper": mock_mapper,
            "knx_gateway": mock_knx_gateway,
        }

        # Setup async_add_entities callback
        async_add_entities = Mock()

        # Call setup
        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

        # Verify empty entity list was added
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 0

    @pytest.mark.asyncio
    async def test_async_setup_entry_missing_mapper(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_knx_gateway
    ):
        """Test setup skips entities when mapper is None."""
        mock_config_entry.runtime_data = MagicMock()
        mock_config_entry.runtime_data.mapper = None
        mock_config_entry.runtime_data.coordinator = mock_coordinator
        mock_config_entry.runtime_data.knx_gateway = mock_knx_gateway
        async_add_entities = Mock()

        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

        async_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_setup_entry_missing_coordinator(
        self, mock_hass, mock_config_entry, mock_knx_gateway
    ):
        """Test setup skips entities when coordinator is None."""
        mock_config_entry.runtime_data = MagicMock()
        mock_config_entry.runtime_data.mapper = MagicMock()
        mock_config_entry.runtime_data.coordinator = None
        mock_config_entry.runtime_data.knx_gateway = mock_knx_gateway
        async_add_entities = AsyncMock()

        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

        async_add_entities.assert_not_called()


@pytest.mark.smoke
class TestSensorRegistrationMutants:
    """Kill surviving sensor.py mutants: super() args, datapoint dispatch, entity_type."""

    def test_config_entry_stored_not_none(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Kill: super().__init__(coordinator, None, mapped_entity) mutation."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )
        assert sensor._config_entry is mock_config_entry

    def test_datapoint_address_none_initially_then_set(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: _datapoint_address = '' instead of None mutation."""
        entity = Mock()
        entity.unique_id = "no_dp"
        entity.name = "No DP Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "unknowntype"
        entity.datapoints = {}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingSensor(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert sensor._datapoint_address is None

    def test_entity_type_lowercased_for_dispatch(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: entity_type.lower() → entity_type.upper() mutation."""
        entity = Mock()
        entity.unique_id = "upper_test"
        entity.name = "Upper Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "TEMPERATURE"  # uppercase — .lower() makes it match
        entity.datapoints = {"Temperature": "5/1/1"}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingSensor(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        # With .lower(): "temperature" == "temperature" → address set
        # With .upper(): "TEMPERATURE" == "temperature" → no match → None
        assert sensor._datapoint_address == "5/1/1"

    def test_temperature_dispatch_uses_temperature_key(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: 'temperature' == 'XXtemperatureXX' or 'TEMPERATURE' mutations."""
        entity = Mock()
        entity.unique_id = "t_dispatch"
        entity.name = "T Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "temperature"
        entity.datapoints = {"Temperature": "6/1/1"}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingSensor(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert sensor._datapoint_address == "6/1/1"

    def test_humidity_dispatch_uses_humidity_key(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: 'humidity' == 'XXhumidityXX' or 'HUMIDITY' mutations."""
        entity = Mock()
        entity.unique_id = "h_dispatch"
        entity.name = "H Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "humidity"
        entity.datapoints = {"Humidity": "6/2/1"}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingSensor(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert sensor._datapoint_address == "6/2/1"

    def test_humidity_datapoint_not_none_when_present(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: self._datapoint_address = None (instead of datapoints.get('Humidity'))."""
        entity = Mock()
        entity.unique_id = "h_none"
        entity.name = "H Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "humidity"
        entity.datapoints = {"Humidity": "6/2/1"}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingSensor(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert sensor._datapoint_address is not None

    @pytest.mark.asyncio
    async def test_async_added_registers_listener_with_address(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Kill: register_listener(None, handler) mutation."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )
        await sensor.async_added_to_hass()
        registered = [c[0][0] for c in mock_knx_gateway.register_listener.call_args_list]
        assert "1/2/3" in registered


@pytest.mark.smoke
class TestSensorMutationTargets:
    """Smoke tests targeting surviving mutants in LuxorLivingSensor."""

    def test_native_value_initially_none(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Kill: _attr_native_value = None → some other default."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )
        assert sensor.native_value is None

    def test_on_telegram_none_value_skips_state_update(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Kill: 'if normalized is None: return' guard removed."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )
        sensor.async_write_ha_state = Mock()
        sensor._on_telegram("1/2/3", None)
        assert sensor.native_value is None
        sensor.async_write_ha_state.assert_not_called()

    def test_normalize_value_len1_tuple_passthrough(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Kill: len == 2 → len == 1, would decode 1-byte tuples as DPT float."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )
        result = sensor._normalize_value((42,))
        assert result == (42,)

    def test_normalize_value_len3_tuple_passthrough(
        self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
    ):
        """Kill: len == 2 → len == 3, would decode 3-byte tuples as DPT float."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )
        result = sensor._normalize_value((1, 2, 3))
        assert result == (1, 2, 3)

    def test_datapoint_address_temperature_key(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: 'Temperature' key → 'temperature' case mutation."""
        entity = Mock()
        entity.unique_id = "temp_test"
        entity.name = "Test"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "temperature"
        entity.datapoints = {"Temperature": "3/1/1"}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingSensor(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert sensor._datapoint_address == "3/1/1"

    def test_datapoint_address_co2_key(self, mock_coordinator, mock_config_entry, mock_knx_gateway):
        """Kill: 'CO2' key mutation in entity_type dispatch."""
        entity = Mock()
        entity.unique_id = "co2_test"
        entity.name = "CO2 Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "co2"
        entity.datapoints = {"CO2": "4/1/1"}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingSensor(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert sensor._datapoint_address == "4/1/1"

    def test_datapoint_address_fallback_first_value(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: fallback 'list(datapoints.values())[0]' index mutation."""
        entity = Mock()
        entity.unique_id = "fallback_test"
        entity.name = "Generic Sensor"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "generic"
        entity.datapoints = {"SomeValue": "5/1/1"}
        entity.attributes = {}
        entity.parameters = {}
        sensor = LuxorLivingSensor(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert sensor._datapoint_address == "5/1/1"


# Add import for DOMAIN constant
from custom_components.luxor_living.const import DOMAIN
