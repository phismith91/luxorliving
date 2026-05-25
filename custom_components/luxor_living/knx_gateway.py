"""KNX Gateway Manager for LUXORliving IP1 with REST API Authentication."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, cast

from homeassistant.core import HomeAssistant
from xknx import XKNX
from xknx.core import XknxConnectionState
from xknx.dpt import DPTArray, DPTBinary
from xknx.dpt.dpt_9 import DPT2ByteFloat
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import Telegram
from xknx.telegram.address import GroupAddress
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

from .circuit_breaker import CircuitBreakerOpenException, get_knx_circuit_breaker
from .const import SESSION_REFRESH_INTERVAL
from .rest_client import AuthenticationError, BAOSRestClient, TunnelingError

_LOGGER = logging.getLogger(__name__)

# Auto-discovery configuration
DISCOVERY_MIN_SAMPLES = 3  # Minimum stable readings before creating sensor
DISCOVERY_VALUE_TOLERANCE = 0.5  # Maximum value deviation for stability
DISCOVERY_MAX_CANDIDATES_PER_ADDRESS = 20  # Prevent memory leak: max samples per address
DISCOVERY_DEBOUNCE_DELAY = 2.0  # Seconds to wait before triggering reload (batch discoveries)


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
        self.discovery_timeout = discovery_timeout

        self._xknx: XKNX | None = None
        self._rest_client: BAOSRestClient | None = None
        self._listeners: dict[str, list[Callable]] = {}
        self._connected = False
        self._tunneling_enabled = False
        self._setup_complete = False  # Guards reconnect handler against initial-connect events
        self._unregister_connection_cb: Callable[[], None] | None = None
        self._session_refresh_task: asyncio.Task | None = None
        self._initial_read_pending: set[str] = set()  # Track pending initial reads
        self._ga_label_map: dict[str, list[str]] = {}
        self._ia_label_map: dict[str, list[str]] = {}
        self._ga_sensor_type_map: dict[str, str] = {}  # {address: sensor_type} for known entities

        # Auto-discovery state
        self._discovered_sensors: dict[str, dict[str, Any]] = {}  # {address: sensor_info}
        self._discovery_candidates: dict[str, list[tuple[float, datetime]]] = defaultdict(
            list
        )  # {address: [(value, timestamp)]}
        self._discovery_callbacks: list[Callable[[dict], None]] = (
            []
        )  # Notify when new sensor discovered
        self._known_addresses: set[str] = set()  # Known LXP addresses to exclude from discovery
        self._pending_discoveries: list[dict[str, Any]] = []  # Batch discoveries for debouncing
        self._debounce_task: asyncio.Task | None = None  # Debounce reload task

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
                self.hass.async_create_task(self._telegram_received_callback(telegram))

            self._xknx.telegram_queue.register_telegram_received_cb(_sync_callback)

            # Register connection-state callback AFTER start() so the initial
            # CONNECTED event is not mistaken for a reconnect.
            self._unregister_connection_cb = (
                self._xknx.connection_manager.register_connection_state_changed_cb(
                    self._on_connection_state_changed
                )
            )

            self._connected = True
            self._setup_complete = True  # Reconnect handler is now active

            if self._connection_type == ConnectionType.TUNNELING:
                self._session_refresh_task = asyncio.create_task(
                    self._session_refresh_loop(),
                    name="luxor_session_refresh",
                )
                _LOGGER.debug(
                    "Session refresh loop started (interval %ds)", SESSION_REFRESH_INTERVAL
                )

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
                except Exception as err:
                    _LOGGER.debug("Error during REST logout cleanup: %s", err)

            return False

    async def async_disconnect(self) -> None:
        """
        Disconnect from KNX gateway and cleanup REST session.

        NOTE: Logout automatically deactivates tunneling!
        """
        # Stop reconnect handler before disconnecting so it doesn't fire during teardown
        self._setup_complete = False
        if self._unregister_connection_cb:
            self._unregister_connection_cb()
            self._unregister_connection_cb = None

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

        # Cancel session refresh loop
        if self._session_refresh_task and not self._session_refresh_task.done():
            self._session_refresh_task.cancel()
            try:
                await self._session_refresh_task
            except asyncio.CancelledError:
                pass
        self._session_refresh_task = None

        # Cancel pending debounce task so no orphaned coroutines remain
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
        self._debounce_task = None

        self._connected = False
        self._tunneling_enabled = False
        self._xknx = None

    async def _session_refresh_loop(self) -> None:
        """Periodically re-authenticate to prevent IP1 session-table saturation.

        The IP1 gateway accumulates stale tunneling sessions until the KNX bus
        freezes (typically 24-72 h).  Proactively cycling the REST session every
        6 h keeps the table clean even when XKNX never detects a disconnect.
        """
        try:
            while True:
                await asyncio.sleep(SESSION_REFRESH_INTERVAL)
                if not self._rest_client or self.simulation_mode:
                    continue
                _LOGGER.info(
                    "Proactive session refresh — cycling REST auth to prevent gateway lockup"
                )
                try:
                    await self._rest_client.logout()
                    await self._rest_client.login(self.username, self.password)
                    await self._rest_client.enable_tunneling()
                    _LOGGER.info("Proactive session refresh complete")
                except Exception as err:
                    _LOGGER.error(
                        "Proactive session refresh failed (will retry in %ds): %s",
                        SESSION_REFRESH_INTERVAL,
                        err,
                    )
        except asyncio.CancelledError:
            _LOGGER.debug("Session refresh loop cancelled")
            raise

    def _on_connection_state_changed(self, state: XknxConnectionState) -> None:
        """Handle xknx connection state changes.

        Called synchronously by xknx on every state transition. Schedules async
        work via hass.async_create_task so the event loop is not blocked.
        """
        if not self._setup_complete:
            return  # Ignore events that fire before/during initial setup

        if state == XknxConnectionState.DISCONNECTED:
            self._connected = False
            _LOGGER.warning(
                "KNX gateway %s:%s disconnected — entities will be unavailable",
                self.host,
                self.port,
            )
        elif state == XknxConnectionState.CONNECTING:
            _LOGGER.info("KNX gateway %s:%s reconnecting…", self.host, self.port)
        elif state == XknxConnectionState.CONNECTED:
            _LOGGER.info(
                "KNX gateway %s:%s reconnected — re-enabling REST tunneling",
                self.host,
                self.port,
            )
            self.hass.async_create_task(self._async_on_reconnect())

    async def _async_on_reconnect(self) -> None:
        """Re-authenticate and re-enable tunneling after xknx auto-reconnect.

        xknx restores the KNX/IP transport layer on its own (auto_reconnect=True),
        but the IP1's REST tunneling authorisation must be explicitly renewed.
        Without this the gateway accepts the KNX connection but ignores all telegrams.
        """
        if not self._rest_client or self.simulation_mode:
            return
        try:
            _LOGGER.info("Re-authenticating after reconnect (host=%s)", self.host)
            await self._rest_client.logout()
            await self._rest_client.login(self.username, self.password)
            await self._rest_client.enable_tunneling()
            self._connected = True
            _LOGGER.info("Tunneling re-enabled — entities are available again")
        except Exception as err:
            _LOGGER.error(
                "Failed to re-enable tunneling after reconnect: %s — "
                "reload the integration if the gateway remains unreachable",
                err,
            )

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
            elif value_type == "temperature":
                # DPT 9.001 (2-byte float for temperature in °C)
                encoded = DPT2ByteFloat().to_knx(float(value))
                payload = GroupValueWrite(encoded)
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
                self._initial_read_pending.add(group_address)

            await self._xknx.telegrams.put(telegram)
            _LOGGER.info(
                "📤 Sent GroupValueRead to %s%s",
                group_address,
                " (INITIAL READ)" if is_initial else "",
            )
            return True

        except Exception as err:
            _LOGGER.error("Failed to read from %s: %s", group_address, err)
            if is_initial and group_address in self._initial_read_pending:
                self._initial_read_pending.discard(group_address)
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
        # Normalize key to consistent string form "x/y/z"
        try:
            normalized = str(GroupAddress(group_address))
        except Exception as err:
            _LOGGER.debug("Could not parse group address %r, using as-is: %s", group_address, err)
            normalized = str(group_address)

        if normalized not in self._listeners:
            self._listeners[normalized] = []

        self._listeners[normalized].append(callback)
        _LOGGER.debug(
            "Registered listener for KNX address %s",
            normalized,
        )

    def set_group_address_labels(self, label_map: dict[str, list[str]]) -> None:
        """Provide a GA→labels map to enrich KNX logs with names.

        Args:
            label_map: Mapping of 'x/y/z' → ['Name (ID)', ...]
        """
        self._ga_label_map = label_map or {}
        _LOGGER.debug("Loaded %d GA labels for log enrichment", len(self._ga_label_map))

    def set_individual_address_labels(self, label_map: dict[str, list[str]]) -> None:
        """Provide an IA→labels map to enrich KNX logs with source device names."""
        self._ia_label_map = label_map or {}
        _LOGGER.debug("Loaded %d IA labels for log enrichment", len(self._ia_label_map))

    def unregister_listener(
        self,
        group_address: str | int,
        callback: Callable[[str, Any], None],
    ) -> None:
        """Unregister a callback for a group address."""
        try:
            normalized = str(GroupAddress(group_address))
        except Exception as err:
            _LOGGER.debug("Could not parse group address %r, using as-is: %s", group_address, err)
            normalized = str(group_address)

        if normalized in self._listeners:
            try:
                self._listeners[normalized].remove(callback)
                _LOGGER.debug("Unregistered listener for %s", normalized)
            except ValueError:
                pass

    async def _telegram_received_callback(self, telegram: Telegram) -> None:
        """Handle incoming KNX telegrams."""
        if not isinstance(telegram.payload, (GroupValueWrite, GroupValueResponse)):
            return

        try:
            # Get group address as string
            group_address = str(telegram.destination_address)
            source_address = str(telegram.source_address) if telegram.source_address else "unknown"

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
                if isinstance(raw_value, (list, tuple, bytes)) and len(raw_value) == 1:
                    # DPT 5.001 (percent): 0-255 → 0-100
                    byte_val = int(raw_value[0])
                    value = int(byte_val * 100 / 255)
                elif isinstance(raw_value, (list, tuple, bytes)) and len(raw_value) == 2:
                    # 2-byte float (DPT 9.xxx), used by Wetterstation (Temp, Wind, Lux)
                    try:
                        # IMPORTANT: from_knx() expects DPTArray object, not bytes!
                        value = DPT2ByteFloat().from_knx(payload_value)
                    except Exception as err:
                        _LOGGER.debug("DPT2ByteFloat decode failed for %r: %s", payload_value, err)
                        value = raw_value
                else:
                    # Unknown DPT - return raw value
                    value = raw_value
            elif isinstance(payload_value, (list, tuple)) and len(payload_value) == 2:
                # Some telegrams surface the raw tuple directly, handle as 2-byte float
                try:
                    # Create DPTArray from raw tuple for conversion
                    value = DPT2ByteFloat().from_knx(DPTArray(payload_value))
                except Exception as err:
                    _LOGGER.debug("DPT2ByteFloat decode failed for %r: %s", payload_value, err)
                    value = payload_value
            elif isinstance(payload_value, int):
                # Direct integer value (common for binary/switch)
                value = bool(payload_value)
            else:
                value = payload_value

            # Track initial read completion
            was_initial = group_address in self._initial_read_pending
            if was_initial:
                self._initial_read_pending.discard(group_address)

            telegram_type = (
                "Response" if isinstance(telegram.payload, GroupValueResponse) else "Write"
            )

            # Determine sensor type emoji and label for DPT 9.xxx floats
            sensor_emoji = ""
            sensor_label = ""
            if isinstance(value, float):
                # Try to get known sensor type from entity mapping first
                detected_type = self._ga_sensor_type_map.get(group_address)
                if not detected_type:
                    # Fallback to value-based heuristic for unknown addresses
                    detected_type = self._detect_sensor_type(value)

                type_info = {
                    "temperature": ("🌡️", "Temperature", "°C", 1),
                    "humidity": ("💧", "Humidity", "%", 1),
                    "illuminance": ("☀️", "Illuminance", "lx", 1),
                    "pressure": ("🌪️", "Pressure", "hPa", 100),  # Convert Pa to hPa
                    "wind_speed": ("🌬️", "Wind", "m/s", 1),
                    "generic_sensor": ("📊", "Sensor", "", 1),
                }
                emoji, label, unit, divisor = type_info.get(detected_type, ("📊", "Sensor", "", 1))
                sensor_emoji = emoji
                display_value = value / divisor
                sensor_label = (
                    f"{label}: {display_value:.1f}{unit}"
                    if unit
                    else f"{label}: {display_value:.1f}"
                )

            # Log DPT 9.xxx float telegrams at INFO level for monitoring
            if isinstance(value, float):
                _LOGGER.info(
                    "%s KNX %s %s → %s (%s)",
                    sensor_emoji,
                    sensor_label,
                    source_address,
                    group_address,
                    telegram_type,
                )
            else:
                _LOGGER.debug(
                    "KNX Telegram: %s → %s = %s (%s)",
                    source_address,
                    group_address,
                    value,
                    telegram_type,
                )
            # Enrich with labels if known
            labels = self._ga_label_map.get(group_address)
            labels_str = f" | {', '.join(labels)}" if labels else ""
            # Source device enrichment via individual address
            try:
                source_addr = str(telegram.source_address)
            except Exception as err:
                _LOGGER.debug("Could not stringify telegram source address: %s", err)
                source_addr = "?"
            src_labels = self._ia_label_map.get(source_addr)
            src_str = (
                f" ← from {source_addr} ({', '.join(src_labels)})"
                if src_labels
                else f" ← from {source_addr}"
            )
            _LOGGER.info(
                "📥 Received KNX %s: %s=%s (DPT: %s)%s%s%s",
                telegram_type,
                group_address,
                value,
                type(payload_value).__name__,
                " ✅ INITIAL READ RESPONSE" if was_initial else "",
                labels_str,
                src_str,
            )

            # Notify listeners
            if group_address in self._listeners:
                # Create snapshot to avoid modification during iteration
                callbacks = list(self._listeners[group_address])
                _LOGGER.debug(
                    "🔔 Notifying %d listener(s) for address %s", len(callbacks), group_address
                )
                for callback in callbacks:
                    # Check if still registered (could be removed during iteration)
                    if callback not in self._listeners.get(group_address, []):
                        continue
                    try:
                        # Ensure callbacks run in HA event loop thread to avoid thread-safety issues.
                        # In tests or simulation, hass may not provide a loop; fallback to direct call.
                        loop = getattr(self.hass, "loop", None)
                        call_in_loop = getattr(loop, "call_soon_threadsafe", None) if loop else None
                        if callable(call_in_loop):
                            call_in_loop(callback, group_address, value)
                        else:
                            callback(group_address, value)
                    except Exception as err:
                        _LOGGER.error(
                            "Error scheduling listener callback for %s: %s",
                            group_address,
                            err,
                        )

                # Auto-discovery: Track DPT 9.xxx values in sensor range (exclude known LXP addresses)
                if (
                    isinstance(value, float)
                    and group_address not in self._discovered_sensors
                    and group_address not in self._known_addresses
                ):
                    await self._process_discovery_candidate(group_address, value)

        except Exception as err:
            _LOGGER.error("Error processing incoming telegram: %s", err, exc_info=True)

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
        try:
            # Normalize value similar to _telegram_received_callback
            processed_value = value

            # If explicit type provided, coerce accordingly
            if value_type == "binary" or isinstance(value, bool):
                processed_value = bool(value)
            elif value_type == "percent":
                # Coerce to int percentage robustly; handle unexpected value types
                if isinstance(value, (int, float, str)):
                    try:
                        processed_value = int(float(value))
                    except (TypeError, ValueError):
                        processed_value = 0
                else:
                    processed_value = 0
            elif isinstance(value, (list, tuple, bytes)) and len(value) == 2:
                # Attempt to decode 2-byte float
                try:
                    processed_value = DPT2ByteFloat().from_knx(DPTArray(value))
                except Exception as err:
                    _LOGGER.debug("DPT2ByteFloat decode failed for %r: %s", value, err)
                    processed_value = value
            elif isinstance(value, int):
                # Preserve integer semantics (e.g., 0/1 for binary)
                processed_value = bool(value) if value in (0, 1) else value
            # else leave as-is (float, DPTArray-like, etc.)

            # Log incoming push
            _LOGGER.info("📥 External push: %s = %s", group_address, processed_value)

            # Notify listeners if any
            if group_address in self._listeners:
                callbacks = list(self._listeners[group_address])
                for callback in callbacks:
                    if callback not in self._listeners.get(group_address, []):
                        continue
                    try:
                        loop = getattr(self.hass, "loop", None)
                        call_in_loop = getattr(loop, "call_soon_threadsafe", None) if loop else None
                        if callable(call_in_loop):
                            call_in_loop(callback, group_address, processed_value)
                        else:
                            callback(group_address, processed_value)
                    except Exception as err:
                        _LOGGER.error(
                            "Error scheduling listener callback for pushed value %s: %s",
                            group_address,
                            err,
                        )

            # Run discovery logic for float values
            if isinstance(processed_value, float) and group_address not in self._known_addresses:
                await self._process_discovery_candidate(group_address, processed_value)

        except Exception as err:
            _LOGGER.error("Error processing incoming pushed value: %s", err, exc_info=True)

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

    async def _process_discovery_candidate(self, group_address: str, value: float) -> None:
        """
        Process a potential auto-discovery candidate.

        Track DPT 9.xxx float values and create sensors after stable readings.

        Args:
            group_address: KNX group address (e.g., "5/1/10")
            value: Converted float value
        """
        # Skip if address is known from LXP
        if group_address in self._known_addresses:
            return

        # Skip if already discovered
        if group_address in self._discovered_sensors:
            return

        now = datetime.now()

        # Add to candidates
        self._discovery_candidates[group_address].append((value, now))

        # Keep only recent samples (last 10 minutes) AND limit max samples per address
        cutoff = now.timestamp() - 600
        self._discovery_candidates[group_address] = [
            (v, t) for v, t in self._discovery_candidates[group_address] if t.timestamp() > cutoff
        ][
            -DISCOVERY_MAX_CANDIDATES_PER_ADDRESS:
        ]  # Keep only last N samples (prevent memory leak)

        # Check if we have enough stable samples
        samples = self._discovery_candidates[group_address]
        if len(samples) < DISCOVERY_MIN_SAMPLES:
            return

        # Check value stability (last N samples within tolerance)
        recent_values = [v for v, _ in samples[-DISCOVERY_MIN_SAMPLES:]]
        avg_value = sum(recent_values) / len(recent_values)
        max_deviation = max(abs(v - avg_value) for v in recent_values)

        if max_deviation > DISCOVERY_VALUE_TOLERANCE:
            _LOGGER.debug(
                "Discovery candidate %s unstable: deviation=%.2f (samples=%s)",
                group_address,
                max_deviation,
                recent_values,
            )
            return

        # Stable sensor detected! Determine type based on value range
        sensor_type = self._detect_sensor_type(avg_value)

        sensor_info = {
            "address": group_address,
            "type": sensor_type,
            "last_value": value,
            "discovered_at": now.isoformat(),
            "sample_count": len(samples),
        }

        self._discovered_sensors[group_address] = sensor_info

        _LOGGER.info(
            "🔍 Auto-discovered sensor: %s (%s) = %.2f", group_address, sensor_type, avg_value
        )

        # Add to pending discoveries (debounced callback)
        self._pending_discoveries.append(sensor_info)

        # Trigger debounced callback
        await self._trigger_debounced_callbacks()

    def _detect_sensor_type(self, value: float) -> str:
        """
        Detect sensor type based on value range.

        DPT 9.xxx subtypes:
        - Temperature: -273..+670°C (typical: -50..+50°C)
        - Lux: 0..670760 lux (typical: 0..100000)
        - Humidity: 0..100% (exact)
        - Pressure: 0..14000 Pa (typical: 95000..110000 Pa)
        - Wind: 0..670 m/s
        """
        # Pressure: Usually in Pa range (95000-110000 Pa for atmospheric pressure)
        if 90000 <= value <= 120000:
            return "pressure"
        # Illuminance: Large positive values (>150)
        elif value > 150:
            return "illuminance"
        # Humidity: 0-100% range, typically with decimals
        elif 0 <= value <= 100 and value > 50:  # Over 50 more likely humidity than temperature
            return "humidity"
        # Temperature: -50 to +50°C typical range
        elif -50 <= value <= 50:
            return "temperature"
        # Fallback
        else:
            return "generic_sensor"

    def register_discovery_callback(self, callback: Callable[[dict], None]) -> None:
        """Register a callback for when new sensors are discovered."""
        self._discovery_callbacks.append(callback)

    def get_discovered_sensors(self) -> dict[str, dict[str, Any]]:
        """Return all discovered sensors."""
        return self._discovered_sensors.copy()

    def load_discovered_sensors(self, sensors: dict[str, dict[str, Any]]) -> None:
        """Load previously discovered sensors (e.g., from config entry)."""
        self._discovered_sensors = sensors.copy()
        _LOGGER.info("Loaded %d discovered sensors from storage", len(sensors))

    def set_known_addresses(self, addresses: set[str]) -> None:
        """Set known LXP addresses to exclude from auto-discovery."""
        self._known_addresses = addresses
        _LOGGER.info(
            "Registered %d known LXP addresses (excluded from auto-discovery)", len(addresses)
        )

    def set_sensor_types(self, sensor_types: dict[str, str]) -> None:
        """Set known sensor types for accurate logging (e.g., {'5/0/3': 'illuminance'})."""
        self._ga_sensor_type_map = sensor_types
        _LOGGER.debug("Registered %d sensor type mappings", len(sensor_types))

    async def _trigger_debounced_callbacks(self) -> None:
        """Trigger discovery callbacks with debouncing to prevent reload loops."""
        # Cancel existing debounce task
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        # Schedule new debounced task
        self._debounce_task = asyncio.create_task(self._execute_debounced_callbacks())

    async def _execute_debounced_callbacks(self) -> None:
        """Execute callbacks after debounce delay."""
        try:
            await asyncio.sleep(self.discovery_timeout)

            # Process all pending discoveries in one batch
            if self._pending_discoveries:
                discoveries = self._pending_discoveries.copy()
                self._pending_discoveries.clear()

                _LOGGER.info(
                    "🚀 Triggering callbacks for %d discovered sensors (debounced)",
                    len(discoveries),
                )

                for sensor_info in discoveries:
                    for callback in self._discovery_callbacks:
                        try:
                            callback(sensor_info)
                        except Exception as err:
                            _LOGGER.error("Error in discovery callback: %s", err)
        except asyncio.CancelledError:
            _LOGGER.debug("Debounce task cancelled (new discoveries incoming)")
