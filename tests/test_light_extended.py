"""Extended tests for light.py covering uncovered branches."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.luxor_living.light import (
    LuxorLivingDimmableLight,
    LuxorLivingLight,
    _create_light_entity_sync,
)


def _make_mapped_entity(entity_type="light", datapoints=None):
    me = MagicMock()
    me.unique_id = f"test_{entity_type}"
    me.name = "Test Light"
    me.device_name = "Test Device"
    me.device_id = "dev_001"
    me.entity_type = entity_type
    me.parameters = {}
    me.attributes = {}
    me.datapoints = datapoints or {}
    return me


def _make_light(datapoints=None, connected=True):
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

    mapped = _make_mapped_entity("light", datapoints)
    entity = LuxorLivingLight(coordinator, entry, mapped, gateway)
    entity.async_write_ha_state = MagicMock()
    return entity, gateway


def _make_dimmable(datapoints=None, connected=True):
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

    mapped = _make_mapped_entity("dimmable_light", datapoints)
    entity = LuxorLivingDimmableLight(coordinator, entry, mapped, gateway)
    entity.async_write_ha_state = MagicMock()
    return entity, gateway


# ── _create_light_entity_sync ─────────────────────────────────────────────────


class TestCreateLightEntitySync:
    def test_creates_dimmable_light(self):
        coordinator, gateway = MagicMock(), MagicMock()
        gateway.register_listener = MagicMock()
        entry = MagicMock()
        entry.runtime_data = MagicMock()
        entry.runtime_data.knx_gateway = gateway
        mapped = _make_mapped_entity("dimmable_light", {})
        entity = _create_light_entity_sync(coordinator, entry, mapped, gateway)
        assert isinstance(entity, LuxorLivingDimmableLight)

    def test_creates_plain_light(self):
        coordinator, gateway = MagicMock(), MagicMock()
        gateway.register_listener = MagicMock()
        entry = MagicMock()
        entry.runtime_data = MagicMock()
        entry.runtime_data.knx_gateway = gateway
        mapped = _make_mapped_entity("light", {})
        entity = _create_light_entity_sync(coordinator, entry, mapped, gateway)
        assert isinstance(entity, LuxorLivingLight)
        assert not isinstance(entity, LuxorLivingDimmableLight)


# ── LuxorLivingLight.__init__ ─────────────────────────────────────────────────


class TestLightInit:
    def test_address_on_from_onoff(self):
        entity, _ = _make_light({"OnOff": "1/0/0"})
        assert entity._address_on == "1/0/0"

    def test_address_on_from_schalten(self):
        entity, _ = _make_light({"SchaltenOnOff": "1/0/1"})
        assert entity._address_on == "1/0/1"

    def test_address_status_from_status_onoff(self):
        entity, _ = _make_light({"status@OnOff": "1/0/2"})
        assert entity._address_status == "1/0/2"

    def test_registers_status_listener(self):
        entity, gateway = _make_light({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        addresses = [call[0][0] for call in gateway.register_listener.call_args_list]
        assert "1/0/2" in addresses

    def test_registers_control_listener_when_different(self):
        entity, gateway = _make_light({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        addresses = [call[0][0] for call in gateway.register_listener.call_args_list]
        assert "1/0/0" in addresses

    def test_no_duplicate_listener_same_address(self):
        entity, gateway = _make_light({"OnOff": "1/0/0", "status@OnOff": "1/0/0"})
        assert gateway.register_listener.call_count == 1

    def test_initial_state_is_off(self):
        entity, _ = _make_light({"OnOff": "1/0/0"})
        assert entity._attr_is_on is False


# ── _handle_knx_update ────────────────────────────────────────────────────────


class TestHandleKnxUpdate:
    def test_updates_state_on_control_address(self):
        entity, _ = _make_light({"OnOff": "1/0/0"})
        entity._handle_knx_update("1/0/0", True)
        assert entity._attr_is_on is True
        entity.async_write_ha_state.assert_called_once()

    def test_updates_off_state(self):
        entity, _ = _make_light({"OnOff": "1/0/0"})
        entity._attr_is_on = True
        entity._handle_knx_update("1/0/0", False)
        assert entity._attr_is_on is False

    def test_updates_on_status_address(self):
        entity, _ = _make_light({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        entity._handle_knx_update("1/0/2", True)
        assert entity._attr_is_on is True

    def test_ignores_unknown_address(self):
        entity, _ = _make_light({"OnOff": "1/0/0"})
        entity._handle_knx_update("9/9/9", True)
        entity.async_write_ha_state.assert_not_called()


# ── async_turn_on / async_turn_off ────────────────────────────────────────────


class TestTurnOnOff:
    @pytest.mark.asyncio
    async def test_turn_on_sends_telegram(self):
        entity, gateway = _make_light({"OnOff": "1/0/0"})
        await entity.async_turn_on()
        gateway.async_send_telegram.assert_awaited_once_with("1/0/0", True, "binary")

    @pytest.mark.asyncio
    async def test_turn_on_sets_state_true(self):
        entity, _ = _make_light({"OnOff": "1/0/0"})
        await entity.async_turn_on()
        assert entity._attr_is_on is True

    @pytest.mark.asyncio
    async def test_turn_off_sends_telegram(self):
        entity, gateway = _make_light({"OnOff": "1/0/0"})
        await entity.async_turn_off()
        gateway.async_send_telegram.assert_awaited_once_with("1/0/0", False, "binary")

    @pytest.mark.asyncio
    async def test_turn_off_sets_state_false(self):
        entity, _ = _make_light({"OnOff": "1/0/0"})
        entity._attr_is_on = True
        await entity.async_turn_off()
        assert entity._attr_is_on is False

    @pytest.mark.asyncio
    async def test_turn_on_no_address_does_nothing(self):
        entity, gateway = _make_light({})
        await entity.async_turn_on()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_turn_off_no_address_does_nothing(self):
        entity, gateway = _make_light({})
        await entity.async_turn_off()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_turn_on_failed_does_not_update_state(self):
        entity, gateway = _make_light({"OnOff": "1/0/0"})
        gateway.async_send_telegram = AsyncMock(return_value=False)
        await entity.async_turn_on()
        assert entity._attr_is_on is False

    @pytest.mark.asyncio
    async def test_turn_off_failed_does_not_update_state(self):
        entity, gateway = _make_light({"OnOff": "1/0/0"})
        entity._attr_is_on = True
        gateway.async_send_telegram = AsyncMock(return_value=False)
        await entity.async_turn_off()
        assert entity._attr_is_on is True


# ── _is_rate_limited ──────────────────────────────────────────────────────────


class TestRateLimiting:
    def test_not_rate_limited_normally(self):
        entity, _ = _make_light({"OnOff": "1/0/0"})
        assert entity._is_rate_limited() is False

    def test_rate_limited_after_5_commands(self):
        entity, _ = _make_light({"OnOff": "1/0/0"})
        entity._command_times = [time.time() - 0.1] * 5
        assert entity._is_rate_limited() is True

    @pytest.mark.asyncio
    async def test_turn_on_blocked_when_rate_limited(self):
        entity, gateway = _make_light({"OnOff": "1/0/0"})
        entity._command_times = [time.time() - 0.1] * 5
        await entity.async_turn_on()
        gateway.async_send_telegram.assert_not_awaited()


# ── async_added_to_hass ───────────────────────────────────────────────────────


class TestAsyncAddedToHass:
    @pytest.mark.asyncio
    async def test_connected_reads_both_addresses(self):
        entity, gateway = _make_light({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        assert gateway.async_read_group_address.await_count == 2

    @pytest.mark.asyncio
    async def test_connected_reads_single_address(self):
        entity, gateway = _make_light({"OnOff": "1/0/0"})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        gateway.async_read_group_address.assert_awaited_once_with("1/0/0", is_initial=True)

    @pytest.mark.asyncio
    async def test_no_read_when_no_addresses(self):
        entity, gateway = _make_light({})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        gateway.async_read_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_not_connected_skips_initial_read(self):
        entity, gateway = _make_light({"OnOff": "1/0/0"}, connected=False)
        entity.async_on_remove = MagicMock()
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await entity.async_added_to_hass()
        gateway.async_read_group_address.assert_not_awaited()


# ── async_will_remove_from_hass ───────────────────────────────────────────────


class TestAsyncWillRemoveFromHass:
    @pytest.mark.asyncio
    async def test_unregisters_all_listeners(self):
        entity, gateway = _make_light({"OnOff": "1/0/0", "status@OnOff": "1/0/2"})
        await entity.async_will_remove_from_hass()
        assert gateway.unregister_listener.call_count == 2

    @pytest.mark.asyncio
    async def test_no_unregister_when_no_listeners(self):
        entity, gateway = _make_light({})
        await entity.async_will_remove_from_hass()
        gateway.unregister_listener.assert_not_called()


# ── LuxorLivingDimmableLight ──────────────────────────────────────────────────


class TestDimmableLight:
    def test_registers_dim_listener(self):
        entity, gateway = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1", "Status%": "1/0/3"})
        addresses = [call[0][0] for call in gateway.register_listener.call_args_list]
        assert "1/0/1" in addresses

    def test_registers_dim_status_listener(self):
        entity, gateway = _make_dimmable({"OnOff": "1/0/0", "Status%": "1/0/3"})
        addresses = [call[0][0] for call in gateway.register_listener.call_args_list]
        assert "1/0/3" in addresses

    def test_initial_brightness_is_255(self):
        entity, _ = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        assert entity._attr_brightness == 255

    @pytest.mark.asyncio
    async def test_turn_on_with_dimmer_sends_percent(self):
        entity, gateway = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        from homeassistant.components.light import ATTR_BRIGHTNESS

        await entity.async_turn_on(**{ATTR_BRIGHTNESS: 128})
        gateway.async_send_telegram.assert_awaited_once()
        args = gateway.async_send_telegram.call_args[0]
        assert args[2] == "percent"

    @pytest.mark.asyncio
    async def test_turn_on_without_dimmer_falls_back_to_onoff(self):
        entity, gateway = _make_dimmable({"OnOff": "1/0/0"})
        await entity.async_turn_on()
        gateway.async_send_telegram.assert_awaited_once_with("1/0/0", True, "binary")

    @pytest.mark.asyncio
    async def test_turn_on_dim_success_updates_brightness(self):
        entity, _ = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        from homeassistant.components.light import ATTR_BRIGHTNESS

        await entity.async_turn_on(**{ATTR_BRIGHTNESS: 128})
        assert entity._attr_brightness == 128
        assert entity._attr_is_on is True

    @pytest.mark.asyncio
    async def test_async_added_reads_dim_addresses(self):
        entity, gateway = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        calls = [c[0][0] for c in gateway.async_read_group_address.await_args_list]
        assert "1/0/1" in calls

    @pytest.mark.asyncio
    async def test_async_added_reads_dim_status(self):
        entity, gateway = _make_dimmable({"OnOff": "1/0/0", "Status%": "1/0/3"})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        calls = [c[0][0] for c in gateway.async_read_group_address.await_args_list]
        assert "1/0/3" in calls

    def test_handle_brightness_update_valid(self):
        entity, _ = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        entity._handle_brightness_update("1/0/1", 50)
        expected = int(50 * 255 / 100)
        assert entity._attr_brightness == expected
        assert entity._attr_is_on is True

    def test_handle_brightness_update_zero_turns_off(self):
        entity, _ = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        entity._attr_is_on = True
        entity._handle_brightness_update("1/0/1", 0)
        assert entity._attr_is_on is False

    def test_handle_brightness_ignores_unknown_address(self):
        entity, _ = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        entity._handle_brightness_update("9/9/9", 50)
        entity.async_write_ha_state.assert_not_called()

    def test_extra_state_attributes_includes_dim_address(self):
        entity, _ = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        attrs = entity.extra_state_attributes
        assert "knx_address_dim" in attrs

    def test_extra_state_attributes_includes_on_address(self):
        entity, _ = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        attrs = entity.extra_state_attributes
        assert "knx_address_on" in attrs

    def test_extra_state_attributes_no_dim_when_missing(self):
        entity, _ = _make_dimmable({"OnOff": "1/0/0"})
        attrs = entity.extra_state_attributes
        assert "knx_address_dim" not in attrs

    @pytest.mark.asyncio
    async def test_will_remove_unregisters_dim_listener(self):
        entity, gateway = _make_dimmable({"OnOff": "1/0/0", "Dimmen%": "1/0/1"})
        await entity.async_will_remove_from_hass()
        addresses = [call[0][0] for call in gateway.unregister_listener.call_args_list]
        assert "1/0/1" in addresses

    @pytest.mark.asyncio
    async def test_will_remove_unregisters_dim_status_listener(self):
        entity, gateway = _make_dimmable({"OnOff": "1/0/0", "Status%": "1/0/3"})
        await entity.async_will_remove_from_hass()
        addresses = [call[0][0] for call in gateway.unregister_listener.call_args_list]
        assert "1/0/3" in addresses
