"""Tests for KNX Tunneling connection and tunnel management."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant


class TestKNXTunneling:
    """Test KNX Tunneling connection scenarios."""

    @pytest.fixture
    def mock_knx_connection(self):
        """Mock KNX connection."""
        with patch('xknx.XKNX') as mock_xknx:
            connection = AsyncMock()
            connection.connection_state = MagicMock()
            connection.connection_state.state = "CONNECTED"
            mock_xknx.return_value = connection
            yield connection

    async def test_tunneling_connection_success(self, mock_hass, mock_knx_connection):
        """Test successful tunneling connection to BAOS 777."""
        from custom_components.luxor_living.knx_gateway import KNXGateway
        
        gateway = KNXGateway(
            host="192.168.1.3",
            port=3671,
            connection_type="tunneling"
        )
        
        await gateway.connect()
        
        assert gateway.is_connected()
        mock_knx_connection.start.assert_called_once()

    async def test_tunnel_already_in_use(self, mock_hass):
        """Test error when tunnel is already occupied (LuxorPlug running)."""
        from custom_components.luxor_living.knx_gateway import KNXGateway
        from xknx.exceptions import CommunicationError
        
        with patch('xknx.XKNX') as mock_xknx:
            mock_xknx.return_value.start.side_effect = CommunicationError(
                "Tunnel already in use"
            )
            
            gateway = KNXGateway(
                host="192.168.1.3",
                port=3671,
                connection_type="tunneling"
            )
            
            with pytest.raises(CommunicationError, match="Tunnel already in use"):
                await gateway.connect()

    async def test_tunnel_slot_detection(self, mock_hass):
        """Test detection of available tunnel slots."""
        from custom_components.luxor_living.knx_gateway import KNXGateway
        
        gateway = KNXGateway(
            host="192.168.1.3",
            port=3671,
            connection_type="tunneling"
        )
        
        # Mock BAOS 777 response: 1 slot total, 1 in use
        with patch.object(gateway, '_check_tunnel_availability') as mock_check:
            mock_check.return_value = {
                'total_slots': 1,
                'used_slots': 1,
                'available': False
            }
            
            available = await gateway.check_tunnel_available()
            
            assert available is False

    async def test_connection_retry_on_tunnel_busy(self, mock_hass):
        """Test automatic retry when tunnel is temporarily busy."""
        from custom_components.luxor_living.knx_gateway import KNXGateway
        from xknx.exceptions import CommunicationError
        
        gateway = KNXGateway(
            host="192.168.1.3",
            port=3671,
            connection_type="tunneling",
            retry_count=3,
            retry_delay=0.1  # Fast for testing
        )
        
        with patch('xknx.XKNX') as mock_xknx:
            # First 2 attempts fail, 3rd succeeds
            mock_xknx.return_value.start.side_effect = [
                CommunicationError("Busy"),
                CommunicationError("Busy"),
                None  # Success
            ]
            
            await gateway.connect()
            
            assert gateway.is_connected()
            assert mock_xknx.return_value.start.call_count == 3

    async def test_graceful_disconnect_on_luxorplug_start(self, mock_hass, mock_knx_connection):
        """Test HA gracefully disconnects when LuxorPlug needs tunnel."""
        from custom_components.luxor_living.knx_gateway import KNXGateway
        
        gateway = KNXGateway(
            host="192.168.1.3",
            port=3671,
            connection_type="tunneling"
        )
        
        await gateway.connect()
        assert gateway.is_connected()
        
        # Simulate LuxorPlug taking tunnel
        mock_knx_connection.connection_state.state = "DISCONNECTED"
        await gateway.handle_disconnect()
        
        assert not gateway.is_connected()


class TestKNXTunnelingDiagnostics:
    """Test diagnostic features for tunneling troubleshooting."""

    async def test_connection_diagnostics(self, mock_hass):
        """Test diagnostic information for tunnel connection."""
        from custom_components.luxor_living.knx_gateway import KNXGateway
        
        gateway = KNXGateway(
            host="192.168.1.3",
            port=3671,
            connection_type="tunneling"
        )
        
        diagnostics = await gateway.get_diagnostics()
        
        assert diagnostics['connection_type'] == 'tunneling'
        assert diagnostics['host'] == '192.168.1.3'
        assert diagnostics['port'] == 3671
        assert 'tunnel_status' in diagnostics
        assert 'last_error' in diagnostics

    async def test_log_tunnel_conflict_helpful_message(self, mock_hass, caplog):
        """Test that tunnel conflicts log helpful error messages."""
        from custom_components.luxor_living.knx_gateway import KNXGateway
        from xknx.exceptions import CommunicationError
        
        with patch('xknx.XKNX') as mock_xknx:
            mock_xknx.return_value.start.side_effect = CommunicationError(
                "Tunnel already in use"
            )
            
            gateway = KNXGateway(
                host="192.168.1.3",
                port=3671,
                connection_type="tunneling"
            )
            
            with pytest.raises(CommunicationError):
                await gateway.connect()
            
            # Check log contains helpful message
            assert "BAOS 777 tunnel is occupied" in caplog.text
            assert "Stop LuxorPlug" in caplog.text or "close LuxorPlug" in caplog.text


class TestKNXRoutingFallback:
    """Test fallback from tunneling to routing (if needed)."""

    async def test_routing_fallback_on_tunnel_failure(self, mock_hass):
        """Test fallback to routing when tunneling fails persistently."""
        from custom_components.luxor_living.knx_gateway import KNXGateway
        from xknx.exceptions import CommunicationError
        
        gateway = KNXGateway(
            host="192.168.1.3",
            port=3671,
            connection_type="tunneling",
            fallback_to_routing=True
        )
        
        with patch('xknx.XKNX') as mock_xknx:
            # Tunneling fails, routing succeeds
            mock_xknx_tunnel = AsyncMock()
            mock_xknx_tunnel.start.side_effect = CommunicationError("Tunnel busy")
            
            mock_xknx_routing = AsyncMock()
            mock_xknx_routing.start.return_value = None
            
            mock_xknx.side_effect = [mock_xknx_tunnel, mock_xknx_routing]
            
            await gateway.connect()
            
            assert gateway.connection_type == "routing"
            assert gateway.is_connected()
