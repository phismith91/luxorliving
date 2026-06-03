"""Extended tests for coordinator.py covering uncovered error branches."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.luxor_living.coordinator import LuxorLivingCoordinator
from custom_components.luxor_living.rest_client import AuthenticationError


def _make_coordinator():
    hass = MagicMock()
    gateway = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    coord = LuxorLivingCoordinator(hass, gateway, entry, scan_interval=30)
    coord.async_set_updated_data = MagicMock()
    return coord


class TestAsyncUpdateData:
    @pytest.mark.asyncio
    async def test_success_returns_state_cache(self):
        coord = _make_coordinator()
        result = await coord._async_update_data()
        assert result == {}

    @pytest.mark.asyncio
    async def test_success_resets_auth_failures(self):
        coord = _make_coordinator()
        coord._auth_failures = 2
        await coord._async_update_data()
        assert coord._auth_failures == 0

    @pytest.mark.asyncio
    async def test_auth_error_increments_counter(self):
        coord = _make_coordinator()
        coord._state_cache = MagicMock()
        coord._state_cache.update.side_effect = AuthenticationError("bad creds")
        with pytest.raises(UpdateFailed, match="Authentication error"):
            await coord._async_update_data()
        assert coord._auth_failures == 1

    @pytest.mark.asyncio
    async def test_auth_error_raises_update_failed(self):
        coord = _make_coordinator()
        coord._state_cache = MagicMock()
        coord._state_cache.update.side_effect = AuthenticationError("bad creds")
        with pytest.raises(UpdateFailed):
            await coord._async_update_data()

    @pytest.mark.asyncio
    async def test_auth_error_triggers_repair_after_3_failures(self):
        coord = _make_coordinator()
        coord._auth_failures = 2
        coord._state_cache = MagicMock()
        coord._state_cache.update.side_effect = AuthenticationError("bad creds")

        with patch(
            "custom_components.luxor_living.repairs.create_auth_repair_issue",
            new_callable=AsyncMock,
        ) as mock_repair:
            with pytest.raises(UpdateFailed):
                await coord._async_update_data()
            mock_repair.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generic_exception_raises_update_failed(self):
        coord = _make_coordinator()
        coord._state_cache = MagicMock()
        coord._state_cache.update.side_effect = RuntimeError("unexpected error")
        with pytest.raises(UpdateFailed, match="Error fetching"):
            await coord._async_update_data()


@pytest.mark.smoke
class TestGetSetState:
    def test_get_state_returns_none_for_unknown(self):
        coord = _make_coordinator()
        assert coord.get_state("1/0/0") is None

    def test_set_state_stores_value(self):
        coord = _make_coordinator()
        coord.set_state("1/0/0", True)
        assert coord.get_state("1/0/0") is True

    def test_set_state_calls_async_set_updated_data(self):
        coord = _make_coordinator()
        coord.set_state("1/0/0", 42)
        coord.async_set_updated_data.assert_called_once()

    def test_set_state_updates_existing_value(self):
        coord = _make_coordinator()
        coord.set_state("1/0/0", True)
        coord.set_state("1/0/0", False)
        assert coord.get_state("1/0/0") is False


class TestCoordinatorMutationTargets:
    """Smoke tests targeting surviving mutants in coordinator.__init__ and set_state."""

    # ── __init__ parameter mutations ──────────────────────────────────────

    @pytest.mark.smoke
    def test_default_scan_interval_is_30(self):
        """Kill mutmut_1: scan_interval default 30 → 31."""
        import inspect

        from custom_components.luxor_living.coordinator import LuxorLivingCoordinator

        sig = inspect.signature(LuxorLivingCoordinator.__init__)
        assert sig.parameters["scan_interval"].default == 30

    @pytest.mark.smoke
    def test_coordinator_name_is_luxor_living(self):
        """Kill mutmut_4: name='Luxor Living' → name=None."""
        coord = _make_coordinator()
        assert coord.name == "Luxor Living"

    @pytest.mark.smoke
    def test_update_interval_matches_scan_interval(self):
        """Kill mutmut_5: update_interval=timedelta(seconds=scan) → None."""
        from datetime import timedelta

        coord = _make_coordinator()
        assert coord.update_interval == timedelta(seconds=30)

    # ── set_state: async_set_updated_data argument ────────────────────────

    @pytest.mark.smoke
    def test_set_state_passes_cache_not_none(self):
        """Kill mutmut_2: async_set_updated_data(self._state_cache) → (None)."""
        coord = _make_coordinator()
        coord.set_state("2/0/0", 42)

        coord.async_set_updated_data.assert_called_once()
        call_arg = coord.async_set_updated_data.call_args[0][0]
        assert call_arg is not None
        assert call_arg["2/0/0"] == 42
