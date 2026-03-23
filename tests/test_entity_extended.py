"""Extended tests for entity.py covering uncovered branches."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.luxor_living.entity import LuxorLivingEntity


def _make_entity(connected=True, simulation_mode=False, last_update_success=True):
    """Create a LuxorLivingEntity with mocked dependencies."""
    coordinator = MagicMock()
    coordinator.last_update_success = last_update_success
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    coordinator.async_request_refresh = AsyncMock()

    config_entry = MagicMock()
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.knx_gateway = MagicMock()
    config_entry.runtime_data.knx_gateway.connected = connected
    config_entry.runtime_data.knx_gateway.simulation_mode = simulation_mode

    mapped_entity = MagicMock()
    mapped_entity.unique_id = "test_unique_id"
    mapped_entity.name = "Test Entity"
    mapped_entity.device_name = "Test Device"
    mapped_entity.device_id = "device_001"
    mapped_entity.parameters = {}
    mapped_entity.attributes = {}

    entity = LuxorLivingEntity(coordinator, config_entry, mapped_entity)
    return entity


class TestAvailability:
    def test_available_when_connected(self):
        entity = _make_entity(connected=True)
        assert entity.available is True

    def test_unavailable_when_disconnected(self):
        entity = _make_entity(connected=False)
        assert entity.available is False

    def test_available_in_simulation_mode_even_disconnected(self):
        entity = _make_entity(connected=False, simulation_mode=True)
        assert entity.available is True

    def test_unavailable_when_coordinator_failed(self):
        entity = _make_entity(connected=True, last_update_success=False)
        assert entity.available is False

    def test_available_when_no_runtime_data(self):
        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.async_add_listener = MagicMock(return_value=lambda: None)
        config_entry = MagicMock()
        config_entry.runtime_data = None
        mapped_entity = MagicMock()
        mapped_entity.unique_id = "x"
        mapped_entity.parameters = {}
        mapped_entity.attributes = {}
        entity = LuxorLivingEntity(coordinator, config_entry, mapped_entity)
        assert entity.available is True

    def test_available_when_no_knx_gateway(self):
        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.async_add_listener = MagicMock(return_value=lambda: None)
        config_entry = MagicMock()
        config_entry.runtime_data = MagicMock()
        config_entry.runtime_data.knx_gateway = None
        mapped_entity = MagicMock()
        mapped_entity.unique_id = "x"
        mapped_entity.parameters = {}
        mapped_entity.attributes = {}
        entity = LuxorLivingEntity(coordinator, config_entry, mapped_entity)
        assert entity.available is True


class TestDeviceInfo:
    def test_device_info_contains_domain(self):
        entity = _make_entity()
        info = entity.device_info
        domain_ids = [k[0] for k in info["identifiers"]]
        assert any("luxor" in d for d in domain_ids)

    def test_device_info_manufacturer(self):
        entity = _make_entity()
        assert entity.device_info["manufacturer"] == "Theben"

    def test_device_info_uses_mapped_entity_names(self):
        entity = _make_entity()
        assert entity.device_info["name"] == "Test Device"


class TestRaiseIfUnavailable:
    def test_raises_when_unavailable(self):
        entity = _make_entity(connected=False)
        with pytest.raises(HomeAssistantError):
            entity._raise_if_unavailable()

    def test_does_not_raise_when_available(self):
        entity = _make_entity(connected=True)
        entity._raise_if_unavailable()  # must not raise


class TestHandleCoordinatorUpdate:
    def test_handle_update_calls_write_ha_state(self):
        entity = _make_entity()
        entity.async_write_ha_state = MagicMock()
        entity._handle_coordinator_update()
        entity.async_write_ha_state.assert_called_once()


class TestAsyncUpdate:
    @pytest.mark.asyncio
    async def test_async_update_requests_refresh(self):
        entity = _make_entity()
        await entity.async_update()
        entity.coordinator.async_request_refresh.assert_awaited_once()


class TestAsyncAddedToHass:
    @pytest.mark.asyncio
    async def test_subscribes_to_coordinator(self):
        entity = _make_entity()
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        entity.coordinator.async_add_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_requests_refresh_when_coordinator_not_successful(self):
        entity = _make_entity(last_update_success=False)
        entity.coordinator.last_update_success = False
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        entity.coordinator.async_request_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_refresh_when_coordinator_successful(self):
        entity = _make_entity(last_update_success=True)
        entity.coordinator.last_update_success = True
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        entity.coordinator.async_request_refresh.assert_not_awaited()


class TestDecodeTimeParameter:
    def test_zero_returns_disabled(self):
        result = LuxorLivingEntity._decode_time_parameter("00000000")
        assert result == "disabled"

    def test_seconds(self):
        # 30000 ms = 30s → hex: 0x7530 = 30000
        result = LuxorLivingEntity._decode_time_parameter("00007530")
        assert "30" in result
        assert "s" in result

    def test_minutes(self):
        # 180000 ms = 3 min → hex: 0x2BF20 = 180000
        result = LuxorLivingEntity._decode_time_parameter("0002BF20")
        assert "min" in result

    def test_hours(self):
        # 7200000 ms = 2h → hex: 0x6DDD00 = 7200000
        result = LuxorLivingEntity._decode_time_parameter("006DDD00")
        assert "h" in result

    def test_short_string_returns_raw(self):
        result = LuxorLivingEntity._decode_time_parameter("abc")
        assert result == "abc"

    def test_invalid_hex_returns_raw(self):
        result = LuxorLivingEntity._decode_time_parameter("GGGGGGGG")
        assert result == "GGGGGGGG"


class TestGetParameterAttributes:
    def test_empty_parameters_returns_empty(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {}
        result = entity._get_parameter_attributes()
        assert result == {}

    def test_panic_flag_true(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"teilnahmePanik": "true"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("panic_enabled") is True

    def test_panic_flag_false(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"teilnahmePanik": "false"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("panic_enabled") is False

    def test_central_off_flag(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"teilnahmeZentralAus": "true"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("central_off_enabled") is True

    def test_on_icon(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"someParam": "val"}
        entity._mapped_entity.attributes = {"on_icon": "Ceiling_ON", "off_icon": ""}
        result = entity._get_parameter_attributes()
        assert result.get("icon_type") == "Ceiling_ON"

    def test_off_icon_fallback(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"x": "y"}
        entity._mapped_entity.attributes = {"on_icon": "Default_ON", "off_icon": "Lamp_OFF"}
        result = entity._get_parameter_attributes()
        assert result.get("icon_type") == "Lamp_OFF"

    def test_staircase_timer(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"treppenlichtzeit": "00007530"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert "staircase_timer" in result

    def test_impulse_count_valid(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"impulsAnzahl": "5"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("impulse_count") == 5

    def test_impulse_count_invalid_ignored(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"impulsAnzahl": "notanumber"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert "impulse_count" not in result
