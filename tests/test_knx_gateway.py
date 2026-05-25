"""Tests for KNX Gateway."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.knx_gateway import LuxorKNXGateway


@pytest_asyncio.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))
    return hass


class TestLuxorKNXGateway:
    """Test LuxorKNXGateway class."""

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
        mock_xknx.telegram_queue.register_telegram_received_cb = MagicMock()
        mock_xknx.connection_manager.register_connection_state_changed_cb = MagicMock(
            return_value=MagicMock()
        )
        mock_xknx_class.return_value = mock_xknx

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
        mock_xknx.connection_manager.connect = AsyncMock()
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
        mock_xknx.connection_manager.connect = AsyncMock()
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

        async def _one_iteration():
            """Run the loop but cancel after the first sleep so it executes exactly once."""
            task = asyncio.create_task(gateway._session_refresh_loop())
            await asyncio.sleep(0)  # let the task start
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await _one_iteration()

        mock_sleep.assert_called_once_with(SESSION_REFRESH_INTERVAL)
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
