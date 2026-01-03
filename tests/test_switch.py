"""Tests for LUXORliving switch platform."""

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.coordinator import LuxorLivingCoordinator
from custom_components.luxor_living.knx_gateway import LuxorKNXGateway
from custom_components.luxor_living.switch import (
    LuxorLivingSwitch,
    async_setup_entry,
)


@pytest.fixture
def mock_coordinator():
    """Mock Data Coordinator."""
    coordinator = Mock(spec=LuxorLivingCoordinator)
    coordinator.last_update_success = True
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
    entity.entity_type = "switch"
    entity.datapoints = {
        "OnOff": "1/2/3",
        "StatusOnOff": "1/2/4",
    }
    return entity


class TestLuxorLivingSwitch:
    """Test LuxorLivingSwitch class."""

    def test_init(self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway):
        """Test switch initialization."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )

        assert switch.coordinator == mock_coordinator
        assert switch.is_on is False
        assert switch._address_on == "1/2/3"
        assert switch._address_status == "1/2/4"

        # Should register listeners
        assert mock_knx_gateway.register_listener.call_count == 2

    @pytest.mark.asyncio
    async def test_async_added_to_hass(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test switch added to hass - should request initial state."""
        mock_knx_gateway._connected = True
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        switch.async_on_remove = Mock(return_value=lambda: None)

        await switch.async_added_to_hass()

        # Should request initial state from BOTH addresses
        assert mock_knx_gateway.async_read_group_address.call_count == 2

    @pytest.mark.asyncio
    async def test_turn_on(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test turning switch on."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        switch.async_write_ha_state = Mock()

        await switch.async_turn_on()

        mock_knx_gateway.async_send_telegram.assert_called_once()
        assert switch.is_on is True

    @pytest.mark.asyncio
    async def test_turn_off(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test turning switch off."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        switch.async_write_ha_state = Mock()

        await switch.async_turn_off()

        mock_knx_gateway.async_send_telegram.assert_called_once()
        assert switch.is_on is False

    def test_handle_knx_update(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test handling KNX status update."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        switch.async_write_ha_state = Mock()

        # Simulate KNX status update
        switch._handle_knx_update("1/2/4", True)

        assert switch.is_on is True

    def test_handle_knx_update_off(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test handling KNX status update (off)."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        switch.async_write_ha_state = Mock()
        switch._attr_is_on = True

        # Simulate KNX status update (off)
        switch._handle_knx_update("1/2/4", False)

        assert switch.is_on is False

    def test_handle_knx_update_wrong_address(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test that wrong addresses are ignored."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        switch.async_write_ha_state = Mock()

        # Simulate update on wrong address
        switch._handle_knx_update("9/9/9", True)

        # State should not change
        assert switch.is_on is False

    @pytest.mark.asyncio
    async def test_will_remove_from_hass(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test cleanup when entity is removed."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )

        await switch.async_will_remove_from_hass()

        # Should unregister listeners
        assert mock_knx_gateway.unregister_listener.call_count >= 1


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.fixture
    def switch(self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway):
        """Create a switch instance for testing."""
        return LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )

    def test_rate_limiting_not_triggered(self, switch):
        """Test that rate limiting doesn't block normal usage."""
        # Should not be rate limited initially
        assert not switch._is_rate_limited()
        assert not switch._is_rate_limited()
        assert not switch._is_rate_limited()
        assert not switch._is_rate_limited()
        assert not switch._is_rate_limited()

    def test_rate_limiting_triggered(self, switch, monkeypatch):
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

        monkeypatch.setattr(time, "time", mock_time)

        # First 5 calls should not be limited
        for i in range(5):
            assert not switch._is_rate_limited(), f"Call {i+1} should not be limited"

        # 6th call should be limited
        assert switch._is_rate_limited(), "6th call should be rate limited"

    def test_rate_limiting_resets_after_time(self, switch, monkeypatch):
        """Test that rate limiting resets after timestamps expire."""
        import time

        # First set of calls
        timestamps1 = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
        call_count = 0

        def mock_time1():
            nonlocal call_count
            result = timestamps1[min(call_count, len(timestamps1) - 1)]
            call_count += 1
            return result

        monkeypatch.setattr(time, "time", mock_time1)

        # Trigger rate limiting
        for _ in range(6):
            switch._is_rate_limited()

        assert switch._is_rate_limited()

        # Now simulate time passing (2 seconds later)
        timestamps2 = [2.0]
        call_count = 0

        def mock_time2():
            return 2.0

        monkeypatch.setattr(time, "time", mock_time2)

        # Should not be limited anymore (old timestamps removed)
        assert not switch._is_rate_limited()

    @pytest.mark.asyncio
    async def test_turn_on_rate_limited(self, switch, mock_knx_gateway):
        """Test that turn_on is blocked when rate limited."""
        # Trigger rate limiting
        for _ in range(6):
            switch._is_rate_limited()

        # turn_on should not send telegram
        await switch.async_turn_on()
        mock_knx_gateway.async_send_telegram.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_rate_limited(self, switch, mock_knx_gateway):
        """Test that turn_off is blocked when rate limited."""
        # Trigger rate limiting
        for _ in range(6):
            switch._is_rate_limited()

        # turn_off should not send telegram
        await switch.async_turn_off()
        mock_knx_gateway.async_send_telegram.assert_not_called()
