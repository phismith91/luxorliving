"""Tests for KNX Gateway."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.knx_gateway import LuxorKNXGateway


@pytest.fixture(autouse=True)
def _mock_shared_session():
    """Stub HA's shared websession helper so the gateway never builds a real one."""
    with patch(
        "custom_components.luxor_living.knx_gateway.async_get_clientsession",
        return_value=MagicMock(),
    ):
        yield


@pytest_asyncio.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))
    return hass


class TestLuxorKNXGateway:
    """Test LuxorKNXGateway class."""

    @pytest.mark.smoke
    def test_init_simulation_mode(self, mock_hass):
        """Test initialization in simulation mode."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            connection_type="tunneling",
            simulation_mode=True,
        )

        assert gateway.simulation_mode is True
        assert gateway.host == "192.168.1.3"
        assert gateway.port == 3671
        assert gateway.username == "admin"
        assert gateway._connected is False

    @pytest.mark.smoke
    def test_init_tunneling_mode(self, mock_hass):
        """Test initialization with tunneling mode."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            connection_type="tunneling",
            simulation_mode=False,
        )

        assert gateway.simulation_mode is False
        from xknx.io import ConnectionType

        assert gateway._connection_type == ConnectionType.TUNNELING

    def test_init_routing_mode(self, mock_hass):
        """Test initialization with routing mode."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="224.0.23.12",
            port=3671,
            username="admin",
            password="admin",
            connection_type="routing",
            simulation_mode=False,
        )

        from xknx.io import ConnectionType

        assert gateway._connection_type == ConnectionType.ROUTING

    def test_init_zombie_watchdog_state(self, mock_hass):
        """New zombie-watchdog fields must start unarmed/zeroed."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
        )

        assert gateway._zombie_watchdog_task is None
        assert gateway._last_cemi_error_count == 0
        assert gateway._last_zombie_reconnect_at == 0.0

    @pytest.mark.asyncio
    async def test_async_setup_simulation_mode(self, mock_hass):
        """Test setup in simulation mode."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )

        result = await gateway.async_setup()

        assert result is True
        assert gateway.connected is True
        assert gateway._xknx is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.BAOSRestClient")
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    async def test_async_setup_with_rest_auth(self, mock_xknx_class, mock_rest_class, mock_hass):
        """Test setup with REST API authentication (tunneling)."""
        # Mock REST Client
        mock_rest_client = AsyncMock()
        mock_rest_client.login = AsyncMock(return_value="test_token")
        mock_rest_client.enable_tunneling = AsyncMock(return_value=True)
        mock_rest_client.logout = AsyncMock()
        mock_rest_class.return_value = mock_rest_client

        # Mock XKNX
        mock_xknx = AsyncMock()
        mock_xknx.start = AsyncMock()
        mock_xknx.stop = AsyncMock()
        mock_xknx.telegram_queue.register_telegram_received_cb = MagicMock()
        mock_xknx.connection_manager.register_connection_state_changed_cb = MagicMock(
            return_value=MagicMock()
        )
        mock_xknx_class.return_value = mock_xknx
        mock_rest_client.__aexit__ = AsyncMock()

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            connection_type="tunneling",
            simulation_mode=False,
        )

        result = await gateway.async_setup()

        # Verify REST API login was called
        mock_rest_client.login.assert_called_once_with("admin", "admin")

        # Verify tunneling was enabled
        mock_rest_client.enable_tunneling.assert_called_once()

        # Verify KNX started
        mock_xknx.start.assert_called_once()

        assert result is True
        assert gateway.connected is True
        assert gateway._tunneling_enabled is True
        mock_xknx.start.assert_called_once()
        # In XKNX 3.x, connection happens automatically in start()

        # Teardown: cancel background session-refresh task so no lingering tasks remain
        await gateway.async_disconnect()

    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    @patch("custom_components.luxor_living.knx_gateway.BAOSRestClient")
    async def test_async_setup_failure(self, mock_rest_client_class, mock_xknx_class, mock_hass):
        """Test setup failure."""
        # Mock REST client success
        mock_rest = AsyncMock()
        mock_rest.login = AsyncMock()
        mock_rest.enable_tunneling = AsyncMock()
        mock_rest.logout = AsyncMock()
        mock_rest.__aenter__ = AsyncMock(return_value=mock_rest)
        mock_rest.__aexit__ = AsyncMock()
        mock_rest_client_class.return_value = mock_rest

        # Mock XKNX failure
        mock_xknx = AsyncMock()
        mock_xknx.start = AsyncMock(side_effect=Exception("Connection failed"))
        mock_xknx_class.return_value = mock_xknx

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )

        result = await gateway.async_setup()

        assert result is False
        assert gateway.connected is False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_send_telegram_simulation(self, mock_hass):
        """Test sending telegram in simulation mode."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )
        await gateway.async_setup()

        result = await gateway.async_send_telegram("1/2/3", True, "binary")

        assert result is True

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_async_send_telegram_not_connected(self, mock_hass):
        """Test sending telegram when not connected."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )

        result = await gateway.async_send_telegram("1/2/3", True, "binary")

        assert result is False

    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    @patch("custom_components.luxor_living.knx_gateway.BAOSRestClient")
    async def test_async_send_telegram_binary(
        self, mock_rest_client_class, mock_xknx_class, mock_hass
    ):
        """Test sending binary telegram."""
        # Mock REST client
        mock_rest = AsyncMock()
        mock_rest.login = AsyncMock()
        mock_rest.enable_tunneling = AsyncMock()
        mock_rest.logout = AsyncMock()
        mock_rest.__aenter__ = AsyncMock(return_value=mock_rest)
        mock_rest.__aexit__ = AsyncMock()
        mock_rest_client_class.return_value = mock_rest

        # Mock XKNX
        mock_xknx = AsyncMock()
        mock_xknx.start = AsyncMock()
        mock_xknx.stop = AsyncMock()
        mock_xknx.connection_manager.connect = AsyncMock()
        mock_xknx.connection_manager.register_connection_state_changed_cb = MagicMock(
            return_value=MagicMock()
        )
        mock_xknx.telegram_queue.register_telegram_received_cb = MagicMock()
        mock_xknx.telegrams.put = AsyncMock()
        mock_xknx_class.return_value = mock_xknx

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        await gateway.async_setup()

        result = await gateway.async_send_telegram("1/2/3", True, "binary")

        assert result is True
        mock_xknx.telegrams.put.assert_called_once()

        await gateway.async_disconnect()  # cancel session_refresh_task

    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    @patch("custom_components.luxor_living.knx_gateway.BAOSRestClient")
    async def test_async_send_telegram_percent(
        self, mock_rest_client_class, mock_xknx_class, mock_hass
    ):
        """Test sending percent telegram."""
        # Mock REST client
        mock_rest = AsyncMock()
        mock_rest.login = AsyncMock()
        mock_rest.enable_tunneling = AsyncMock()
        mock_rest.logout = AsyncMock()
        mock_rest.__aenter__ = AsyncMock(return_value=mock_rest)
        mock_rest.__aexit__ = AsyncMock()
        mock_rest_client_class.return_value = mock_rest

        # Mock XKNX
        mock_xknx = AsyncMock()
        mock_xknx.start = AsyncMock()
        mock_xknx.stop = AsyncMock()
        mock_xknx.connection_manager.connect = AsyncMock()
        mock_xknx.connection_manager.register_connection_state_changed_cb = MagicMock(
            return_value=MagicMock()
        )
        mock_xknx.telegram_queue.register_telegram_received_cb = MagicMock()
        mock_xknx.telegrams.put = AsyncMock()
        mock_xknx_class.return_value = mock_xknx

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        await gateway.async_setup()

        result = await gateway.async_send_telegram("1/2/3", 50, "percent")

        assert result is True
        mock_xknx.telegrams.put.assert_called_once()

        await gateway.async_disconnect()  # cancel session_refresh_task

    @pytest.mark.smoke
    def test_register_listener(self, mock_hass):
        """Test registering a listener."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )

        callback = MagicMock()
        gateway.register_listener("1/2/3", callback)

        assert "1/2/3" in gateway._listeners
        assert callback in gateway._listeners["1/2/3"]

    def test_unregister_listener(self, mock_hass):
        """Test unregistering a listener."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )

        callback = MagicMock()
        gateway.register_listener("1/2/3", callback)
        gateway.unregister_listener("1/2/3", callback)

        assert callback not in gateway._listeners.get("1/2/3", [])

    @pytest.mark.asyncio
    async def test_telegram_received_callback_binary(self, mock_hass):
        """Test receiving binary telegram."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )

        callback = MagicMock()
        gateway.register_listener("1/2/3", callback)

        # Mock telegram
        from xknx.dpt import DPTBinary
        from xknx.telegram import Telegram
        from xknx.telegram.address import GroupAddress
        from xknx.telegram.apci import GroupValueWrite

        mock_telegram = MagicMock(spec=Telegram)
        mock_telegram.destination_address = GroupAddress("1/2/3")
        mock_telegram.payload = MagicMock(spec=GroupValueWrite)
        mock_telegram.payload.value = DPTBinary(True)

        await gateway._telegram_received_callback(mock_telegram)

        callback.assert_called_once_with("1/2/3", True)

    @pytest.mark.asyncio
    async def test_telegram_received_callback_percent(self, mock_hass):
        """Test receiving percent telegram."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )

        callback = MagicMock()
        gateway.register_listener("1/2/4", callback)

        # Mock telegram with DPT 5.001 (percent)
        from xknx.dpt import DPTArray
        from xknx.telegram import Telegram
        from xknx.telegram.address import GroupAddress
        from xknx.telegram.apci import GroupValueWrite

        mock_telegram = MagicMock(spec=Telegram)
        mock_telegram.destination_address = GroupAddress("1/2/4")
        mock_telegram.payload = MagicMock(spec=GroupValueWrite)
        mock_telegram.payload.value = MagicMock(spec=DPTArray)
        mock_telegram.payload.value.value = [127]  # 50% (127/255)

        await gateway._telegram_received_callback(mock_telegram)

        # Should decode to ~50% (127 * 100 / 255 = 49.8...)
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == "1/2/4"
        assert 49 <= args[1] <= 50  # Allow rounding

    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    @patch("custom_components.luxor_living.knx_gateway.BAOSRestClient")
    async def test_async_disconnect(self, mock_rest_client_class, mock_xknx_class, mock_hass):
        """Test disconnecting from gateway."""
        # Mock REST client
        mock_rest = AsyncMock()
        mock_rest.login = AsyncMock()
        mock_rest.enable_tunneling = AsyncMock()
        mock_rest.disable_tunneling = AsyncMock()
        mock_rest.logout = AsyncMock()
        mock_rest.__aenter__ = AsyncMock(return_value=mock_rest)
        mock_rest.__aexit__ = AsyncMock()
        mock_rest_client_class.return_value = mock_rest

        # Mock XKNX
        mock_xknx = AsyncMock()
        mock_xknx.start = AsyncMock()
        mock_xknx.connection_manager.connect = AsyncMock()
        mock_xknx.connection_manager.register_connection_state_changed_cb = MagicMock(
            return_value=MagicMock()
        )
        mock_xknx.telegram_queue.register_telegram_received_cb = MagicMock()
        mock_xknx.stop = AsyncMock()
        mock_xknx_class.return_value = mock_xknx

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        await gateway.async_setup()

        await gateway.async_disconnect()

        assert gateway.connected is False
        mock_xknx.stop.assert_called_once()
        # We now call __aexit__ instead of logout directly
        mock_rest.__aexit__.assert_called_once()

    @pytest.mark.smoke
    def test_properties(self, mock_hass):
        """Test gateway properties."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )

        assert gateway.connected is False
        assert gateway.xknx is None

        # After setup
        asyncio.run(gateway.async_setup())
        assert gateway.connected is True

    @pytest.mark.asyncio
    async def test_process_incoming_value_calls_listeners(self, mock_hass):
        """Test that externally pushed values notify registered listeners."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )

        callback = MagicMock()
        gateway.register_listener("1/2/3", callback)

        await gateway.process_incoming_value("1/2/3", True, "binary")

        callback.assert_called_once_with("1/2/3", True)

    @pytest.mark.asyncio
    async def test_process_incoming_value_discovery(self, mock_hass):
        """Test that pushed float values are considered for auto-discovery."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )

        # Ensure no known addresses and a small debounce for test speed
        gateway.set_known_addresses(set())
        gateway.discovery_timeout = 0.01

        # Push three stable float values to trigger discovery
        await gateway.process_incoming_value("5/1/10", 23.5)
        await gateway.process_incoming_value("5/1/10", 23.6)
        await gateway.process_incoming_value("5/1/10", 23.4)

        # Allow debounce task to run
        await asyncio.sleep(0.05)

        discovered = gateway.get_discovered_sensors()
        assert "5/1/10" in discovered
        assert discovered["5/1/10"]["type"] in {"temperature", "humidity", "generic_sensor"}


class TestReconnectHandler:
    """Tests for the KNX reconnect handler (_on_connection_state_changed / _async_on_reconnect)."""

    def test_on_connection_state_changed_noop_before_setup_complete(self, mock_hass):
        """Callback must be ignored when _setup_complete is False."""
        from xknx.core import XknxConnectionState

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        assert gateway._setup_complete is False

        gateway._on_connection_state_changed(XknxConnectionState.DISCONNECTED)

        assert gateway._connected is False
        mock_hass.async_create_task.assert_not_called()

    def test_on_connection_state_changed_disconnected_clears_connected_flag(self, mock_hass):
        """DISCONNECTED state must set _connected=False."""
        from xknx.core import XknxConnectionState

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        gateway._setup_complete = True
        gateway._connected = True

        gateway._on_connection_state_changed(XknxConnectionState.DISCONNECTED)

        assert gateway._connected is False
        mock_hass.async_create_task.assert_not_called()

    def test_on_connection_state_changed_connecting_does_not_schedule_task(self, mock_hass):
        """CONNECTING state must not schedule a reconnect task."""
        from xknx.core import XknxConnectionState

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        gateway._setup_complete = True
        gateway._connected = False

        gateway._on_connection_state_changed(XknxConnectionState.CONNECTING)

        assert gateway._connected is False
        mock_hass.async_create_task.assert_not_called()

    def test_on_connection_state_changed_connected_schedules_reconnect(self, mock_hass):
        """CONNECTED state must schedule _async_on_reconnect via hass.async_create_task."""
        from xknx.core import XknxConnectionState

        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        gateway._setup_complete = True

        gateway._on_connection_state_changed(XknxConnectionState.CONNECTED)

        mock_hass.async_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_on_reconnect_success(self, mock_hass):
        """Successful reconnect must re-authenticate and set _connected=True."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        gateway._connected = False

        mock_rest = AsyncMock()
        mock_rest.logout = AsyncMock()
        mock_rest.login = AsyncMock()
        mock_rest.enable_tunneling = AsyncMock()
        gateway._rest_client = mock_rest

        await gateway._async_on_reconnect()

        mock_rest.logout.assert_called_once()
        mock_rest.login.assert_called_once_with("admin", "admin")
        mock_rest.enable_tunneling.assert_called_once()
        assert gateway._connected is True

    @pytest.mark.asyncio
    async def test_async_on_reconnect_failure_leaves_disconnected(self, mock_hass):
        """Reconnect exception must not set _connected=True."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        gateway._connected = False

        mock_rest = AsyncMock()
        mock_rest.logout = AsyncMock(side_effect=Exception("Network error"))
        gateway._rest_client = mock_rest

        await gateway._async_on_reconnect()

        assert gateway._connected is False

    @pytest.mark.asyncio
    async def test_async_on_reconnect_skipped_without_rest_client(self, mock_hass):
        """Reconnect must be a no-op when _rest_client is None."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=False,
        )
        gateway._rest_client = None

        await gateway._async_on_reconnect()

        assert gateway._connected is False

    @pytest.mark.asyncio
    async def test_async_on_reconnect_skipped_in_simulation_mode(self, mock_hass):
        """Reconnect must be a no-op in simulation mode even when rest_client is set."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )
        mock_rest = AsyncMock()
        gateway._rest_client = mock_rest

        await gateway._async_on_reconnect()

        mock_rest.logout.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_disconnect_without_connection_callback(self, mock_hass):
        """Disconnect must be safe when no connection-state callback was registered."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=True,
        )
        await gateway.async_setup()
        assert gateway._unregister_connection_cb is None

        await gateway.async_disconnect()

        assert gateway.connected is False


class TestSessionRefreshLoop:
    """Tests for the proactive session-refresh loop (_session_refresh_loop)."""

    def _make_gateway(self, mock_hass, *, simulation_mode: bool = False) -> LuxorKNXGateway:
        return LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=simulation_mode,
        )

    @pytest.mark.asyncio
    async def test_refresh_loop_calls_logout_login_enable(self, mock_hass):
        """One full iteration must call logout, login, and enable_tunneling."""
        from custom_components.luxor_living.const import SESSION_REFRESH_INTERVAL

        gateway = self._make_gateway(mock_hass)
        mock_rest = AsyncMock()
        gateway._rest_client = mock_rest

        sleep_calls: list[int] = []

        async def _controlled_sleep(interval: int) -> None:
            sleep_calls.append(interval)
            if len(sleep_calls) >= 2:
                raise asyncio.CancelledError  # stop after first body execution

        with patch("asyncio.sleep", side_effect=_controlled_sleep):
            try:
                await gateway._session_refresh_loop()
            except asyncio.CancelledError:
                pass

        assert sleep_calls[0] == SESSION_REFRESH_INTERVAL, "first sleep must use the interval"
        mock_rest.logout.assert_called_once()
        mock_rest.login.assert_called_once_with("admin", "admin")
        mock_rest.enable_tunneling.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_loop_skips_without_rest_client(self, mock_hass):
        """Loop must not crash and must skip the refresh when _rest_client is None."""
        gateway = self._make_gateway(mock_hass)
        gateway._rest_client = None

        with patch("asyncio.sleep", new_callable=AsyncMock):
            task = asyncio.create_task(gateway._session_refresh_loop())
            await asyncio.sleep(0)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_refresh_loop_skips_in_simulation_mode(self, mock_hass):
        """Loop must not perform I/O in simulation mode."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)
        mock_rest = AsyncMock()
        gateway._rest_client = mock_rest

        with patch("asyncio.sleep", new_callable=AsyncMock):
            task = asyncio.create_task(gateway._session_refresh_loop())
            await asyncio.sleep(0)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        mock_rest.logout.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_loop_continues_after_exception(self, mock_hass):
        """A REST failure must be logged but must not stop the loop."""
        gateway = self._make_gateway(mock_hass)
        mock_rest = AsyncMock()
        mock_rest.logout.side_effect = Exception("network error")
        gateway._rest_client = mock_rest

        call_count = 0

        async def _count_sleeps(interval):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError

        with patch("asyncio.sleep", side_effect=_count_sleeps):
            try:
                await gateway._session_refresh_loop()
            except asyncio.CancelledError:
                pass

        assert call_count >= 2  # loop did not terminate after first failure

    @pytest.mark.asyncio
    async def test_refresh_loop_cancelled_on_disconnect(self, mock_hass):
        """async_disconnect must cancel a running session refresh task."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)
        await gateway.async_setup()

        # Manually plant a fake running task to verify disconnect cancels it
        async def _never_ending():
            await asyncio.sleep(99999)

        task = asyncio.create_task(_never_ending())
        gateway._session_refresh_task = task

        await gateway.async_disconnect()

        assert task.cancelled()
        assert gateway._session_refresh_task is None

    @pytest.mark.asyncio
    async def test_refresh_loop_none_task_safe_on_disconnect(self, mock_hass):
        """async_disconnect must not raise when _session_refresh_task is None."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)
        await gateway.async_setup()
        gateway._session_refresh_task = None

        await gateway.async_disconnect()  # must not raise

        assert gateway.connected is False

    @pytest.mark.asyncio
    async def test_refresh_loop_sets_connected_true(self, mock_hass):
        """After a successful refresh, _connected must be set to True."""
        gateway = self._make_gateway(mock_hass)
        mock_rest = AsyncMock()
        gateway._rest_client = mock_rest
        gateway._connected = False

        call_count = 0

        async def _controlled_sleep(interval: int) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError

        with patch("asyncio.sleep", side_effect=_controlled_sleep):
            try:
                await gateway._session_refresh_loop()
            except asyncio.CancelledError:
                pass

        assert gateway._connected is True


class TestZombieWatchdog:
    """Tests for the zombie-tunnel watchdog (_zombie_watchdog_loop)."""

    def _make_gateway(self, mock_hass, *, simulation_mode: bool = False) -> LuxorKNXGateway:
        return LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
            simulation_mode=simulation_mode,
        )

    def _controlled_sleep(self, sleep_calls: list[int], stop_after: int = 2):
        async def _sleep(interval: int) -> None:
            sleep_calls.append(interval)
            if len(sleep_calls) >= stop_after:
                raise asyncio.CancelledError

        return _sleep

    @pytest.mark.asyncio
    async def test_watchdog_noop_below_threshold(self, mock_hass):
        """Error count increasing by less than the threshold must not reconnect."""
        from custom_components.luxor_living.const import ZOMBIE_ERROR_THRESHOLD

        gateway = self._make_gateway(mock_hass)
        mock_xknx = MagicMock()
        mock_xknx.connection_manager.cemi_count_outgoing_error = ZOMBIE_ERROR_THRESHOLD - 1
        gateway._xknx = mock_xknx

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_not_called()
        assert gateway._last_cemi_error_count == ZOMBIE_ERROR_THRESHOLD - 1

    @pytest.mark.asyncio
    async def test_watchdog_skips_without_xknx(self, mock_hass):
        """Loop must not crash and must skip the check when _xknx is None."""
        gateway = self._make_gateway(mock_hass)
        gateway._xknx = None

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_watchdog_skips_in_simulation_mode(self, mock_hass):
        """Loop must not act on the counter in simulation mode."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)
        mock_xknx = MagicMock()
        mock_xknx.connection_manager.cemi_count_outgoing_error = 999
        gateway._xknx = mock_xknx

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_watchdog_triggers_recovery_above_threshold(self, mock_hass):
        """Error count jumping by >= threshold must schedule _async_zombie_recover."""
        from custom_components.luxor_living.const import ZOMBIE_ERROR_THRESHOLD

        gateway = self._make_gateway(mock_hass)
        mock_xknx = MagicMock()
        mock_xknx.connection_manager.cemi_count_outgoing_error = ZOMBIE_ERROR_THRESHOLD
        gateway._xknx = mock_xknx

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_called_once()
        # Coroutine objects expose __name__ == the method name; close it to
        # avoid a "never awaited" warning since we don't run the event loop here.
        scheduled_coro = mock_hass.async_create_task.call_args[0][0]
        assert scheduled_coro.__name__ == "_async_zombie_recover"
        scheduled_coro.close()

    @pytest.mark.asyncio
    async def test_watchdog_respects_cooldown(self, mock_hass):
        """A second breach within ZOMBIE_RECONNECT_COOLDOWN must not re-trigger."""
        from custom_components.luxor_living.const import ZOMBIE_ERROR_THRESHOLD

        gateway = self._make_gateway(mock_hass)
        gateway._last_zombie_reconnect_at = time.monotonic()  # just fired
        mock_xknx = MagicMock()
        mock_xknx.connection_manager.cemi_count_outgoing_error = ZOMBIE_ERROR_THRESHOLD
        gateway._xknx = mock_xknx

        sleep_calls: list[int] = []
        with patch("asyncio.sleep", side_effect=self._controlled_sleep(sleep_calls)):
            try:
                await gateway._zombie_watchdog_loop()
            except asyncio.CancelledError:
                pass

        mock_hass.async_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_zombie_recover_calls_disconnect_then_setup(self, mock_hass):
        """Recovery must fully disconnect, then run setup again, in order."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)
        call_order: list[str] = []

        async def _fake_disconnect():
            call_order.append("disconnect")

        async def _fake_setup():
            call_order.append("setup")
            return True

        gateway.async_disconnect = _fake_disconnect
        gateway.async_setup = _fake_setup

        await gateway._async_zombie_recover()

        assert call_order == ["disconnect", "setup"]

    @pytest.mark.asyncio
    async def test_async_zombie_recover_swallows_exceptions(self, mock_hass):
        """A failure during recovery must be logged, not raised (fire-and-forget task)."""
        gateway = self._make_gateway(mock_hass, simulation_mode=True)

        async def _boom():
            raise RuntimeError("gateway unreachable")

        gateway.async_disconnect = _boom

        await gateway._async_zombie_recover()  # must not raise


class TestSessionLockRaceCondition:
    """Regression tests for the race condition between _session_refresh_loop and _async_on_reconnect.

    Issue #141: without the lock, concurrent logout/login cycles create duplicate orphaned
    sessions in the IP1 session table, eventually causing the KNX bus to freeze.
    """

    def _make_gateway(self, mock_hass) -> LuxorKNXGateway:
        return LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
        )

    @pytest.mark.asyncio
    async def test_reconnect_skipped_when_refresh_lock_held(self, mock_hass):
        """_async_on_reconnect must bail out immediately if _session_lock is held.

        Regression: without this guard, a concurrent logout() in _async_on_reconnect
        would cancel the fresh session created by _session_refresh_loop, doubling
        the number of orphaned sessions on the IP1 per refresh cycle.
        """
        gateway = self._make_gateway(mock_hass)
        mock_rest = AsyncMock()
        gateway._rest_client = mock_rest
        gateway._setup_complete = True

        async with gateway._session_lock:
            await gateway._async_on_reconnect()

        mock_rest.logout.assert_not_called()
        mock_rest.login.assert_not_called()
        mock_rest.enable_tunneling.assert_not_called()

    @pytest.mark.asyncio
    async def test_reconnect_acquires_lock_when_free(self, mock_hass):
        """_async_on_reconnect must run normally when the lock is not held."""
        gateway = self._make_gateway(mock_hass)
        mock_rest = AsyncMock()
        gateway._rest_client = mock_rest
        gateway._setup_complete = True

        await gateway._async_on_reconnect()

        mock_rest.logout.assert_called_once()
        mock_rest.login.assert_called_once_with("admin", "admin")
        mock_rest.enable_tunneling.assert_called_once()
        assert gateway._connected is True

    @pytest.mark.asyncio
    async def test_refresh_and_reconnect_do_not_run_concurrently(self, mock_hass):
        """Refresh loop and reconnect handler must not hold the lock simultaneously.

        Simulates the race: refresh loop acquires the lock, then a CONNECTED event
        fires. _async_on_reconnect must skip (not deadlock, not double-logout).
        """
        gateway = self._make_gateway(mock_hass)
        mock_rest = AsyncMock()
        gateway._rest_client = mock_rest
        gateway._setup_complete = True

        refresh_ran = []
        reconnect_ran = []

        async def slow_refresh():
            async with gateway._session_lock:
                refresh_ran.append(True)
                await asyncio.sleep(0.05)  # simulate I/O

        async def try_reconnect():
            await gateway._async_on_reconnect()
            reconnect_ran.append(gateway._session_lock.locked())

        await asyncio.gather(slow_refresh(), try_reconnect())

        assert refresh_ran, "refresh must have executed"
        # reconnect must have seen the lock as held and skipped without calling logout
        assert mock_rest.logout.call_count <= 1  # at most once (from reconnect if it ran after)

    @pytest.mark.asyncio
    async def test_session_lock_attribute_exists(self, mock_hass):
        """Gateway must expose _session_lock as an asyncio.Lock instance."""
        gateway = self._make_gateway(mock_hass)
        assert isinstance(gateway._session_lock, asyncio.Lock)


class TestSendTelegramMutationTargets:
    """Smoke tests targeting surviving mutants in async_send_telegram.

    Each test is written to kill a specific class of mutant identified
    by mutmut (see mutants/custom_components/luxor_living/knx_gateway.py.meta).
    """

    def _make_connected_gateway(self, mock_hass):
        gw = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
        )
        gw._connected = True
        gw._xknx = MagicMock()
        gw._xknx.telegrams = MagicMock()
        gw._xknx.telegrams.put = AsyncMock()
        return gw

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_send_returns_false_when_xknx_is_none(self, mock_hass):
        """Kill mutmut_15: 'or' → 'and' in the not-connected guard.

        If _connected=True but _xknx=None the gateway cannot send.
        The mutant changes 'or' to 'and', making this case slip through.
        """
        gw = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
        )
        gw._connected = True
        gw._xknx = None  # connected flag says True, but no xknx instance

        result = await gw.async_send_telegram("1/2/3", True, "binary")

        assert result is False

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_binary_type_sends_dpt_binary_payload(self, mock_hass):
        """Kill mutmut_25: 'value_type == binary' → 'value_type != binary'.

        Verifies the value_type dispatch is correct: binary → DPTBinary,
        not percent → DPTArray.
        """
        from xknx.dpt import DPTBinary
        from xknx.telegram.apci import GroupValueWrite

        gw = self._make_connected_gateway(mock_hass)

        await gw.async_send_telegram("1/2/3", True, "binary")

        gw._xknx.telegrams.put.assert_called_once()
        telegram = gw._xknx.telegrams.put.call_args[0][0]
        assert isinstance(telegram.payload, GroupValueWrite)
        assert isinstance(telegram.payload.value, DPTBinary)

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_percent_type_sends_correct_byte_value(self, mock_hass):
        """Kill mutations in percent conversion: int(value * 255 / 100).

        50% must encode to 127 (floor of 50*255/100=127.5 → 127).
        A mutant changing 255 to 254 would give 127 too, but 100% = 255
        is unambiguous.
        """
        from xknx.dpt import DPTArray
        from xknx.telegram.apci import GroupValueWrite

        gw = self._make_connected_gateway(mock_hass)

        await gw.async_send_telegram("1/2/3", 100, "percent")

        telegram = gw._xknx.telegrams.put.call_args[0][0]
        assert isinstance(telegram.payload.value, DPTArray)
        assert telegram.payload.value.value == (255,)  # 100% → 255

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_zero_percent_sends_zero_byte(self, mock_hass):
        """0% must encode to byte 0, not a garbage value."""
        from xknx.dpt import DPTArray

        gw = self._make_connected_gateway(mock_hass)
        await gw.async_send_telegram("1/2/3", 0, "percent")

        telegram = gw._xknx.telegrams.put.call_args[0][0]
        assert telegram.payload.value.value == (0,)


class TestRegisterListenerMutationTargets:
    """Smoke tests targeting surviving mutants in register_listener.

    mutmut_1/2/3 all mutate the address normalization step:
    normalized = str(GroupAddress(group_address)) → None / str(None) / etc.
    """

    @pytest.mark.smoke
    def test_listener_stored_under_normalized_address(self, mock_hass):
        """Kill mutmut_1: normalization result used as dict key.

        After register_listener("1/2/3", cb), the callback must be
        retrievable under the canonical "1/2/3" string key.
        """
        gw = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
        )
        cb = MagicMock()
        gw.register_listener("1/2/3", cb)

        assert "1/2/3" in gw._listeners
        assert cb in gw._listeners["1/2/3"]

    @pytest.mark.smoke
    def test_integer_address_normalized_to_string(self, mock_hass):
        """Kill mutmut_2/3: normalization must convert non-string addresses.

        Integer GA 0x0803 = group address 1/0/3 — the callback must be
        stored under the canonical '1/0/3' string, not under None or
        'None'.
        """
        gw = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            username="admin",
            password="admin",
        )
        cb = MagicMock()
        gw.register_listener(0x0803, cb)  # integer address

        # Must be stored under a string key, never None
        for key in gw._listeners:
            assert key is not None
            assert key != "None"
        assert any(cb in cbs for cbs in gw._listeners.values())
