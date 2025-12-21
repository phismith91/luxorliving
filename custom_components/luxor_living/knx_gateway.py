"""KNX Gateway Manager for LUXORliving IP1 with REST API Authentication."""
from __future__ import annotations

import logging
from typing import Callable, Any

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import Telegram
from xknx.telegram.apci import GroupValueWrite, GroupValueRead, GroupValueResponse
from xknx.telegram.address import GroupAddress
from xknx.dpt import DPTBinary, DPTArray

from homeassistant.core import HomeAssistant

from .rest_client import BAOSRestClient, AuthenticationError, TunnelingError

_LOGGER = logging.getLogger(__name__)


class LuxorKNXGateway:
    """
    Manages KNX/IP connection to LUXORliving IP1 Gateway.
    
    Requires REST API authentication to enable KNX Tunneling:
    1. REST Login → Session Token
    2. PUT /rest/device/authtunneling {"enabled": true}
    3. KNX Tunneling connection
    4. On shutdown: Logout → Tunneling auto-deactivated
    """

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        username: str,
        password: str,
        http_port: int = 80,
        connection_type: str = "tunneling",
        simulation_mode: bool = False,
    ) -> None:
        """Initialize the KNX gateway."""
        self.hass = hass
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.http_port = http_port
        self.simulation_mode = simulation_mode
        
        self._xknx: XKNX | None = None
        self._rest_client: BAOSRestClient | None = None
        self._listeners: dict[str, list[Callable]] = {}
        self._connected = False
        self._tunneling_enabled = False
        self._initial_read_pending: set[str] = set()  # Track pending initial reads
        
        # Map connection type string to XKNX enum
        self._connection_type = (
            ConnectionType.TUNNELING
            if connection_type.lower() == "tunneling"
            else ConnectionType.ROUTING
        )
        
        _LOGGER.info(
            "Initializing LUXORliving KNX Gateway: %s:%s (mode: %s, simulation: %s)",
            host,
            port,
            connection_type,
            simulation_mode,
        )

    async def async_setup(self) -> bool:
        """
        Set up the KNX connection with REST API authentication.
        
        Steps:
        1. REST API Login
        2. Enable KNX Tunneling
        3. Connect KNX
        
        Returns:
            True if setup was successful
        """
        if self.simulation_mode:
            _LOGGER.warning("🔥 KNX Gateway in SIMULATION MODE - no real communication")
            self._connected = True
            return True

        try:
            # Step 1: REST API Login (only for tunneling)
            if self._connection_type == ConnectionType.TUNNELING:
                _LOGGER.info("🔐 Step 1/3: REST API Login...")
                self._rest_client = BAOSRestClient(self.host, port=self.http_port)
                
                try:
                    await self._rest_client.login(self.username, self.password)
                    _LOGGER.info("✅ REST API login successful")
                except AuthenticationError as err:
                    _LOGGER.error("❌ Authentication failed: %s", err)
                    return False
                
                # Step 2: Enable KNX Tunneling
                _LOGGER.info("🔧 Step 2/3: Enabling KNX Tunneling...")
                try:
                    await self._rest_client.enable_tunneling()
                    self._tunneling_enabled = True
                    _LOGGER.info("✅ KNX Tunneling enabled")
                except TunnelingError as err:
                    _LOGGER.error("❌ Failed to enable tunneling: %s", err)
                    await self._rest_client.logout()
                    return False
            
            # Step 3: Connect KNX
            _LOGGER.info("🔌 Step 3/3: Connecting KNX...")
            
            # Configure connection BEFORE creating XKNX instance
            connection_config = ConnectionConfig(
                connection_type=self._connection_type,
                gateway_ip=self.host,
                gateway_port=self.port,
                auto_reconnect=True,
                auto_reconnect_wait=3,
            )
            
            # Create XKNX instance with connection config
            self._xknx = XKNX(connection_config=connection_config)
            
            # Start XKNX with configured connection
            await self._xknx.start()
            
            # Register telegram callback (wrap async callback)
            def _sync_callback(telegram: Telegram) -> None:
                """Sync wrapper for async telegram callback."""
                self.hass.async_create_task(self._telegram_received_callback(telegram))
            
            self._xknx.telegram_queue.register_telegram_received_cb(_sync_callback)
            
            self._connected = True
            _LOGGER.info(
                "✅ Successfully connected to KNX Gateway %s:%s (%s mode)",
                self.host,
                self.port,
                self._connection_type.name,
            )
            return True

        except Exception as err:
            _LOGGER.error("Failed to connect to KNX Gateway: %s", err, exc_info=True)
            self._connected = False
            
            # Cleanup REST session on failure
            if self._rest_client:
                try:
                    await self._rest_client.logout()
                except Exception:
                    pass
            
            return False

    async def async_disconnect(self) -> None:
        """
        Disconnect from KNX gateway and cleanup REST session.
        
        NOTE: Logout automatically deactivates tunneling!
        """
        # Disconnect KNX
        if self._xknx and not self.simulation_mode:
            try:
                await self._xknx.stop()
                _LOGGER.info("Disconnected from KNX Gateway")
            except Exception as err:
                _LOGGER.error("Error disconnecting from KNX: %s", err)
        
        # Logout from REST API (deactivates tunneling)
        if self._rest_client:
            try:
                await self._rest_client.logout()
                _LOGGER.info("✅ Logged out from REST API (tunneling auto-deactivated)")
            except Exception as err:
                _LOGGER.error("Error logging out from REST API: %s", err)
            finally:
                self._rest_client = None
        
        self._connected = False
        self._tunneling_enabled = False
        self._xknx = None

    async def async_send_telegram(
        self,
        group_address: str,
        value: bool | int | float | bytes,
        value_type: str = "binary",
    ) -> bool:
        """Send a KNX telegram to a group address.
        
        Args:
            group_address: KNX group address (e.g., "1/2/3")
            value: Value to send
            value_type: Type of value ("binary", "percent", "temperature", etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if self.simulation_mode:
            _LOGGER.warning(
                "🔥 SIMULATION: Would send %s=%s to KNX address %s",
                value_type,
                value,
                group_address,
            )
            return True

        if not self._connected or not self._xknx:
            _LOGGER.error("Cannot send telegram - not connected to KNX gateway")
            return False

        try:
            # Convert group address
            ga = GroupAddress(group_address)
            
            # Create payload based on value type
            if value_type == "binary":
                payload = GroupValueWrite(DPTBinary(int(value)))
            elif value_type == "percent":
                # DPT 5.001 (0-100%) - must be list!
                # Ensure value is numeric for division
                num_value = float(value) if not isinstance(value, (int, float)) else value
                byte_value = int(num_value * 255 / 100)
                payload = GroupValueWrite(DPTArray([byte_value]))
            else:
                # For now, treat unknown types as raw bytes
                payload = GroupValueWrite(DPTArray(value if isinstance(value, (list, bytes)) else [int(value)]))
            
            # Create and send telegram
            telegram = Telegram(
                destination_address=ga,
                payload=payload,
            )
            
            await self._xknx.telegrams.put(telegram)
            
            _LOGGER.debug(
                "✅ Sent KNX telegram: %s=%s to %s",
                value_type,
                value,
                group_address,
            )
            return True

        except Exception as err:
            _LOGGER.error(
                "Failed to send telegram to %s: %s",
                group_address,
                err,
                exc_info=True,
            )
            return False

    async def async_read_group_address(self, group_address: str, is_initial: bool = False) -> bool:
        """Send a read request to a KNX group address.
        
        Args:
            group_address: KNX group address to read
            is_initial: Whether this is an initial read after startup
            
        Returns:
            True if request was sent successfully
        """
        if self.simulation_mode:
            _LOGGER.debug(
                "🔥 SIMULATION: Would read from KNX address %s",
                group_address,
            )
            return True

        if not self._connected or not self._xknx:
            _LOGGER.error("Cannot read - not connected to KNX gateway")
            return False

        try:
            ga = GroupAddress(group_address)
            telegram = Telegram(
                destination_address=ga,
                payload=GroupValueRead(),
            )
            
            if is_initial:
                self._initial_read_pending.add(group_address)
            
            await self._xknx.telegrams.put(telegram)
            _LOGGER.debug("📖 Sent read request to %s%s", group_address, " (initial)" if is_initial else "")
            return True

        except Exception as err:
            _LOGGER.error("Failed to read from %s: %s", group_address, err)
            if is_initial and group_address in self._initial_read_pending:
                self._initial_read_pending.discard(group_address)
            return False

    def register_listener(
        self,
        group_address: str,
        callback: Callable[[str, Any], None],
    ) -> None:
        """Register a callback for incoming telegrams to a specific group address.
        
        Args:
            group_address: KNX group address to listen to
            callback: Callback function that receives (group_address, value)
        """
        if group_address not in self._listeners:
            self._listeners[group_address] = []
        
        self._listeners[group_address].append(callback)
        _LOGGER.debug("Registered listener for KNX address %s", group_address)

    def unregister_listener(
        self,
        group_address: str,
        callback: Callable[[str, Any], None],
    ) -> None:
        """Unregister a callback for a group address."""
        if group_address in self._listeners:
            try:
                self._listeners[group_address].remove(callback)
                _LOGGER.debug("Unregistered listener for %s", group_address)
            except ValueError:
                pass

    async def _telegram_received_callback(self, telegram: Telegram) -> None:
        """Handle incoming KNX telegrams."""
        if not isinstance(telegram.payload, (GroupValueWrite, GroupValueResponse)):
            return

        try:
            # Get group address as string
            group_address = str(telegram.destination_address)
            
            # Extract value from payload
            payload_value = telegram.payload.value
            
            if payload_value is None:
                _LOGGER.debug("Received telegram with None value for %s", group_address)
                return
            
            # Handle different DPT types
            value: bool | int | float | bytes | tuple | list
            if isinstance(payload_value, DPTBinary):
                value = payload_value.value
            elif isinstance(payload_value, DPTArray):
                # Decode DPT arrays based on length
                raw_value = payload_value.value
                if isinstance(raw_value, (list, bytes)) and len(raw_value) == 1:
                    # DPT 5.001 (percent): 0-255 → 0-100
                    byte_val = int(raw_value[0]) if isinstance(raw_value, (list, bytes)) else int(raw_value)
                    value = int(byte_val * 100 / 255)
                else:
                    # Unknown DPT - return raw value
                    value = raw_value
            elif isinstance(payload_value, int):
                # Direct integer value (common for binary/switch)
                value = bool(payload_value)
            else:
                value = payload_value
            
            # Track initial read completion
            was_initial = group_address in self._initial_read_pending
            if was_initial:
                self._initial_read_pending.discard(group_address)
            
            telegram_type = "Response" if isinstance(telegram.payload, GroupValueResponse) else "Write"
            _LOGGER.debug(
                "📥 Received KNX %s: %s=%s (type: %s)%s",
                telegram_type,
                group_address,
                value,
                type(payload_value).__name__,
                " ✅ initial" if was_initial else "",
            )
            
            # Notify listeners
            if group_address in self._listeners:
                # Create snapshot to avoid modification during iteration
                callbacks = list(self._listeners[group_address])
                for callback in callbacks:
                    # Check if still registered (could be removed during iteration)
                    if callback not in self._listeners.get(group_address, []):
                        continue
                    try:
                        await self.hass.async_add_executor_job(
                            callback, group_address, value
                        )
                    except Exception as err:
                        _LOGGER.error(
                            "Error in listener callback for %s: %s",
                            group_address,
                            err,
                        )

        except Exception as err:
            _LOGGER.error("Error processing incoming telegram: %s", err, exc_info=True)

    @property
    def connected(self) -> bool:
        """Return connection status."""
        return self._connected

    @property
    def xknx(self) -> XKNX | None:
        """Return XKNX instance for advanced usage."""
        return self._xknx

    async def async_batch_read_group_addresses(
        self, addresses: list[str], delay_ms: int = 50
    ) -> int:
        """Send batch read requests with small delay between each.
        
        Args:
            addresses: List of KNX group addresses to read
            delay_ms: Delay in milliseconds between reads (default: 50ms)
            
        Returns:
            Number of successfully sent read requests
        """
        import asyncio
        
        if not addresses:
            return 0
        
        _LOGGER.info("📖 Starting batch read of %d addresses", len(addresses))
        
        success_count = 0
        for i, address in enumerate(addresses):
            if await self.async_read_group_address(address, is_initial=True):
                success_count += 1
            
            # Small delay to avoid overwhelming the bus
            if i < len(addresses) - 1:  # Skip delay after last address
                await asyncio.sleep(delay_ms / 1000.0)
        
        _LOGGER.info(
            "📖 Batch read completed: %d/%d successful",
            success_count,
            len(addresses),
        )
        
        return success_count

    @property
    def pending_initial_reads(self) -> int:
        """Return number of pending initial reads."""
        return len(self._initial_read_pending)
