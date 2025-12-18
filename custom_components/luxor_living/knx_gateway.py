"""KNX Gateway Manager for LUXORliving IP1."""
from __future__ import annotations

import asyncio
import logging
from typing import Callable, Any

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import Telegram
from xknx.telegram.apci import GroupValueWrite, GroupValueRead, GroupValueResponse
from xknx.telegram.address import GroupAddress
from xknx.dpt import DPTBinary, DPTArray

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT

_LOGGER = logging.getLogger(__name__)


class LuxorKNXGateway:
    """Manages KNX/IP connection to LUXORliving IP1 Gateway."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        connection_type: str = "tunneling",
        simulation_mode: bool = False,
    ) -> None:
        """Initialize the KNX gateway."""
        self.hass = hass
        self.host = host
        self.port = port
        self.simulation_mode = simulation_mode
        self._xknx: XKNX | None = None
        self._listeners: dict[str, list[Callable]] = {}
        self._connected = False
        
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
        """Set up the KNX connection."""
        if self.simulation_mode:
            _LOGGER.warning("🔥 KNX Gateway in SIMULATION MODE - no real communication")
            self._connected = True
            return True

        try:
            # Create XKNX instance
            self._xknx = XKNX()
            
            # Configure connection
            connection_config = ConnectionConfig(
                connection_type=self._connection_type,
                gateway_ip=self.host,
                gateway_port=self.port,
                auto_reconnect=True,
                auto_reconnect_wait=3,
            )
            
            # Start XKNX
            await self._xknx.start()
            
            # Connect to gateway
            await self._xknx.connection_manager.connect(connection_config)
            
            # Register telegram callback
            self._xknx.telegram_queue.register_telegram_received_cb(
                self._telegram_received_callback
            )
            
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
            return False

    async def async_disconnect(self) -> None:
        """Disconnect from KNX gateway."""
        if self._xknx and not self.simulation_mode:
            try:
                await self._xknx.stop()
                _LOGGER.info("Disconnected from KNX Gateway")
            except Exception as err:
                _LOGGER.error("Error disconnecting from KNX: %s", err)
        
        self._connected = False
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
                payload = GroupValueWrite(DPTBinary(value))
            elif value_type == "percent":
                # DPT 5.001 (0-100%)
                payload = GroupValueWrite(DPTArray(int(value * 255 / 100)))
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

    async def async_read_group_address(self, group_address: str) -> bool:
        """Send a read request to a KNX group address.
        
        Args:
            group_address: KNX group address to read
            
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
            
            await self._xknx.telegrams.put(telegram)
            _LOGGER.debug("📖 Sent read request to %s", group_address)
            return True

        except Exception as err:
            _LOGGER.error("Failed to read from %s: %s", group_address, err)
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
            if isinstance(telegram.payload.value, DPTBinary):
                value = telegram.payload.value.value
            elif isinstance(telegram.payload.value, DPTArray):
                # For DPT arrays, we'll need to decode based on type
                # For now, just get the raw value
                value = telegram.payload.value.value
            else:
                value = telegram.payload.value
            
            _LOGGER.debug(
                "📥 Received KNX telegram: %s=%s",
                group_address,
                value,
            )
            
            # Notify listeners
            if group_address in self._listeners:
                for callback in self._listeners[group_address]:
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
