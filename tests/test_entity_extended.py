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


@pytest.mark.smoke
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


@pytest.mark.smoke
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

    def test_device_info_model_is_luxorliving(self):
        """Kill: model='LUXORliving' → None mutation."""
        entity = _make_entity()
        assert entity.device_info["model"] == "LUXORliving"

    def test_device_info_identifiers_contains_device_id(self):
        """Kill: device_id key in identifiers → wrong key."""
        entity = _make_entity()
        ids = entity.device_info["identifiers"]
        assert any(v == "device_001" for _, v in ids)


@pytest.mark.smoke
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


@pytest.mark.smoke
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

    def test_boundary_59s_is_seconds_not_minutes(self):
        """Kill: < 60 → < 59 boundary mutation."""
        result = LuxorLivingEntity._decode_time_parameter("0000E678")  # 59000ms = 59s
        assert "s" in result
        assert "min" not in result

    def test_boundary_60s_is_minutes_not_seconds(self):
        """Kill: < 60 → < 61 boundary mutation."""
        result = LuxorLivingEntity._decode_time_parameter("0000EA60")  # 60000ms = 60s
        assert "min" in result
        assert result.startswith("1.0")

    def test_boundary_3599s_is_minutes_not_hours(self):
        """Kill: < 3600 → < 3599 boundary mutation."""
        result = LuxorLivingEntity._decode_time_parameter("0036E9B8")  # 3599000ms = 3599s
        assert "min" in result
        assert "h" not in result

    def test_boundary_3600s_is_hours_not_minutes(self):
        """Kill: < 3600 → < 3601 boundary mutation."""
        result = LuxorLivingEntity._decode_time_parameter("0036EE80")  # 3600000ms = 3600s = 1h
        assert "h" in result
        assert result.startswith("1.0")


@pytest.mark.smoke
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

    def test_cellar_timer(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"kellerlichtzeit": "00007530"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert "cellar_timer" in result

    def test_delay_on(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"einschaltverzögerung": "00007530"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert "delay_on" in result

    def test_delay_off(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"ausschaltverzögerung": "00007530"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert "delay_off" in result

    def test_switch_off_warning_true(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"ausschaltvorwarnung": "true"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("switch_off_warning") is True

    def test_switch_off_warning_false(self):
        entity = _make_entity()
        entity._mapped_entity.parameters = {"ausschaltvorwarnung": "false"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("switch_off_warning") is False


@pytest.mark.smoke
class TestEntityMutationTargets2:
    """Kill surviving entity.py mutants identified in round-2 analysis."""

    def test_attr_translation_key_is_none_not_empty(self):
        """Kill: _attr_translation_key = None → ''."""
        entity = _make_entity()
        assert entity._attr_translation_key is None

    def test_unique_id_default_is_unknown_when_attr_missing(self):
        """Kill: getattr(mapped_entity, 'unique_id', 'unknown') → default=None."""
        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.async_add_listener = MagicMock(return_value=lambda: None)
        config_entry = MagicMock()
        config_entry.runtime_data = None
        # Use an object with no unique_id attribute at all
        mapped_entity = MagicMock(
            spec=["name", "device_name", "device_id", "parameters", "attributes"]
        )
        mapped_entity.device_name = "Dev"
        mapped_entity.device_id = "d1"
        mapped_entity.parameters = {}
        mapped_entity.attributes = {}
        entity = LuxorLivingEntity(coordinator, config_entry, mapped_entity)
        assert entity._attr_unique_id == "unknown"

    def test_config_entry_stored_not_none(self):
        """Kill: super().__init__(coordinator, None, mapped_entity) in subclasses."""
        entity = _make_entity()
        assert entity._config_entry is not None

    @pytest.mark.asyncio
    async def test_async_added_calls_listener_with_handler(self):
        """Kill: async_add_listener(None) instead of _handle_coordinator_update."""
        entity = _make_entity()
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        call_args = entity.coordinator.async_add_listener.call_args[0]
        assert call_args[0] == entity._handle_coordinator_update

    @pytest.mark.asyncio
    async def test_async_added_passes_cleanup_to_on_remove(self):
        """Kill: async_on_remove(None) instead of the listener cleanup fn."""
        entity = _make_entity()
        cleanup_fn = MagicMock()
        entity.coordinator.async_add_listener = MagicMock(return_value=cleanup_fn)
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        entity.async_on_remove.assert_called_once_with(cleanup_fn)

    @pytest.mark.asyncio
    async def test_async_added_no_refresh_when_success_is_none(self):
        """Kill: 'is False' → 'is not False' (None would wrongly trigger refresh)."""
        entity = _make_entity(last_update_success=True)
        entity.coordinator.last_update_success = None
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        entity.coordinator.async_request_refresh.assert_not_awaited()

    def test_raise_if_unavailable_error_uses_domain(self):
        """Kill: translation_domain=None/removed mutations."""
        from custom_components.luxor_living.const import DOMAIN

        entity = _make_entity(connected=False)
        with pytest.raises(HomeAssistantError) as exc_info:
            entity._raise_if_unavailable()
        assert exc_info.value.translation_domain == DOMAIN

    def test_raise_if_unavailable_error_key_exact(self):
        """Kill: translation_key='ENTITY_UNAVAILABLE'/'XXentity_unavailableXX' mutations."""
        entity = _make_entity(connected=False)
        with pytest.raises(HomeAssistantError) as exc_info:
            entity._raise_if_unavailable()
        assert exc_info.value.translation_key == "entity_unavailable"

    def test_no_icon_type_when_off_icon_is_default_off(self):
        """Kill: 'Default_OFF' string → 'XXDefault_OFFXX'/'default_off' mutations."""
        entity = _make_entity()
        entity._mapped_entity.parameters = {"dummy": "x"}
        entity._mapped_entity.attributes = {"on_icon": "Default_ON", "off_icon": "Default_OFF"}
        result = entity._get_parameter_attributes()
        assert "icon_type" not in result

    def test_no_icon_type_when_off_icon_is_empty_string(self):
        """Kill: 'and' → 'or' in 'elif off_icon and off_icon != ...' mutation."""
        entity = _make_entity()
        entity._mapped_entity.parameters = {"dummy": "x"}
        entity._mapped_entity.attributes = {"on_icon": "Default_ON", "off_icon": ""}
        result = entity._get_parameter_attributes()
        assert "icon_type" not in result

    def test_staircase_timer_is_decoded_string_not_none(self):
        """Kill: staircase_timer = None / _decode_time_parameter(None) mutations."""
        entity = _make_entity()
        entity._mapped_entity.parameters = {"treppenlichtzeit": "00007530"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("staircase_timer") is not None
        assert isinstance(result["staircase_timer"], str)

    def test_cellar_timer_is_decoded_string_not_none(self):
        """Kill: cellar_timer = None / _decode_time_parameter(None) mutations."""
        entity = _make_entity()
        entity._mapped_entity.parameters = {"kellerlichtzeit": "00007530"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("cellar_timer") is not None
        assert isinstance(result["cellar_timer"], str)

    def test_delay_on_is_decoded_string_not_none(self):
        """Kill: delay_on = None / _decode_time_parameter(None) mutations."""
        entity = _make_entity()
        entity._mapped_entity.parameters = {"einschaltverzögerung": "00007530"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("delay_on") is not None
        assert isinstance(result["delay_on"], str)

    def test_delay_off_is_decoded_string_not_none(self):
        """Kill: delay_off = None / _decode_time_parameter(None) mutations."""
        entity = _make_entity()
        entity._mapped_entity.parameters = {"ausschaltverzögerung": "00007530"}
        entity._mapped_entity.attributes = {}
        result = entity._get_parameter_attributes()
        assert result.get("delay_off") is not None
        assert isinstance(result["delay_off"], str)
