"""Tests for LUXORliving switch platform."""

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.config_entries import ConfigEntry

from custom_components.luxor_living.coordinator import LuxorLivingCoordinator
from custom_components.luxor_living.knx_gateway import LuxorKNXGateway
from custom_components.luxor_living.switch import (
    LuxorLivingSwitch,
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


@pytest.mark.smoke
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


@pytest.mark.smoke
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


@pytest.mark.smoke
class TestSwitchMutationTargets:
    """Smoke tests targeting surviving mutants in LuxorLivingSwitch."""

    @pytest.mark.asyncio
    async def test_turn_on_sends_true_with_binary_type(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: send value True → False, type 'binary' → None."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        switch.async_write_ha_state = Mock()
        await switch.async_turn_on()
        args = mock_knx_gateway.async_send_telegram.call_args[0]
        assert args[1] is True
        assert args[2] == "binary"

    @pytest.mark.asyncio
    async def test_turn_off_sends_false_with_binary_type(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: send value False → True, type 'binary' → None."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        switch.async_write_ha_state = Mock()
        await switch.async_turn_off()
        args = mock_knx_gateway.async_send_telegram.call_args[0]
        assert args[1] is False
        assert args[2] == "binary"

    def test_status_address_priority_status_at_onoff(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: 'status@OnOff' key → 'StatusOnOff' order mutation."""
        entity = Mock()
        entity.unique_id = "priority_test"
        entity.name = "Priority Switch"
        entity.device_id = "dev1"
        entity.device_name = "Device 1"
        entity.entity_type = "switch"
        entity.datapoints = {"OnOff": "1/1/1", "status@OnOff": "1/1/2", "StatusOnOff": "1/1/3"}
        entity.parameters = {}
        entity.attributes = {}
        switch = LuxorLivingSwitch(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert switch._address_status == "1/1/2"

    def test_fallback_address_on_from_schalten_onoff(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: 'OnOff' key mutation loses SchaltenOnOff fallback."""
        entity = Mock()
        entity.unique_id = "schalten_test"
        entity.name = "Schalten Switch"
        entity.device_id = "dev1"
        entity.device_name = "Device 1"
        entity.entity_type = "switch"
        entity.datapoints = {"SchaltenOnOff": "2/3/4"}
        entity.parameters = {}
        entity.attributes = {}
        switch = LuxorLivingSwitch(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert switch._address_on == "2/3/4"

    def test_extra_state_attributes_key_names(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: 'knx_address_on' / 'knx_address_status' key string mutations."""
        entity = Mock()
        entity.unique_id = "attrs_test"
        entity.name = "Attrs Switch"
        entity.device_id = "dev1"
        entity.device_name = "Device"
        entity.entity_type = "switch"
        entity.datapoints = {"OnOff": "1/2/3", "StatusOnOff": "1/2/4"}
        entity.parameters = {}
        entity.attributes = {}
        switch = LuxorLivingSwitch(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        attrs = switch.extra_state_attributes
        assert "knx_address_on" in attrs
        assert "knx_address_status" in attrs


@pytest.mark.smoke
class TestSwitchRegistrationMutants:
    """Kill surviving mutants about super() args, register_listener, is_initial."""

    def test_config_entry_stored_not_none(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: super().__init__(coordinator, None, mapped_entity) mutation."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        assert switch._config_entry is mock_config_entry

    def test_mapped_entity_stored_not_none(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: super().__init__(coordinator, entry, None) mutation."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        assert switch._mapped_entity is mock_mapped_entity

    def test_register_listener_uses_real_addresses(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: register_listener(None, handler) mutations."""
        _ = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        registered = [c[0][0] for c in mock_knx_gateway.register_listener.call_args_list]
        assert "1/2/3" in registered
        assert "1/2/4" in registered

    def test_listen_addresses_contain_real_addresses(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: _listen_addresses.append(None) mutation."""
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        assert "1/2/3" in switch._listen_addresses
        assert "1/2/4" in switch._listen_addresses

    def test_same_address_not_registered_twice(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: _address_on != _address_status → or mutation."""
        entity = Mock()
        entity.unique_id = "same_addr"
        entity.name = "Same Switch"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "switch"
        entity.datapoints = {"OnOff": "1/1/1", "status@OnOff": "1/1/1"}
        entity.parameters = {}
        entity.attributes = {}
        _ = LuxorLivingSwitch(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert mock_knx_gateway.register_listener.call_count == 1

    @pytest.mark.asyncio
    async def test_async_added_reads_with_is_initial_true(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: is_initial=True → is_initial=False mutation."""
        mock_knx_gateway._connected = True
        switch = LuxorLivingSwitch(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        switch.async_on_remove = Mock(return_value=lambda: None)
        await switch.async_added_to_hass()
        for call in mock_knx_gateway.async_read_group_address.call_args_list:
            assert call.kwargs.get("is_initial") is True
