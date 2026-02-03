"""Auto-discovery engine for KNX sensors."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable

_LOGGER = logging.getLogger(__name__)

# Auto-discovery configuration
DISCOVERY_MIN_SAMPLES = 3  # Minimum stable readings before creating sensor
DISCOVERY_VALUE_TOLERANCE = 0.5  # Maximum value deviation for stability
DISCOVERY_MAX_CANDIDATES_PER_ADDRESS = 20  # Prevent memory leak: max samples per address
DISCOVERY_DEBOUNCE_DELAY = 2.0  # Seconds to wait before triggering reload (batch discoveries)


class DiscoveryEngine:
    """Manages auto-discovery of KNX sensors."""

    def __init__(self, discovery_timeout: float = DISCOVERY_DEBOUNCE_DELAY) -> None:
        """Initialize the discovery engine.

        Args:
            discovery_timeout: Debounce delay for discovery callbacks
        """
        self.discovery_timeout = discovery_timeout
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
        self._ga_sensor_type_map: dict[str, str] = {}  # {address: sensor_type} for known entities

    async def process_discovery_candidate(self, group_address: str, value: float) -> None:
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
            "Auto-discovered sensor: %s (%s) = %.2f", group_address, sensor_type, avg_value
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
                    "Triggering callbacks for %d discovered sensors (debounced)",
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
