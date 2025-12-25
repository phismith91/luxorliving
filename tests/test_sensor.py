"""Tests for LUXORliving sensor platform."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.coordinator import LuxorLivingCoordinator
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
    return entity


class TestLuxorLivingSensor:
    """Test LuxorLivingSensor entity."""

    def test_init(self, mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway):
        """Test sensor initialization."""
        sensor = LuxorLivingSensor(
            mock_coordinator, mock_config_entry, mock_temperature_entity, mock_knx_gateway
        )

        assert sensor.name == "Test Temperature"
        assert sensor.unique_id == "test_temp_sensor_001"
        assert sensor.native_unit_of_measurement == "°C"
        assert sensor.device_class == "temperature"
        assert sensor.native_value is None

    def test_init_humidity(self, mock_coordinator, mock_config_entry, mock_humidity_entity, mock_knx_gateway):
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
        mock_mapper.get_entities_by_platform.return_value = [temp_entity]

        # Setup integration data
        mock_hass.data[DOMAIN] = {}
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "coordinator": mock_coordinator,
            "mapper": mock_mapper,
            "knx_gateway": mock_knx_gateway,
        }

        # Setup async_add_entities callback
        async_add_entities = AsyncMock()

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

        # Setup integration data
        mock_hass.data[DOMAIN] = {}
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "coordinator": mock_coordinator,
            "mapper": mock_mapper,
            "knx_gateway": mock_knx_gateway,
        }

        # Setup async_add_entities callback
        async_add_entities = AsyncMock()

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
        """Test setup when mapper is missing."""
        # Setup integration data without mapper
        mock_hass.data[DOMAIN] = {}
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "coordinator": mock_coordinator,
            "knx_gateway": mock_knx_gateway,
        }

        async_add_entities = AsyncMock()

        # Should return early without error
        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

        async_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_setup_entry_missing_coordinator(
        self, mock_hass, mock_config_entry, mock_knx_gateway
    ):
        """Test setup when coordinator is missing."""
        mock_mapper = Mock()
        mock_mapper.get_entities_by_platform.return_value = []

        # Setup integration data without coordinator
        mock_hass.data[DOMAIN] = {}
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "mapper": mock_mapper,
            "knx_gateway": mock_knx_gateway,
        }

        async_add_entities = AsyncMock()

        # Should return early without error
        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

        async_add_entities.assert_not_called()


# Add import for DOMAIN constant
from custom_components.luxor_living.const import DOMAIN
