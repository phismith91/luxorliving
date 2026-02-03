"""KNX Gateway Manager for LUXORliving IP1 with REST API Authentication."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, cast

from homeassistant.core import HomeAssistant
from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import Telegram
from xknx.telegram.address import GroupAddress
from xknx.telegram.apci import GroupValueRead, GroupValueWrite

from .circuit_breaker import CircuitBreakerOpenException, get_knx_circuit_breaker
from .knx.discovery_engine import (
    DISCOVERY_DEBOUNCE_DELAY,
    DISCOVERY_MAX_CANDIDATES_PER_ADDRESS,
    DISCOVERY_MIN_SAMPLES,
    DISCOVERY_VALUE_TOLERANCE,
    DiscoveryEngine,
)
from .knx.listener_manager import ListenerManager
from .knx.telegram_processor import TelegramProcessor
from .rest_client import AuthenticationError, BAOSRestClient, TunnelingError

_LOGGER = logging.getLogger(__name__)

# Re-export constants for backward compatibility
__all__ = [
    "LuxorKNXGateway",
    "DISCOVERY_DEBOUNCE_DELAY",
    "DISCOVERY_MAX_CANDIDATES_PER_ADDRESS",
    "DISCOVERY_MIN_SAMPLES",
    "DISCOVERY_VALUE_TOLERANCE",
]


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
        discovery_timeout: float = DISCOVERY_DEBOUNCE_DELAY,
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
        self._connected = False
        self._tunneling_enabled = False

        # Initialize sub-components
        self._listener_manager = ListenerManager()
        self._discovery_engine = DiscoveryEngine(discovery_timeout)
        self._telegram_processor = TelegramProcessor(
            hass, self._listener_manager, self._discovery_engine
        )

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
            _LOGGER.warning("KNX Gateway in SIMULATION MODE - no real communication")
            self._connected = True
            return True

        circuit_breaker = get_knx_circuit_breaker()

        async def _setup_knx_connection():
            # Step 1: REST API Login (only for tunneling)
            if self._connection_type == ConnectionType.TUNNELING:
                _LOGGER.debug("Step 1/3: REST API Login...")

                # Create REST client and enter async context
                self._rest_client = BAOSRestClient(self.host, port=self.http_port)
                await self._rest_client.__aenter__()

                try:
                    await self._rest_client.login(self.username, self.password)
                    _LOGGER.debug("REST API login successful")
                except AuthenticationError as err:
                    _LOGGER.error("Authentication failed: %s", err)
                    await self._rest_client.__aexit__(None, None, None)
                    self._rest_client = None
                    raise err  # Re-raise to trigger circuit breaker

                # Step 2: Enable KNX Tunneling
                _LOGGER.debug("Step 2/3: Enabling KNX Tunneling...")
                try:
                    await self._rest_client.enable_tunneling()
                    self._tunneling_enabled = True
                    _LOGGER.debug("KNX Tunneling enabled")
                except TunnelingError as err:
                    _LOGGER.error("Failed to enable tunneling: %s", err)
                    await self._rest_client.__aexit__(None, None, None)
                    self._rest_client = None
                    raise err  # Re-raise to trigger circuit breaker

            # Step 3: Connect KNX
            _LOGGER.debug("Step 3/3: Connecting KNX...")

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
                self.hass.async_create_task(
                    self._telegram_processor.telegram_received_callback(telegram)
                )

            self._xknx.telegram_queue.register_telegram_received_cb(_sync_callback)

            self._connected = True
            _LOGGER.info(
                "Successfully connected to KNX Gateway %s:%s (%s mode)",
                self.host,
                self.port,
                self._connection_type.name,
            )

            return True

        try:
            return cast(bool, await circuit_breaker.call(_setup_knx_connection))
        except CircuitBreakerOpenException as e:
            _LOGGER.error("KNX connection rejected by circuit breaker: %s", e)
            self._connected = False
            return False
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
                # Properly exit async context (calls logout + closes session)
                await self._rest_client.__aexit__(None, None, None)
                _LOGGER.info("Logged out from REST API (tunneling auto-deactivated)")
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
                payload = GroupValueWrite(
                    DPTArray(value if isinstance(value, (list, bytes)) else [int(value)])
                )

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
                self._telegram_processor.track_initial_read(group_address)

            await self._xknx.telegrams.put(telegram)
            _LOGGER.info(
                "📤 Sent GroupValueRead to %s%s",
                group_address,
                " (INITIAL READ)" if is_initial else "",
            )
            return True

        except Exception as err:
            _LOGGER.error("Failed to read from %s: %s", group_address, err)
            if is_initial:
                self._telegram_processor.clear_initial_read(group_address)
            return False

    def register_listener(
        self,
        group_address: str | int,
        callback: Callable[[str, Any], None],
    ) -> None:
        """Register a callback for incoming telegrams to a specific group address.

        Args:
            group_address: KNX group address to listen to (int or "x/y/z")
            callback: Callback function that receives (group_address, value)
        """
        self._listener_manager.register_listener(group_address, callback)

    def set_group_address_labels(self, label_map: dict[str, list[str]]) -> None:
        """Provide a GA→labels map to enrich KNX logs with names.

        Args:
            label_map: Mapping of 'x/y/z' → ['Name (ID)', ...]
        """
        self._listener_manager.set_group_address_labels(label_map)

    def set_individual_address_labels(self, label_map: dict[str, list[str]]) -> None:
        """Provide an IA→labels map to enrich KNX logs with source device names."""
        self._listener_manager.set_individual_address_labels(label_map)

    def unregister_listener(
        self,
        group_address: str | int,
        callback: Callable[[str, Any], None],
    ) -> None:
        """Unregister a callback for a group address."""
        self._listener_manager.unregister_listener(group_address, callback)

    async def process_incoming_value(
        self,
        group_address: str,
        value: bool | int | float | bytes | tuple | list,
        value_type: str | None = None,
    ) -> None:
        """Process an externally pushed value (e.g., from webhook or websocket push).

        This normalizes the incoming value similarly to telegram payload processing and
        notifies registered listeners as if a telegram was received. It's used by the
        webhook/WebSocket push spike to integrate external push events into the system.
        """
        await self._telegram_processor.process_incoming_value(group_address, value, value_type)

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
        return self._telegram_processor.pending_initial_reads

    # Discovery-related methods - delegate to discovery engine
    def register_discovery_callback(self, callback: Callable[[dict], None]) -> None:
        """Register a callback for when new sensors are discovered."""
        self._discovery_engine.register_discovery_callback(callback)

    def get_discovered_sensors(self) -> dict[str, dict[str, Any]]:
        """Return all discovered sensors."""
        return self._discovery_engine.get_discovered_sensors()

    def load_discovered_sensors(self, sensors: dict[str, dict[str, Any]]) -> None:
        """Load previously discovered sensors (e.g., from config entry)."""
        self._discovery_engine.load_discovered_sensors(sensors)

    def set_known_addresses(self, addresses: set[str]) -> None:
        """Set known LXP addresses to exclude from auto-discovery."""
        self._discovery_engine.set_known_addresses(addresses)

    def set_sensor_types(self, sensor_types: dict[str, str]) -> None:
        """Set known sensor types for accurate logging (e.g., {'5/0/3': 'illuminance'})."""
        self._discovery_engine.set_sensor_types(sensor_types)
