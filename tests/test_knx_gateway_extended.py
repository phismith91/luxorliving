"""Extended tests for knx_gateway.py covering uncovered branches."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.knx_gateway import LuxorKNXGateway

# ── Fixture ───────────────────────────────────────────────────────────────────


def _gw(simulation_mode=True, connection_type="tunneling", host="192.168.1.100", port=3671):
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda f, *a: f(*a))
    return LuxorKNXGateway(
        hass=hass,
        host=host,
        port=port,
        username="admin",
        password="pass",
        connection_type=connection_type,
        simulation_mode=simulation_mode,
    )


# ── Initialization ────────────────────────────────────────────────────────────


class TestGatewayInit:
    def test_connected_false_on_init(self):
        gw = _gw()
        assert gw.connected is False

    def test_host_and_port_set(self):
        gw = _gw(host="10.0.0.1", port=1234)
        assert gw.host == "10.0.0.1"
        assert gw.port == 1234

    def test_simulation_mode_true(self):
        gw = _gw(simulation_mode=True)
        assert gw.simulation_mode is True

    def test_simulation_mode_false(self):
        gw = _gw(simulation_mode=False)
        assert gw.simulation_mode is False

    def test_routing_connection_type(self):
        from xknx.io import ConnectionType

        gw = _gw(connection_type="routing")
        assert gw._connection_type == ConnectionType.ROUTING

    def test_tunneling_connection_type(self):
        from xknx.io import ConnectionType

        gw = _gw(connection_type="tunneling")
        assert gw._connection_type == ConnectionType.TUNNELING

    def test_unknown_connection_type_defaults_routing(self):
        from xknx.io import ConnectionType

        gw = _gw(connection_type="unknown")
        assert gw._connection_type == ConnectionType.ROUTING

    def test_xknx_none_on_init(self):
        gw = _gw()
        assert gw._xknx is None
        assert gw.xknx is None

    def test_initial_read_pending_empty(self):
        gw = _gw()
        assert gw.pending_initial_reads == 0

    def test_discovered_sensors_empty(self):
        gw = _gw()
        assert gw.get_discovered_sensors() == {}


# ── async_setup simulation mode ───────────────────────────────────────────────


class TestAsyncSetupSimulation:
    @pytest.mark.asyncio
    async def test_setup_simulation_returns_true(self):
        gw = _gw(simulation_mode=True)
        result = await gw.async_setup()
        assert result is True

    @pytest.mark.asyncio
    async def test_setup_simulation_sets_connected(self):
        gw = _gw(simulation_mode=True)
        await gw.async_setup()
        assert gw.connected is True

    @pytest.mark.asyncio
    async def test_setup_simulation_no_xknx_created(self):
        gw = _gw(simulation_mode=True)
        await gw.async_setup()
        assert gw._xknx is None


# ── async_send_telegram simulation ───────────────────────────────────────────


class TestSendTelegramSimulation:
    @pytest.mark.asyncio
    async def test_send_binary_simulation(self):
        gw = _gw(simulation_mode=True)
        result = await gw.async_send_telegram("1/0/0", True, "binary")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_percent_simulation(self):
        gw = _gw(simulation_mode=True)
        result = await gw.async_send_telegram("1/0/1", 50, "percent")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_unknown_type_simulation(self):
        gw = _gw(simulation_mode=True)
        result = await gw.async_send_telegram("1/0/2", 42, "raw")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_not_connected_returns_false(self):
        gw = _gw(simulation_mode=False)
        # Not connected
        result = await gw.async_send_telegram("1/0/0", True, "binary")
        assert result is False


# ── async_send_telegram real mode ─────────────────────────────────────────────


class TestSendTelegramRealMode:
    def _connected_gw(self):
        gw = _gw(simulation_mode=False)
        gw._connected = True
        gw._xknx = MagicMock()
        gw._xknx.telegrams = AsyncMock()
        gw._xknx.telegrams.put = AsyncMock()
        return gw

    @pytest.mark.asyncio
    async def test_send_binary_true(self):
        gw = self._connected_gw()
        result = await gw.async_send_telegram("1/0/0", True, "binary")
        assert result is True
        gw._xknx.telegrams.put.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_binary_false(self):
        gw = self._connected_gw()
        result = await gw.async_send_telegram("1/0/0", False, "binary")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_percent(self):
        gw = self._connected_gw()
        result = await gw.async_send_telegram("1/0/1", 75, "percent")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_raw_bytes(self):
        gw = self._connected_gw()
        result = await gw.async_send_telegram("1/0/2", [0x0F], "raw")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_unknown_type_int(self):
        gw = self._connected_gw()
        result = await gw.async_send_telegram("1/0/3", 42, "unknown_type")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_exception_returns_false(self):
        gw = self._connected_gw()
        gw._xknx.telegrams.put = AsyncMock(side_effect=RuntimeError("KNX error"))
        result = await gw.async_send_telegram("1/0/0", True, "binary")
        assert result is False


# ── async_read_group_address ──────────────────────────────────────────────────


class TestReadGroupAddress:
    @pytest.mark.asyncio
    async def test_read_simulation_returns_true(self):
        gw = _gw(simulation_mode=True)
        result = await gw.async_read_group_address("1/0/0")
        assert result is True

    @pytest.mark.asyncio
    async def test_read_not_connected_returns_false(self):
        gw = _gw(simulation_mode=False)
        result = await gw.async_read_group_address("1/0/0")
        assert result is False

    @pytest.mark.asyncio
    async def test_read_connected_sends_telegram(self):
        gw = _gw(simulation_mode=False)
        gw._connected = True
        gw._xknx = MagicMock()
        gw._xknx.telegrams = AsyncMock()
        gw._xknx.telegrams.put = AsyncMock()
        result = await gw.async_read_group_address("1/0/0")
        assert result is True
        gw._xknx.telegrams.put.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_read_initial_adds_to_pending(self):
        gw = _gw(simulation_mode=False)
        gw._connected = True
        gw._xknx = MagicMock()
        gw._xknx.telegrams = AsyncMock()
        gw._xknx.telegrams.put = AsyncMock()
        await gw.async_read_group_address("1/0/0", is_initial=True)
        assert "1/0/0" in gw._initial_read_pending

    @pytest.mark.asyncio
    async def test_read_exception_returns_false(self):
        gw = _gw(simulation_mode=False)
        gw._connected = True
        gw._xknx = MagicMock()
        gw._xknx.telegrams = AsyncMock()
        gw._xknx.telegrams.put = AsyncMock(side_effect=RuntimeError("err"))
        result = await gw.async_read_group_address("1/0/0")
        assert result is False

    @pytest.mark.asyncio
    async def test_read_initial_exception_removes_from_pending(self):
        gw = _gw(simulation_mode=False)
        gw._connected = True
        gw._xknx = MagicMock()
        gw._xknx.telegrams = AsyncMock()
        gw._xknx.telegrams.put = AsyncMock(side_effect=RuntimeError("err"))
        gw._initial_read_pending.add("1/0/0")
        await gw.async_read_group_address("1/0/0", is_initial=True)
        assert "1/0/0" not in gw._initial_read_pending


# ── register_listener / unregister_listener ───────────────────────────────────


class TestListeners:
    def test_register_listener_string_address(self):
        gw = _gw()
        cb = MagicMock()
        gw.register_listener("1/0/0", cb)
        assert "1/0/0" in gw._listeners

    def test_register_listener_integer_address(self):
        gw = _gw()
        cb = MagicMock()
        gw.register_listener(2048, cb)  # 2048 = 1/0/0
        assert len(gw._listeners) >= 1

    def test_register_multiple_listeners_same_address(self):
        gw = _gw()
        cb1, cb2 = MagicMock(), MagicMock()
        gw.register_listener("1/0/0", cb1)
        gw.register_listener("1/0/0", cb2)
        assert len(gw._listeners["1/0/0"]) == 2

    def test_unregister_listener_removes_callback(self):
        gw = _gw()
        cb = MagicMock()
        gw.register_listener("1/0/0", cb)
        gw.unregister_listener("1/0/0", cb)
        assert cb not in gw._listeners.get("1/0/0", [])

    def test_unregister_nonexistent_listener_no_crash(self):
        gw = _gw()
        gw.unregister_listener("9/9/9", MagicMock())  # Must not raise

    def test_register_listener_invalid_address_uses_string(self):
        gw = _gw()
        cb = MagicMock()
        gw.register_listener("invalid_address", cb)
        assert "invalid_address" in gw._listeners


# ── Properties and state ───────────────────────────────────────────────────────


class TestProperties:
    def test_connected_property_false(self):
        gw = _gw()
        assert gw.connected is False

    def test_pending_initial_reads_zero(self):
        gw = _gw()
        assert gw.pending_initial_reads == 0

    def test_pending_initial_reads_after_add(self):
        gw = _gw()
        gw._initial_read_pending.add("1/0/0")
        gw._initial_read_pending.add("1/0/1")
        assert gw.pending_initial_reads == 2

    def test_xknx_property_none(self):
        gw = _gw()
        assert gw.xknx is None

    def test_set_group_address_labels(self):
        gw = _gw()
        gw.set_group_address_labels({"1/0/0": ["Light 1"]})
        assert gw._ga_label_map == {"1/0/0": ["Light 1"]}

    def test_set_individual_address_labels(self):
        gw = _gw()
        gw.set_individual_address_labels({"1.1.1": ["Device 1"]})
        assert gw._ia_label_map == {"1.1.1": ["Device 1"]}

    def test_set_known_addresses(self):
        gw = _gw()
        gw.set_known_addresses({"1/0/0", "1/0/1"})
        assert "1/0/0" in gw._known_addresses

    def test_set_sensor_types(self):
        gw = _gw()
        gw.set_sensor_types({"5/0/3": "illuminance"})
        assert gw._ga_sensor_type_map == {"5/0/3": "illuminance"}


# ── async_disconnect ──────────────────────────────────────────────────────────


class TestAsyncDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_simulation_does_not_raise(self):
        gw = _gw(simulation_mode=True)
        await gw.async_setup()
        await gw.async_disconnect()
        assert gw.connected is False

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected_is_noop(self):
        gw = _gw(simulation_mode=False)
        await gw.async_disconnect()  # must not raise


# ── _detect_sensor_type ───────────────────────────────────────────────────────


class TestDetectSensorType:
    def test_temperature_range(self):
        gw = _gw()
        assert gw._detect_sensor_type(21.5) == "temperature"

    def test_temperature_negative(self):
        gw = _gw()
        assert gw._detect_sensor_type(-10.0) == "temperature"

    def test_humidity_range(self):
        gw = _gw()
        assert gw._detect_sensor_type(65.0) == "humidity"

    def test_illuminance_large_value(self):
        gw = _gw()
        assert gw._detect_sensor_type(500.0) == "illuminance"

    def test_pressure_range(self):
        gw = _gw()
        assert gw._detect_sensor_type(101325.0) == "pressure"

    def test_generic_fallback(self):
        gw = _gw()
        # Value outside all known ranges
        assert gw._detect_sensor_type(-200.0) == "generic_sensor"


# ── Discovery ─────────────────────────────────────────────────────────────────


class TestDiscovery:
    def test_get_discovered_sensors_empty(self):
        gw = _gw()
        assert gw.get_discovered_sensors() == {}

    def test_load_discovered_sensors(self):
        gw = _gw()
        sensors = {"5/0/1": {"type": "temperature", "last_value": 21.5}}
        gw.load_discovered_sensors(sensors)
        result = gw.get_discovered_sensors()
        assert "5/0/1" in result

    def test_load_discovered_sensors_does_not_mutate_original(self):
        gw = _gw()
        sensors = {"5/0/1": {"type": "temperature"}}
        gw.load_discovered_sensors(sensors)
        sensors["5/0/2"] = {"type": "humidity"}
        assert "5/0/2" not in gw.get_discovered_sensors()

    def test_register_discovery_callback(self):
        gw = _gw()
        cb = MagicMock()
        gw.register_discovery_callback(cb)
        assert cb in gw._discovery_callbacks

    @pytest.mark.asyncio
    async def test_process_incoming_value_binary(self):
        gw = _gw(simulation_mode=True)
        cb = MagicMock()
        gw.register_listener("1/0/0", cb)
        await gw.process_incoming_value("1/0/0", True, "binary")
        cb.assert_called_once_with("1/0/0", True)

    @pytest.mark.asyncio
    async def test_process_incoming_value_percent(self):
        gw = _gw(simulation_mode=True)
        cb = MagicMock()
        gw.register_listener("1/0/1", cb)
        await gw.process_incoming_value("1/0/1", 75, "percent")
        cb.assert_called_once_with("1/0/1", 75)

    @pytest.mark.asyncio
    async def test_process_incoming_value_no_listener(self):
        gw = _gw(simulation_mode=True)
        # Must not raise when no listener registered
        await gw.process_incoming_value("9/9/9", True, "binary")

    @pytest.mark.asyncio
    async def test_process_incoming_value_two_byte_float(self):
        gw = _gw(simulation_mode=True)
        cb = MagicMock()
        gw.register_listener("5/0/1", cb)
        await gw.process_incoming_value("5/0/1", (0x0C, 0x04))
        cb.assert_called_once()


# ── Reconnect watchdog ────────────────────────────────────────────────────────


class TestReconnectWatchdog:
    """5 DISCONNECTED events in window → schedule _async_forced_refresh."""

    def test_five_disconnects_schedule_forced_refresh(self):
        from xknx.core import XknxConnectionState

        gw = _gw(simulation_mode=False)
        gw._rest_client = AsyncMock()
        gw._setup_complete = True

        for _ in range(5):
            gw._on_connection_state_changed(XknxConnectionState.DISCONNECTED)

        gw.hass.async_create_task.assert_called()

    def test_four_disconnects_no_forced_refresh(self):
        from xknx.core import XknxConnectionState

        gw = _gw(simulation_mode=False)
        gw._rest_client = AsyncMock()
        gw._setup_complete = True

        for _ in range(4):
            gw._on_connection_state_changed(XknxConnectionState.DISCONNECTED)

        gw.hass.async_create_task.assert_not_called()

    def test_connected_resets_failure_counter(self):
        from xknx.core import XknxConnectionState

        gw = _gw(simulation_mode=False)
        gw._rest_client = AsyncMock()
        gw._setup_complete = True

        for _ in range(4):
            gw._on_connection_state_changed(XknxConnectionState.DISCONNECTED)
        gw._on_connection_state_changed(XknxConnectionState.CONNECTED)
        gw.hass.async_create_task.reset_mock()

        for _ in range(4):
            gw._on_connection_state_changed(XknxConnectionState.DISCONNECTED)

        gw.hass.async_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_forced_refresh_calls_rest_cycle(self):
        gw = _gw(simulation_mode=False)
        rest = AsyncMock()
        gw._rest_client = rest

        await gw._async_forced_refresh()

        rest.logout.assert_called_once()
        rest.login.assert_called_once_with("admin", "pass")
        rest.disable_tunneling.assert_called_once()
        rest.enable_tunneling.assert_called_once()


# ── Timestamp guard ───────────────────────────────────────────────────────────


class TestTimestampGuard:
    """_async_on_reconnect skips re-auth if a REST refresh happened recently."""

    @pytest.mark.asyncio
    async def test_skips_reconnect_if_recent_refresh(self):
        import time

        gw = _gw(simulation_mode=False)
        rest = AsyncMock()
        gw._rest_client = rest
        gw._last_refresh_at = time.monotonic()  # just refreshed

        await gw._async_on_reconnect()

        rest.logout.assert_not_called()

    @pytest.mark.asyncio
    async def test_proceeds_if_refresh_was_old(self):
        import time

        gw = _gw(simulation_mode=False)
        rest = AsyncMock()
        gw._rest_client = rest
        gw._last_refresh_at = time.monotonic() - 60  # 60 s ago

        await gw._async_on_reconnect()

        rest.logout.assert_called_once()

    @pytest.mark.asyncio
    async def test_forced_refresh_updates_timestamp(self):
        import time

        gw = _gw(simulation_mode=False)
        rest = AsyncMock()
        gw._rest_client = rest
        gw._last_refresh_at = 0.0

        before = time.monotonic()
        await gw._async_forced_refresh()

        assert gw._last_refresh_at >= before


# ── Not-connected rate-limit ──────────────────────────────────────────────────


class TestNotConnectedRateLimit:
    """'Cannot read - not connected' logs ERROR once per interval, then DEBUG."""

    @pytest.mark.asyncio
    async def test_first_call_logs_error(self, caplog):
        import logging

        gw = _gw(simulation_mode=False)
        gw._connected = False

        with caplog.at_level(logging.DEBUG, logger="custom_components.luxor_living.knx_gateway"):
            await gw.async_read_group_address("1/2/3")

        errors = [
            r
            for r in caplog.records
            if r.levelno == logging.ERROR and "not connected" in r.getMessage()
        ]
        assert errors

    @pytest.mark.asyncio
    async def test_second_call_within_interval_logs_debug(self, caplog):
        import logging

        gw = _gw(simulation_mode=False)
        gw._connected = False

        with caplog.at_level(logging.DEBUG, logger="custom_components.luxor_living.knx_gateway"):
            await gw.async_read_group_address("1/2/3")
            await gw.async_read_group_address("1/2/3")

        not_connected = [r for r in caplog.records if "not connected" in r.getMessage()]
        assert len(not_connected) == 2
        assert not_connected[1].levelno == logging.DEBUG

    @pytest.mark.asyncio
    async def test_after_interval_logs_error_again(self, caplog):
        import logging
        import time

        gw = _gw(simulation_mode=False)
        gw._connected = False
        gw._last_not_connected_log_at = time.monotonic() - 61

        with caplog.at_level(logging.DEBUG, logger="custom_components.luxor_living.knx_gateway"):
            await gw.async_read_group_address("1/2/3")

        errors = [
            r
            for r in caplog.records
            if r.levelno == logging.ERROR and "not connected" in r.getMessage()
        ]
        assert errors


# ── Slot saturation diagnostic ─────────────────────────────────────────────────


class TestLogSlotStatus:
    """_log_slot_status escalates to WARNING only when slots are saturated."""

    @pytest.mark.asyncio
    async def test_saturated_logs_warning(self, caplog):
        import logging

        gw = _gw(simulation_mode=False)
        gw._rest_client = AsyncMock()
        gw._rest_client.get_tunneling_status.return_value = {
            "connectedClients": 4,
            "maxSlots": 4,
        }

        with caplog.at_level(logging.DEBUG, logger="custom_components.luxor_living.knx_gateway"):
            await gw._log_slot_status("test")

        matches = [r for r in caplog.records if "slots before flush" in r.getMessage()]
        assert matches
        assert matches[0].levelno == logging.WARNING

    @pytest.mark.asyncio
    async def test_healthy_logs_debug(self, caplog):
        import logging

        gw = _gw(simulation_mode=False)
        gw._rest_client = AsyncMock()
        gw._rest_client.get_tunneling_status.return_value = {
            "connectedClients": 1,
            "maxSlots": 4,
        }

        with caplog.at_level(logging.DEBUG, logger="custom_components.luxor_living.knx_gateway"):
            await gw._log_slot_status("test")

        matches = [r for r in caplog.records if "slots before flush" in r.getMessage()]
        assert matches
        assert matches[0].levelno == logging.DEBUG

    @pytest.mark.asyncio
    async def test_rest_error_swallowed(self):
        gw = _gw(simulation_mode=False)
        gw._rest_client = AsyncMock()
        gw._rest_client.get_tunneling_status.side_effect = RuntimeError("boom")

        await gw._log_slot_status("test")  # must not raise
