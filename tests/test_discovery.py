"""Tests for auto-discovery functionality."""

import asyncio
from unittest.mock import MagicMock

import pytest

from custom_components.luxor_living.knx_gateway import (
    DISCOVERY_DEBOUNCE_DELAY,
    DISCOVERY_MAX_CANDIDATES_PER_ADDRESS,
    DISCOVERY_MIN_SAMPLES,
    LuxorKNXGateway,
)


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    return hass


@pytest.fixture
def gateway(mock_hass):
    """Create a KNX gateway instance for testing."""
    return LuxorKNXGateway(
        hass=mock_hass,
        host="192.168.1.100",
        port=3671,
        username="test",
        password="test",
        http_port=8080,
        connection_type="tunneling",
        simulation_mode=True,
    )


class TestAutoDiscovery:
    """Test auto-discovery functionality."""

    @pytest.mark.asyncio
    async def test_discovery_requires_min_samples(self, gateway: LuxorKNXGateway):
        """Test that discovery requires minimum stable samples."""
        callback = MagicMock()
        gateway.register_discovery_callback(callback)

        # Send only 2 samples (below minimum)
        await gateway._process_discovery_candidate("5/1/10", 22.5)
        await gateway._process_discovery_candidate("5/1/10", 22.6)

        # Wait for potential debounce
        await asyncio.sleep(DISCOVERY_DEBOUNCE_DELAY + 0.5)

        # Should NOT trigger discovery (not enough samples)
        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_discovery_with_stable_samples(self, gateway: LuxorKNXGateway):
        """Test successful discovery with stable temperature samples."""
        callback = MagicMock()
        gateway.register_discovery_callback(callback)

        # Send 3 stable samples
        await gateway._process_discovery_candidate("5/1/10", 22.5)
        await gateway._process_discovery_candidate("5/1/10", 22.6)
        await gateway._process_discovery_candidate("5/1/10", 22.5)

        # Wait for debounce
        await asyncio.sleep(DISCOVERY_DEBOUNCE_DELAY + 0.5)

        # Should trigger discovery
        callback.assert_called_once()
        sensor_info = callback.call_args[0][0]
        assert sensor_info["address"] == "5/1/10"
        assert sensor_info["type"] == "temperature"

    @pytest.mark.asyncio
    async def test_discovery_rejects_unstable_samples(self, gateway: LuxorKNXGateway):
        """Test that unstable values don't trigger discovery."""
        callback = MagicMock()
        gateway.register_discovery_callback(callback)

        # Send unstable samples (deviation > 0.5)
        await gateway._process_discovery_candidate("5/1/10", 22.0)
        await gateway._process_discovery_candidate("5/1/10", 23.0)
        await gateway._process_discovery_candidate("5/1/10", 24.0)

        # Wait for potential debounce
        await asyncio.sleep(DISCOVERY_DEBOUNCE_DELAY + 0.5)

        # Should NOT trigger (unstable)
        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_sensor_type_detection_temperature(self, gateway: LuxorKNXGateway):
        """Test temperature sensor type detection."""
        assert gateway._detect_sensor_type(22.5) == "temperature"
        assert gateway._detect_sensor_type(-10.0) == "temperature"
        assert gateway._detect_sensor_type(35.0) == "temperature"

    @pytest.mark.asyncio
    async def test_sensor_type_detection_humidity(self, gateway: LuxorKNXGateway):
        """Test humidity sensor type detection."""
        assert gateway._detect_sensor_type(55.0) == "humidity"
        assert gateway._detect_sensor_type(80.0) == "humidity"

    @pytest.mark.asyncio
    async def test_sensor_type_detection_illuminance(self, gateway: LuxorKNXGateway):
        """Test illuminance sensor type detection."""
        assert gateway._detect_sensor_type(500.0) == "illuminance"
        assert gateway._detect_sensor_type(50000.0) == "illuminance"

    @pytest.mark.asyncio
    async def test_sensor_type_detection_pressure(self, gateway: LuxorKNXGateway):
        """Test pressure sensor type detection."""
        assert gateway._detect_sensor_type(101325.0) == "pressure"
        assert gateway._detect_sensor_type(100000.0) == "pressure"

    @pytest.mark.asyncio
    async def test_known_addresses_excluded(self, gateway: LuxorKNXGateway):
        """Test that known LXP addresses are excluded from discovery."""
        callback = MagicMock()
        gateway.register_discovery_callback(callback)

        # Mark address as known
        gateway.set_known_addresses({"5/0/2"})

        # Try to discover known address
        await gateway._process_discovery_candidate("5/0/2", 22.5)
        await gateway._process_discovery_candidate("5/0/2", 22.6)
        await gateway._process_discovery_candidate("5/0/2", 22.5)

        # Wait for potential debounce
        await asyncio.sleep(DISCOVERY_DEBOUNCE_DELAY + 0.5)

        # Should NOT trigger (known address)
        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self, gateway: LuxorKNXGateway):
        """Test that candidates are limited to prevent memory leak."""
        # Send more than MAX_CANDIDATES samples
        for i in range(DISCOVERY_MAX_CANDIDATES_PER_ADDRESS + 10):
            await gateway._process_discovery_candidate("5/1/10", 22.5 + (i * 0.01))

        # Check that samples are limited
        candidates = gateway._discovery_candidates["5/1/10"]
        assert len(candidates) <= DISCOVERY_MAX_CANDIDATES_PER_ADDRESS

        # Cancel pending debounce task — asyncio.create_task leaves it running
        # after the test body finishes, which causes "lingering task" errors in
        # strict asyncio environments (Python 3.14+).
        if gateway._debounce_task and not gateway._debounce_task.done():
            gateway._debounce_task.cancel()
            await asyncio.gather(gateway._debounce_task, return_exceptions=True)

    @pytest.mark.asyncio
    async def test_debouncing_batches_discoveries(self, gateway: LuxorKNXGateway):
        """Test that debouncing batches multiple discoveries into one callback."""
        callback = MagicMock()
        gateway.register_discovery_callback(callback)

        # Discover two sensors quickly
        for _ in range(DISCOVERY_MIN_SAMPLES):
            await gateway._process_discovery_candidate("5/1/10", 22.5)
            await gateway._process_discovery_candidate("5/1/11", 45.0)

        # Wait for debounce
        await asyncio.sleep(DISCOVERY_DEBOUNCE_DELAY + 0.5)

        # Should have called callback for both sensors
        assert callback.call_count == 2

    @pytest.mark.asyncio
    async def test_load_discovered_sensors(self, gateway: LuxorKNXGateway):
        """Test loading previously discovered sensors from storage."""
        sensors = {
            "5/1/10": {
                "address": "5/1/10",
                "type": "temperature",
                "last_value": 22.5,
                "discovered_at": "2025-12-26T20:00:00",
                "sample_count": 3,
            }
        }

        gateway.load_discovered_sensors(sensors)

        # Check that sensors were loaded
        discovered = gateway.get_discovered_sensors()
        assert "5/1/10" in discovered
        assert discovered["5/1/10"]["type"] == "temperature"

    @pytest.mark.asyncio
    async def test_get_discovered_sensors(self, gateway: LuxorKNXGateway):
        """Test retrieving discovered sensors."""
        callback = MagicMock()
        gateway.register_discovery_callback(callback)

        # Discover a sensor
        for _ in range(DISCOVERY_MIN_SAMPLES):
            await gateway._process_discovery_candidate("5/1/10", 22.5)

        # Wait for debounce
        await asyncio.sleep(DISCOVERY_DEBOUNCE_DELAY + 0.5)

        # Retrieve discovered sensors
        discovered = gateway.get_discovered_sensors()
        assert "5/1/10" in discovered
        assert discovered["5/1/10"]["type"] == "temperature"
