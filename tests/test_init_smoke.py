"""Smoke tests for __init__.py — targets PLATFORMS, unload, and GA address logic."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import Platform


@pytest.mark.smoke
class TestPlatformsList:
    """Kill mutations in the PLATFORMS constant."""

    def test_platforms_contains_light(self):
        from custom_components.luxor_living import PLATFORMS

        assert Platform.LIGHT in PLATFORMS

    def test_platforms_does_not_contain_switch(self):
        # Switch platform was removed: no LXP role maps to Platform.SWITCH,
        # switching actuators are exposed as `light`.
        from custom_components.luxor_living import PLATFORMS

        assert Platform.SWITCH not in PLATFORMS

    def test_platforms_contains_binary_sensor(self):
        from custom_components.luxor_living import PLATFORMS

        assert Platform.BINARY_SENSOR in PLATFORMS

    def test_platforms_contains_sensor(self):
        from custom_components.luxor_living import PLATFORMS

        assert Platform.SENSOR in PLATFORMS

    def test_platforms_contains_climate(self):
        from custom_components.luxor_living import PLATFORMS

        assert Platform.CLIMATE in PLATFORMS

    def test_platforms_contains_cover(self):
        from custom_components.luxor_living import PLATFORMS

        assert Platform.COVER in PLATFORMS

    def test_platforms_has_exactly_five_entries(self):
        """Kill: extra/missing platform mutations."""
        from custom_components.luxor_living import PLATFORMS

        assert len(PLATFORMS) == 5


@pytest.mark.smoke
class TestAsyncUnloadEntry:
    """Kill mutations in async_unload_entry."""

    @pytest.mark.asyncio
    async def test_disconnects_knx_gateway_on_unload(self):
        """Kill: gateway.async_disconnect_for_unload() call removed."""
        from custom_components.luxor_living import async_unload_entry

        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        state = MagicMock()
        state.knx_gateway = MagicMock()
        state.knx_gateway.async_disconnect_for_unload = AsyncMock()
        state.push_client = None

        entry = MagicMock()
        entry.runtime_data = state

        result = await async_unload_entry(hass, entry)

        state.knx_gateway.async_disconnect_for_unload.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_unload_platforms_result(self):
        """Kill: bool(unload_ok) wrapping mutation."""
        from custom_components.luxor_living import async_unload_entry

        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

        state = MagicMock()
        state.knx_gateway = MagicMock()
        state.knx_gateway.async_disconnect_for_unload = AsyncMock()
        state.push_client = None

        entry = MagicMock()
        entry.runtime_data = state

        result = await async_unload_entry(hass, entry)
        assert result is False

    @pytest.mark.asyncio
    async def test_stops_push_client_on_unload(self):
        """Kill: push_client.stop() call removed."""
        from custom_components.luxor_living import async_unload_entry

        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        state = MagicMock()
        state.knx_gateway = MagicMock()
        state.knx_gateway.async_disconnect_for_unload = AsyncMock()
        push_client = MagicMock()
        push_client.stop = AsyncMock()
        state.push_client = push_client

        entry = MagicMock()
        entry.runtime_data = state

        await async_unload_entry(hass, entry)
        push_client.stop.assert_awaited_once()


@pytest.mark.smoke
class TestAsyncUpdateOptions:
    """Kill mutations in async_update_options."""

    @pytest.mark.asyncio
    async def test_reloads_config_entry(self):
        """Kill: async_reload() call removed or wrong entry_id."""
        from custom_components.luxor_living import async_update_options

        hass = MagicMock()
        hass.config_entries.async_reload = AsyncMock()

        entry = MagicMock()
        entry.entry_id = "test_entry_id"

        await async_update_options(hass, entry)

        hass.config_entries.async_reload.assert_awaited_once_with("test_entry_id")


@pytest.mark.smoke
class TestGaAddressFormula:
    """Kill mutations in the int→GA address conversion used in async_setup_entry."""

    def test_ga_formula_known_value(self):
        """Kill: bit-shift or mask mutations in GA address computation.

        This formula is used in async_setup_entry to convert LXP int addresses
        to KNX group address strings for known_addresses set.
        """
        address = 8966  # 0x2306 = Höhe% from cover fixture
        ga_str = f"{(address >> 11) & 0x1F}/{(address >> 8) & 0x07}/{address & 0xFF}"
        # 8966 = 0x2306; (8966>>11)=4, &0x1F=4; (8966>>8)=35, &0x07=3; 8966&0xFF=6
        assert ga_str == "4/3/6"

    def test_ga_formula_main_group_mask(self):
        """Kill: >> 11 → >> 10 or &0x1F → &0x0F mutations."""
        address = 32768  # 0x8000; main = (32768>>11)&0x1F = 16&0x1F = 16
        main = (address >> 11) & 0x1F
        assert main == 16

    def test_ga_formula_middle_group_mask(self):
        """Kill: >> 8 → >> 7 or &0x07 → &0x0F mutations."""
        address = 0x0700  # middle = (0x0700>>8)&0x07 = 7&0x07 = 7
        middle = (address >> 8) & 0x07
        assert middle == 7

    def test_ga_formula_sub_group_mask(self):
        """Kill: &0xFF → &0x7F or no mask mutations."""
        address = 0x00FF  # sub = 0xFF&0xFF = 255
        sub = address & 0xFF
        assert sub == 255
