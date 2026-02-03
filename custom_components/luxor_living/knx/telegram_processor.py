"""Telegram processing for KNX gateway."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from xknx.dpt import DPTArray, DPTBinary
from xknx.dpt.dpt_9 import DPT2ByteFloat
from xknx.telegram import Telegram
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class TelegramProcessor:
    """Processes incoming and outgoing KNX telegrams."""

    def __init__(
        self,
        hass: HomeAssistant,
        listener_manager: Any,
        discovery_engine: Any,
    ) -> None:
        """Initialize the telegram processor.

        Args:
            hass: Home Assistant instance
            listener_manager: ListenerManager instance for callback notifications
            discovery_engine: DiscoveryEngine instance for auto-discovery
        """
        self.hass = hass
        self._listener_manager = listener_manager
        self._discovery_engine = discovery_engine
        self._initial_read_pending: set[str] = set()

    async def telegram_received_callback(self, telegram: Telegram) -> None:
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
                    except Exception:
                        value = raw_value
                else:
                    # Unknown DPT - return raw value
                    value = raw_value
            elif isinstance(payload_value, (list, tuple)) and len(payload_value) == 2:
                # Some telegrams surface the raw tuple directly, handle as 2-byte float
                try:
                    # Create DPTArray from raw tuple for conversion
                    value = DPT2ByteFloat().from_knx(DPTArray(payload_value))
                except Exception:
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
                detected_type = self._discovery_engine._ga_sensor_type_map.get(group_address)
                if not detected_type:
                    # Fallback to value-based heuristic for unknown addresses
                    detected_type = self._discovery_engine._detect_sensor_type(value)

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
            labels = self._listener_manager.get_group_address_labels(group_address)
            labels_str = f" | {', '.join(labels)}" if labels else ""
            # Source device enrichment via individual address
            try:
                source_addr = str(telegram.source_address)
            except Exception:
                source_addr = "?"
            src_labels = self._listener_manager.get_individual_address_labels(source_addr)
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
            listeners = self._listener_manager.get_listeners(group_address)
            if listeners:
                # Create snapshot to avoid modification during iteration
                callbacks = list(listeners)
                _LOGGER.debug(
                    "🔔 Notifying %d listener(s) for address %s", len(callbacks), group_address
                )
                for callback in callbacks:
                    # Check if still registered (could be removed during iteration)
                    if callback not in self._listener_manager.get_listeners(group_address):
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
                if isinstance(value, float):
                    await self._discovery_engine.process_discovery_candidate(group_address, value)

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
            # Normalize value similar to telegram_received_callback
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
                except Exception:
                    processed_value = value
            elif isinstance(value, int):
                # Preserve integer semantics (e.g., 0/1 for binary)
                processed_value = bool(value) if value in (0, 1) else value
            # else leave as-is (float, DPTArray-like, etc.)

            # Log incoming push
            _LOGGER.info("📥 External push: %s = %s", group_address, processed_value)

            # Notify listeners if any
            listeners = self._listener_manager.get_listeners(group_address)
            if listeners:
                callbacks = list(listeners)
                for callback in callbacks:
                    if callback not in self._listener_manager.get_listeners(group_address):
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
            if isinstance(processed_value, float):
                await self._discovery_engine.process_discovery_candidate(
                    group_address, processed_value
                )

        except Exception as err:
            _LOGGER.error("Error processing incoming pushed value: %s", err, exc_info=True)

    def track_initial_read(self, group_address: str) -> None:
        """Track that an initial read is pending for a group address."""
        self._initial_read_pending.add(group_address)

    def clear_initial_read(self, group_address: str) -> None:
        """Clear initial read tracking for a group address."""
        self._initial_read_pending.discard(group_address)

    @property
    def pending_initial_reads(self) -> int:
        """Return count of pending initial reads."""
        return len(self._initial_read_pending)
