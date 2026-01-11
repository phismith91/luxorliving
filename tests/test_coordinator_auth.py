"""Unit tests for LuxorLivingCoordinator authentication and error handling."""

from datetime import timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.luxor_living.coordinator import LuxorLivingCoordinator


@pytest.fixture
def mock_gateway():
    """Create a mock KNX gateway."""
    gateway = Mock()
    gateway.get_datapoint = AsyncMock(return_value={"value": 1})
    return gateway


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.entry_id = "test_entry"
    entry.title = "Test LUXORliving"
    return entry


@pytest.fixture
def mock_hass():
    """Create a minimal mock Home Assistant instance."""
    hass = Mock()
    hass.data = {}
    return hass


@pytest.fixture
def coordinator(mock_hass, mock_gateway, mock_entry):
    """Create a coordinator instance."""
    return LuxorLivingCoordinator(
        hass=mock_hass,
        gateway=mock_gateway,
        entry=mock_entry,
        scan_interval=30,
    )


class TestCoordinatorAuthFailures:
    """Test coordinator authentication failure handling."""

    @pytest.mark.asyncio
    async def test_coordinator_initializes_with_zero_auth_failures(
        self, coordinator: LuxorLivingCoordinator
    ):
        """Coordinator starts with zero auth failures."""
        assert coordinator._auth_failures == 0

    @pytest.mark.asyncio
    async def test_coordinator_resets_auth_failures_on_success(
        self, coordinator: LuxorLivingCoordinator
    ):
        """Auth failure counter resets on successful update."""
        # Simulate 2 failures
        coordinator._auth_failures = 2

        # Successful update
        result = await coordinator._async_update_data()

        # Failure count reset
        assert coordinator._auth_failures == 0
        assert isinstance(result, dict)


class TestCoordinatorStateCache:
    """Test coordinator state cache management."""

    @pytest.mark.asyncio
    async def test_get_state_returns_cached_value(
        self, coordinator: LuxorLivingCoordinator
    ):
        """get_state returns cached value for known address."""
        coordinator._state_cache["1/2/3"] = 42
        assert coordinator.get_state("1/2/3") == 42

    @pytest.mark.asyncio
    async def test_get_state_returns_none_for_unknown_address(
        self, coordinator: LuxorLivingCoordinator
    ):
        """get_state returns None for unknown address."""
        assert coordinator.get_state("9/9/9") is None

    @pytest.mark.asyncio
    async def test_set_state_updates_cache(self, coordinator: LuxorLivingCoordinator):
        """set_state updates the state cache."""
        coordinator.set_state("1/2/3", 100)
        assert coordinator._state_cache["1/2/3"] == 100

    @pytest.mark.asyncio
    async def test_set_state_triggers_update_event(
        self, coordinator: LuxorLivingCoordinator
    ):
        """set_state triggers coordinator update event."""
        with patch.object(coordinator, "async_set_updated_data") as mock_update:
            coordinator.set_state("1/2/3", 50)
            mock_update.assert_called_once_with(coordinator._state_cache)


class TestCoordinatorConfiguration:
    """Test coordinator configuration and setup."""

    @pytest.mark.asyncio
    async def test_coordinator_update_interval_configurable(
        self, mock_hass, mock_gateway, mock_entry
    ):
        """Coordinator accepts custom scan interval."""
        coordinator = LuxorLivingCoordinator(
            hass=mock_hass,
            gateway=mock_gateway,
            entry=mock_entry,
            scan_interval=60,  # Custom interval
        )

        assert coordinator._scan_interval == 60
        assert coordinator.update_interval == timedelta(seconds=60)

    @pytest.mark.asyncio
    async def test_coordinator_stores_gateway_reference(
        self, coordinator: LuxorLivingCoordinator, mock_gateway
    ):
        """Coordinator stores reference to KNX gateway."""
        assert coordinator.gateway == mock_gateway

    @pytest.mark.asyncio
    async def test_coordinator_stores_entry_reference(
        self, coordinator: LuxorLivingCoordinator, mock_entry
    ):
        """Coordinator stores reference to config entry."""
        assert coordinator.entry == mock_entry
