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
