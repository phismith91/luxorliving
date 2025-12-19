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
            connection_type="tunneling",
            simulation_mode=True,
        )
        
        assert gateway.simulation_mode is True
        assert gateway.host == "192.168.1.3"
        assert gateway.port == 3671
        assert gateway._connected is False

    def test_init_tunneling_mode(self, mock_hass):
        """Test initialization with tunneling mode."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
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
            simulation_mode=True,
        )
        
        result = await gateway.async_setup()
        
        assert result is True
        assert gateway.connected is True
        assert gateway._xknx is None

    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    async def test_async_setup_real_mode(self, mock_xknx_class, mock_hass):
        """Test setup in real mode."""
        mock_xknx = AsyncMock()
        mock_xknx.start = AsyncMock()
        mock_xknx.telegram_queue.register_telegram_received_cb = MagicMock()
        mock_xknx_class.return_value = mock_xknx
        
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            simulation_mode=False,
        )
        
        result = await gateway.async_setup()
        
        assert result is True
        assert gateway.connected is True
        mock_xknx.start.assert_called_once()
        mock_xknx.telegram_queue.register_telegram_received_cb.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    async def test_async_setup_failure(self, mock_xknx_class, mock_hass):
        """Test setup failure."""
        mock_xknx = AsyncMock()
        mock_xknx.start = AsyncMock(side_effect=Exception("Connection failed"))
        mock_xknx_class.return_value = mock_xknx
        
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            simulation_mode=False,
        )
        
        result = await gateway.async_setup()
        
        assert result is False
        assert gateway.connected is False

    @pytest.mark.asyncio
    async def test_async_send_telegram_simulation(self, mock_hass):
        """Test sending telegram in simulation mode."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
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
            simulation_mode=False,
        )
        
        result = await gateway.async_send_telegram("1/2/3", True, "binary")
        
        assert result is False

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    async def test_async_send_telegram_binary(self, mock_xknx_class, mock_hass):
        """Test sending binary telegram."""
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
            simulation_mode=False,
        )
        await gateway.async_setup()
        
        result = await gateway.async_send_telegram("1/2/3", True, "binary")
        
        assert result is True
        mock_xknx.telegrams.put.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.luxor_living.knx_gateway.XKNX")
    async def test_async_send_telegram_percent(self, mock_xknx_class, mock_hass):
        """Test sending percent telegram."""
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
            simulation_mode=True,
        )
        
        callback = MagicMock()
        gateway.register_listener("1/2/3", callback)
        
        # Mock telegram
        from xknx.telegram import Telegram
        from xknx.telegram.apci import GroupValueWrite
        from xknx.telegram.address import GroupAddress
        from xknx.dpt import DPTBinary
        
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
            simulation_mode=True,
        )
        
        callback = MagicMock()
        gateway.register_listener("1/2/4", callback)
        
        # Mock telegram with DPT 5.001 (percent)
        from xknx.telegram import Telegram
        from xknx.telegram.apci import GroupValueWrite
        from xknx.telegram.address import GroupAddress
        from xknx.dpt import DPTArray
        
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
    async def test_async_disconnect(self, mock_xknx_class, mock_hass):
        """Test disconnecting from gateway."""
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
            simulation_mode=False,
        )
        await gateway.async_setup()
        
        await gateway.async_disconnect()
        
        assert gateway.connected is False
        mock_xknx.stop.assert_called_once()

    def test_properties(self, mock_hass):
        """Test gateway properties."""
        gateway = LuxorKNXGateway(
            hass=mock_hass,
            host="192.168.1.3",
            port=3671,
            simulation_mode=True,
        )
        
        assert gateway.connected is False
        assert gateway.xknx is None
        
        # After setup
        asyncio.run(gateway.async_setup())
        assert gateway.connected is True
