"""Tests for LUXORliving switch platform."""
import pytest
from unittest.mock import Mock, AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.luxor_living.switch import (
    LuxorLivingSwitch,
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
    """Mock mapped entity for switch."""
    entity = Mock()
    entity.unique_id = "test_switch_001"
    entity.name = "Test Switch"
    entity.device_id = "device_001"
    entity.device_name = "Test Device"
    entity.datapoints = {
        "OnOff": "1/3/1",
        "status@OnOff": "1/3/2",
    }
    return entity


class TestLuxorLivingSwitch:
    """Test LuxorLivingSwitch class."""

    def test_init(self, mock_mapped_entity, mock_knx_gateway):
        """Test switch initialization."""
        switch = LuxorLivingSwitch(mock_mapped_entity, mock_knx_gateway)
        
        assert switch.unique_id == "test_switch_001"
        assert switch.name == "Test Switch"
        assert switch.is_on is False
        assert switch._address_on == "1/3/1"
        assert switch._address_status == "1/3/2"
        
        # Should register listener for status updates
        mock_knx_gateway.register_listener.assert_called_once_with(
            "1/3/2",
            switch._handle_knx_update
        )

    @pytest.mark.asyncio
    async def test_async_added_to_hass(self, mock_mapped_entity, mock_knx_gateway):
        """Test entity added to hass - should request initial state."""
        mock_knx_gateway._connected = True  # KNX is connected
        switch = LuxorLivingSwitch(mock_mapped_entity, mock_knx_gateway)
        
        await switch.async_added_to_hass()
        
        # Should request current state from KNX
        mock_knx_gateway.async_read_group_address.assert_called_once_with("1/3/2", is_initial=True)

    @pytest.mark.asyncio
    async def test_async_added_to_hass_no_status_address(self, mock_knx_gateway):
        """Test entity added when no status address available - should use OnOff as fallback."""
        mock_knx_gateway._connected = True  # KNX is connected
        entity = Mock()
        entity.unique_id = "test_switch_no_status"
        entity.name = "Test Switch No Status"
        entity.device_id = "device_002"
        entity.device_name = "Test Device"
        entity.datapoints = {"OnOff": "1/3/3"}  # No status address
        
        switch = LuxorLivingSwitch(entity, mock_knx_gateway)
        
        await switch.async_added_to_hass()
        
        # Should fallback to OnOff address for reading
        mock_knx_gateway.async_read_group_address.assert_called_once_with("1/3/3", is_initial=True)

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_mapped_entity, mock_knx_gateway):
        """Test turning switch on."""
        switch = LuxorLivingSwitch(mock_mapped_entity, mock_knx_gateway)
        switch.async_write_ha_state = Mock()
        
        await switch.async_turn_on()
        
        mock_knx_gateway.async_send_telegram.assert_called_once_with(
            "1/3/1",
            True,
            "binary"
        )
        assert switch.is_on is True

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_mapped_entity, mock_knx_gateway):
        """Test turning switch off."""
        switch = LuxorLivingSwitch(mock_mapped_entity, mock_knx_gateway)
        switch.async_write_ha_state = Mock()
        switch._attr_is_on = True
        
        await switch.async_turn_off()
        
        mock_knx_gateway.async_send_telegram.assert_called_once_with(
            "1/3/1",
            False,
            "binary"
        )
        assert switch.is_on is False

    def test_handle_knx_update(self, mock_mapped_entity, mock_knx_gateway):
        """Test handling KNX status update."""
        switch = LuxorLivingSwitch(mock_mapped_entity, mock_knx_gateway)
        switch.schedule_update_ha_state = Mock()
        
        # Simulate KNX status update
        switch._handle_knx_update("1/3/2", True)
        
        assert switch.is_on is True
        switch.schedule_update_ha_state.assert_called_once()

    def test_handle_knx_update_off(self, mock_mapped_entity, mock_knx_gateway):
        """Test handling KNX status update - off."""
        switch = LuxorLivingSwitch(mock_mapped_entity, mock_knx_gateway)
        switch._attr_is_on = True
        switch.schedule_update_ha_state = Mock()
        
        # Simulate KNX status update
        switch._handle_knx_update("1/3/2", False)
        
        assert switch.is_on is False
        switch.schedule_update_ha_state.assert_called_once()

    def test_handle_knx_update_wrong_address(self, mock_mapped_entity, mock_knx_gateway):
        """Test KNX update from different address is ignored."""
        switch = LuxorLivingSwitch(mock_mapped_entity, mock_knx_gateway)
        switch.schedule_update_ha_state = Mock()
        
        # Simulate update from wrong address
        switch._handle_knx_update("9/9/9", True)
        
        # State should not change
        assert switch.is_on is False
        switch.schedule_update_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_will_remove_from_hass(self, mock_mapped_entity, mock_knx_gateway):
        """Test cleanup when entity is removed."""
        switch = LuxorLivingSwitch(mock_mapped_entity, mock_knx_gateway)
        
        await switch.async_will_remove_from_hass()
        
        mock_knx_gateway.unregister_listener.assert_called_once_with(
            "1/3/2",
            switch._handle_knx_update
        )
