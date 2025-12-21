"""Tests for LUXORliving light platform."""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from custom_components.luxor_living.light import (
    async_setup_entry,
    LuxorLivingLight,
    LuxorLivingDimmableLight,
)
from custom_components.luxor_living.knx_gateway import LuxorKNXGateway


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def mock_knx_gateway():
    """Mock KNX Gateway."""
    gateway = Mock(spec=LuxorKNXGateway)
    gateway.async_send_telegram = AsyncMock(return_value=True)
    gateway.async_read_group_address = AsyncMock(return_value=True)
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

    def test_init(self, mock_mapped_entity, mock_knx_gateway):
        """Test light initialization."""
        light = LuxorLivingLight(mock_mapped_entity, mock_knx_gateway)
        
        assert light.unique_id == "test_light_001"
        assert light.name == "Test Light"
        assert light.is_on is False
        assert light._address_on == "1/2/3"
        assert light._address_status == "1/2/4"
        
        # Should register listener for status updates
        mock_knx_gateway.register_listener.assert_called_once_with(
            "1/2/4",
            light._handle_knx_update
        )

    @pytest.mark.asyncio
    async def test_async_added_to_hass(self, mock_mapped_entity, mock_knx_gateway):
        """Test entity added to hass - should request initial state."""
        mock_knx_gateway._connected = True  # KNX is connected
        light = LuxorLivingLight(mock_mapped_entity, mock_knx_gateway)
        
        await light.async_added_to_hass()
        
        # Should request current state from BOTH addresses (STATUS and CONTROL)
        assert mock_knx_gateway.async_read_group_address.call_count == 2
        mock_knx_gateway.async_read_group_address.assert_any_call("1/2/4", is_initial=True)  # STATUS
        mock_knx_gateway.async_read_group_address.assert_any_call("1/2/3", is_initial=True)  # CONTROL

    @pytest.mark.asyncio
    async def test_async_added_to_hass_no_status_address(self, mock_knx_gateway):
        """Test entity added when no status address available - should use OnOff as fallback."""
        mock_knx_gateway._connected = True  # KNX is connected
        entity = Mock()
        entity.unique_id = "test_light_no_status"
        entity.name = "Test Light No Status"
        entity.device_id = "device_003"
        entity.device_name = "Test Device"
        entity.entity_type = "switch_light"
        entity.datapoints = {"OnOff": "1/2/8"}  # No status address
        
        light = LuxorLivingLight(entity, mock_knx_gateway)
        
        await light.async_added_to_hass()
        
        # Should fallback to OnOff address for reading
        mock_knx_gateway.async_read_group_address.assert_called_once_with("1/2/8", is_initial=True)

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_mapped_entity, mock_knx_gateway):
        """Test turning light on."""
        light = LuxorLivingLight(mock_mapped_entity, mock_knx_gateway)
        light.async_write_ha_state = Mock()
        
        await light.async_turn_on()
        
        mock_knx_gateway.async_send_telegram.assert_called_once_with(
            "1/2/3",
            True,
            "binary"
        )
        assert light.is_on is True

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_mapped_entity, mock_knx_gateway):
        """Test turning light off."""
        light = LuxorLivingLight(mock_mapped_entity, mock_knx_gateway)
        light.async_write_ha_state = Mock()
        light._attr_is_on = True
        
        await light.async_turn_off()
        
        mock_knx_gateway.async_send_telegram.assert_called_once_with(
            "1/2/3",
            False,
            "binary"
        )
        assert light.is_on is False

    def test_handle_knx_update(self, mock_mapped_entity, mock_knx_gateway):
        """Test handling KNX status update."""
        light = LuxorLivingLight(mock_mapped_entity, mock_knx_gateway)
        light.schedule_update_ha_state = Mock()
        
        # Simulate KNX status update
        light._handle_knx_update("1/2/4", True)
        
        assert light.is_on is True
        light.schedule_update_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_will_remove_from_hass(self, mock_mapped_entity, mock_knx_gateway):
        """Test cleanup when entity is removed."""
        light = LuxorLivingLight(mock_mapped_entity, mock_knx_gateway)
        
        await light.async_will_remove_from_hass()
        
        mock_knx_gateway.unregister_listener.assert_called_once_with(
            "1/2/4",
            light._handle_knx_update
        )


class TestLuxorLivingDimmableLight:
    """Test LuxorLivingDimmableLight class."""

    def test_init(self, mock_dimmable_entity, mock_knx_gateway):
        """Test dimmable light initialization."""
        light = LuxorLivingDimmableLight(mock_dimmable_entity, mock_knx_gateway)
        
        assert light.unique_id == "test_dim_light_001"
        assert light.name == "Test Dimmable Light"
        assert light.brightness == 255
        assert light._address_dim == "1/2/7"
        
        # Should register listeners for status and brightness
        assert mock_knx_gateway.register_listener.call_count == 2

    @pytest.mark.asyncio
    async def test_async_added_to_hass(self, mock_dimmable_entity, mock_knx_gateway):
        """Test dimmable light added to hass - should request initial state."""
        mock_knx_gateway._connected = True  # KNX is connected
        light = LuxorLivingDimmableLight(mock_dimmable_entity, mock_knx_gateway)
        
        await light.async_added_to_hass()
        
        # Should request status, control, and brightness (3 addresses)
        assert mock_knx_gateway.async_read_group_address.call_count == 3
        calls = [call.args[0] for call in mock_knx_gateway.async_read_group_address.call_args_list]
        assert "1/2/6" in calls  # Status
        assert "1/2/5" in calls  # Control (OnOff)
        assert "1/2/7" in calls  # Brightness

    @pytest.mark.asyncio
    async def test_turn_on_with_brightness(self, mock_dimmable_entity, mock_knx_gateway):
        """Test turning on with specific brightness."""
        light = LuxorLivingDimmableLight(mock_dimmable_entity, mock_knx_gateway)
        light.async_write_ha_state = Mock()
        
        await light.async_turn_on(brightness=128)
        
        # Should send percentage value (128 / 255 * 100 = 50%)
        mock_knx_gateway.async_send_telegram.assert_called_once_with(
            "1/2/7",
            50,
            "percent"
        )
        assert light.is_on is True
        assert light.brightness == 128

    def test_handle_brightness_update(self, mock_dimmable_entity, mock_knx_gateway):
        """Test handling KNX brightness update."""
        light = LuxorLivingDimmableLight(mock_dimmable_entity, mock_knx_gateway)
        light.schedule_update_ha_state = Mock()
        
        # Simulate KNX brightness update (75%)
        light._handle_brightness_update("1/2/7", 75)
        
        # Should convert 75% to brightness (191/255)
        assert light.brightness == 191
        assert light.is_on is True
        light.schedule_update_ha_state.assert_called_once()

    def test_handle_brightness_update_zero(self, mock_dimmable_entity, mock_knx_gateway):
        """Test handling zero brightness update."""
        light = LuxorLivingDimmableLight(mock_dimmable_entity, mock_knx_gateway)
        light.schedule_update_ha_state = Mock()
        
        # Simulate KNX brightness update (0%)
        light._handle_brightness_update("1/2/7", 0)
        
        assert light.brightness == 0
        assert light.is_on is False
