"""Tests for LUXORliving light platform."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.coordinator import LuxorLivingCoordinator
from custom_components.luxor_living.knx_gateway import LuxorKNXGateway
from custom_components.luxor_living.light import (
    LuxorLivingDimmableLight,
    LuxorLivingLight,
    async_setup_entry,
)


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
    gateway.async_read_group_address = AsyncMock(return_value=True)
    gateway.async_read_via_rest = AsyncMock(return_value=None)
    gateway.register_listener = Mock()
    gateway.unregister_listener = Mock()
    return gateway


@pytest.fixture
def mock_mapped_entity():
    """Mock mapped entity for light."""
    entity = Mock()
    entity.unique_id = "test_light_001"
    entity.name = "Test Light"
    entity.device_id = "device_001"
    entity.device_name = "Test Device"
    entity.entity_type = "switch_light"
    entity.datapoints = {
        "OnOff": "1/2/3",
        "StatusOnOff": "1/2/4",
    }
    return entity


@pytest.fixture
def mock_dimmable_entity():
    """Mock mapped entity for dimmable light."""
    entity = Mock()
    entity.unique_id = "test_dim_light_001"
    entity.name = "Test Dimmable Light"
    entity.device_id = "device_002"
    entity.device_name = "Test Dimmer"
    entity.entity_type = "dimmable_light"
    entity.datapoints = {
        "OnOff": "1/2/5",
        "StatusOnOff": "1/2/6",
        "Dimmen%": "1/2/7",
    }
    return entity


class TestLuxorLivingLight:
    """Test LuxorLivingLight class."""

    def test_init(self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway):
        """Test light initialization."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )

        assert light.coordinator == mock_coordinator
        assert light.is_on is False
        assert light._address_on == "1/2/3"
        assert light._address_status == "1/2/4"

        # Should register listeners for status AND control addresses
        assert mock_knx_gateway.register_listener.call_count == 2

    @pytest.mark.asyncio
    async def test_async_added_to_hass(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test entity added to hass - should request initial state."""
        mock_knx_gateway._connected = True  # KNX is connected
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_on_remove = Mock(return_value=lambda: None)

        await light.async_added_to_hass()

        # Request current state from BOTH addresses
        assert mock_knx_gateway.async_read_group_address.call_count == 2

    @pytest.mark.asyncio
    async def test_turn_on(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test turning light on."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        await light.async_turn_on()

        mock_knx_gateway.async_send_telegram.assert_called_once()
        assert light.is_on is True

    @pytest.mark.asyncio
    async def test_turn_off(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test turning light off."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        await light.async_turn_off()

        mock_knx_gateway.async_send_telegram.assert_called_once()
        assert light.is_on is False

    def test_handle_knx_update(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test handling KNX status update."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        # Simulate KNX status update
        light._handle_knx_update("1/2/4", True)

        assert light.is_on is True

    @pytest.mark.asyncio
    async def test_will_remove_from_hass(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test cleanup when entity is removed."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )

        await light.async_will_remove_from_hass()

        # Should unregister listeners
        assert mock_knx_gateway.unregister_listener.call_count >= 1


class TestLuxorLivingDimmableLight:
    """Test LuxorLivingDimmableLight class."""

    def test_init(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test dimmable light initialization."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )

        assert light.coordinator == mock_coordinator
        assert light.brightness == 255
        assert light._address_dim == "1/2/7"

    @pytest.mark.asyncio
    async def test_async_added_to_hass(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test dimmable light added to hass."""
        mock_knx_gateway._connected = True
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_on_remove = Mock(return_value=lambda: None)

        await light.async_added_to_hass()

        # Should request initial state
        assert mock_knx_gateway.async_read_group_address.call_count >= 2

    @pytest.mark.asyncio
    async def test_turn_on_with_brightness(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test turning on with specific brightness."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        await light.async_turn_on(brightness=128)

        mock_knx_gateway.async_send_telegram.assert_called_once()
        assert light.is_on is True

    def test_handle_brightness_update(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test handling KNX brightness update."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        # Simulate brightness update (50% = 50)
        light._handle_brightness_update("1/2/7", 50)

        assert light.is_on is True
        assert light.brightness == int(50 * 255 / 100)

    def test_handle_brightness_update_zero(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test handling zero brightness update."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        # Simulate brightness update (0%)
        light._handle_brightness_update("1/2/7", 0)

        assert light.is_on is False
        assert light.brightness == 0


class TestLightRateLimiting:
    """Test rate limiting functionality for lights."""

    @pytest.fixture
    def light(self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway):
        """Create a light instance for testing."""
        return LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )

    def test_rate_limiting_not_triggered(self, light):
        """Test that rate limiting doesn't block normal usage."""
        # Should not be rate limited initially
        assert not light._is_rate_limited()
        assert not light._is_rate_limited()
        assert not light._is_rate_limited()
        assert not light._is_rate_limited()
        assert not light._is_rate_limited()

    def test_rate_limiting_triggered(self, light, monkeypatch):
        """Test that rate limiting blocks after 5 commands in 1 second."""
        import time
        
        # Mock time to control timestamps
        timestamps = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]  # 6 calls within 0.5s
        call_count = 0
        
        def mock_time():
            nonlocal call_count
            result = timestamps[min(call_count, len(timestamps) - 1)]
            call_count += 1
            return result
        
        monkeypatch.setattr(time, 'time', mock_time)
        
        # First 5 calls should not be limited
        for i in range(5):
            assert not light._is_rate_limited(), f"Call {i+1} should not be limited"
        
        # 6th call should be limited
        assert light._is_rate_limited(), "6th call should be rate limited"

    @pytest.mark.asyncio
    async def test_turn_on_rate_limited(self, light, mock_knx_gateway):
        """Test that turn_on is blocked when rate limited."""
        # Trigger rate limiting
        for _ in range(6):
            light._is_rate_limited()
        
        # turn_on should not send telegram
        await light.async_turn_on()
        mock_knx_gateway.async_send_telegram.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_rate_limited(self, light, mock_knx_gateway):
        """Test that turn_off is blocked when rate limited."""
        # Trigger rate limiting
        for _ in range(6):
            light._is_rate_limited()
        
        # turn_off should not send telegram
        await light.async_turn_off()
        mock_knx_gateway.async_send_telegram.assert_not_called()
