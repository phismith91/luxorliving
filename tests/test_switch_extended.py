"""Extended tests for switch.py covering uncovered branches."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.luxor_living.switch import LuxorLivingSwitch


def _make_mapped_entity(datapoints=None):
    me = MagicMock()
    me.unique_id = "test_switch"
    me.name = "Test Switch"
    me.device_name = "Test Device"
    me.device_id = "dev_001"
    me.entity_type = "switch"
    me.parameters = {}
    me.attributes = {}
    me.datapoints = datapoints or {}
    return me


def _make_switch(datapoints=None, connected=True):
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    coordinator.async_request_refresh = AsyncMock()

    gateway = MagicMock()
    gateway.connected = connected
    gateway.simulation_mode = False
    gateway._connected = connected
    gateway.register_listener = MagicMock()
    gateway.unregister_listener = MagicMock()
    gateway.async_read_group_address = AsyncMock(return_value=True)
    gateway.async_send_telegram = AsyncMock(return_value=True)

    entry = MagicMock()
    entry.runtime_data = MagicMock()
    entry.runtime_data.knx_gateway = gateway

    mapped = _make_mapped_entity(datapoints)
    entity = LuxorLivingSwitch(coordinator, entry, mapped, gateway)
    entity.async_write_ha_state = MagicMock()
    return entity, gateway


# ── __init__ ──────────────────────────────────────────────────────────────────


class TestSwitchInit:
    def test_address_on_from_onoff(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        assert entity._address_on == "1/0/0"

    def test_address_on_from_schalten(self):
        entity, _ = _make_switch({"SchaltenOnOff": "1/0/1"})
        assert entity._address_on == "1/0/1"

    def test_address_status_from_status_onoff(self):
        entity, _ = _make_switch({"status@OnOff": "1/0/2"})
        assert entity._address_status == "1/0/2"

    def test_registers_status_listener(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        addresses = [call[0][0] for call in gateway.register_listener.call_args_list]
        assert "1/0/2" in addresses

    def test_registers_control_listener_when_different_from_status(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        addresses = [call[0][0] for call in gateway.register_listener.call_args_list]
        assert "1/0/0" in addresses

    def test_no_duplicate_listener_when_same_address(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0", "status@OnOff": "1/0/0"})
        # Should only register once since both addresses are the same
        assert gateway.register_listener.call_count == 1

    def test_initial_state_is_off(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        assert entity._attr_is_on is False


# ── _handle_knx_update ────────────────────────────────────────────────────────


class TestHandleKnxUpdate:
    def test_update_on_state_on_control_address(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        entity._handle_knx_update("1/0/0", True)
        assert entity._attr_is_on is True
        entity.async_write_ha_state.assert_called_once()

    def test_update_off_state(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        entity._attr_is_on = True
        entity._handle_knx_update("1/0/0", False)
        assert entity._attr_is_on is False

    def test_update_on_status_address(self):
        entity, _ = _make_switch({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        entity._handle_knx_update("1/0/2", True)
        assert entity._attr_is_on is True

    def test_update_only_status_address_set(self):
        # _address_on is None — covers the 227->229 branch
        entity, _ = _make_switch({"status@OnOff": "1/0/2"})
        entity._handle_knx_update("1/0/2", True)
        assert entity._attr_is_on is True

    def test_ignores_unknown_address(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        entity._handle_knx_update("9/9/9", True)
        entity.async_write_ha_state.assert_not_called()


# ── async_turn_on / async_turn_off ────────────────────────────────────────────


class TestTurnOnOff:
    @pytest.mark.asyncio
    async def test_turn_on_sends_telegram(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0"})
        await entity.async_turn_on()
        gateway.async_send_telegram.assert_awaited_once_with("1/0/0", True, "binary")

    @pytest.mark.asyncio
    async def test_turn_on_sets_state_true(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        await entity.async_turn_on()
        assert entity._attr_is_on is True
        entity.async_write_ha_state.assert_called()

    @pytest.mark.asyncio
    async def test_turn_off_sends_telegram(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0"})
        entity._attr_is_on = True
        await entity.async_turn_off()
        gateway.async_send_telegram.assert_awaited_once_with("1/0/0", False, "binary")

    @pytest.mark.asyncio
    async def test_turn_off_sets_state_false(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        entity._attr_is_on = True
        await entity.async_turn_off()
        assert entity._attr_is_on is False

    @pytest.mark.asyncio
    async def test_turn_on_no_address_does_nothing(self):
        entity, gateway = _make_switch({})
        await entity.async_turn_on()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_turn_off_no_address_does_nothing(self):
        entity, gateway = _make_switch({})
        await entity.async_turn_off()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_turn_on_failed_telegram_does_not_update_state(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0"})
        gateway.async_send_telegram = AsyncMock(return_value=False)
        await entity.async_turn_on()
        assert entity._attr_is_on is False

    @pytest.mark.asyncio
    async def test_turn_off_failed_telegram_does_not_update_state(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0"})
        entity._attr_is_on = True
        gateway.async_send_telegram = AsyncMock(return_value=False)
        await entity.async_turn_off()
        assert entity._attr_is_on is True


# ── _is_rate_limited ──────────────────────────────────────────────────────────


class TestRateLimiting:
    def test_not_rate_limited_normally(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        assert entity._is_rate_limited() is False

    def test_rate_limited_after_5_commands(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        now = time.time()
        entity._command_times = [now - 0.1] * 5
        assert entity._is_rate_limited() is True

    @pytest.mark.asyncio
    async def test_turn_on_blocked_when_rate_limited(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0"})
        now = time.time()
        entity._command_times = [now - 0.1] * 5
        await entity.async_turn_on()
        gateway.async_send_telegram.assert_not_awaited()


# ── async_added_to_hass ───────────────────────────────────────────────────────


class TestAsyncAddedToHass:
    @pytest.mark.asyncio
    async def test_connected_reads_both_addresses(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        assert gateway.async_read_group_address.await_count == 2

    @pytest.mark.asyncio
    async def test_connected_reads_single_address(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0"})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        gateway.async_read_group_address.assert_awaited_once_with("1/0/0", is_initial=True)

    @pytest.mark.asyncio
    async def test_no_read_when_no_addresses(self):
        entity, gateway = _make_switch({})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        gateway.async_read_group_address.assert_not_awaited()


# ── async_will_remove_from_hass ───────────────────────────────────────────────


class TestAsyncWillRemoveFromHass:
    @pytest.mark.asyncio
    async def test_unregisters_all_listeners(self):
        entity, gateway = _make_switch({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        await entity.async_will_remove_from_hass()
        assert gateway.unregister_listener.call_count == 2

    @pytest.mark.asyncio
    async def test_no_unregister_when_no_listeners(self):
        entity, gateway = _make_switch({})
        await entity.async_will_remove_from_hass()
        gateway.unregister_listener.assert_not_called()


# ── extra_state_attributes ────────────────────────────────────────────────────


class TestExtraStateAttributes:
    def test_knx_address_on_included(self):
        entity, _ = _make_switch({"OnOff": "1/0/0"})
        attrs = entity.extra_state_attributes
        assert "knx_address_on" in attrs

    def test_knx_address_status_included(self):
        entity, _ = _make_switch({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        attrs = entity.extra_state_attributes
        assert "knx_address_status" in attrs

    def test_no_addresses_empty_attrs(self):
        entity, _ = _make_switch({})
        attrs = entity.extra_state_attributes
        assert "knx_address_on" not in attrs
        assert "knx_address_status" not in attrs
