"""Tests for LUXORliving light platform."""

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.coordinator import LuxorLivingCoordinator
from custom_components.luxor_living.knx_gateway import LuxorKNXGateway
from custom_components.luxor_living.light import (
    LuxorLivingDimmableLight,
    LuxorLivingLight,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def mock_coordinator():
    """Mock Data Coordinator."""
    coordinator = Mock(spec=LuxorLivingCoordinator)
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_add_listener = Mock(return_value=lambda: None)
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Mock Config Entry."""
    entry = Mock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {"host": "192.168.1.3"}
    return entry


@pytest.fixture
def mock_knx_gateway():
    """Mock KNX Gateway."""
    gateway = Mock(spec=LuxorKNXGateway)
    gateway.async_send_telegram = AsyncMock(return_value=True)
    gateway.async_read_group_address = AsyncMock(return_value=True)
    gateway.async_read_via_rest = AsyncMock(return_value=None)
    gateway.register_listener = Mock()
    gateway.unregister_listener = Mock()
    return gateway


@pytest.fixture
def mock_mapped_entity():
    """Mock mapped entity for light."""
    entity = Mock()
    entity.unique_id = "test_light_001"
    entity.name = "Test Light"
    entity.device_id = "device_001"
    entity.device_name = "Test Device"
    entity.entity_type = "switch_light"
    entity.datapoints = {
        "OnOff": "1/2/3",
        "StatusOnOff": "1/2/4",
    }
    return entity


@pytest.fixture
def mock_dimmable_entity():
    """Mock mapped entity for dimmable light."""
    entity = Mock()
    entity.unique_id = "test_dim_light_001"
    entity.name = "Test Dimmable Light"
    entity.device_id = "device_002"
    entity.device_name = "Test Dimmer"
    entity.entity_type = "dimmable_light"
    entity.datapoints = {
        "OnOff": "1/2/5",
        "StatusOnOff": "1/2/6",
        "Dimmen%": "1/2/7",
    }
    return entity


@pytest.mark.smoke
class TestLuxorLivingLight:
    """Test LuxorLivingLight class."""

    def test_init(self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway):
        """Test light initialization."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )

        assert light.coordinator == mock_coordinator
        assert light.is_on is False
        assert light._address_on == "1/2/3"
        assert light._address_status == "1/2/4"

        # Listeners are deferred to async_added_to_hass (event loop), so __init__
        # must compute the addresses but not register them yet.
        assert mock_knx_gateway.register_listener.call_count == 0
        assert set(light._listen_addresses) == {"1/2/3", "1/2/4"}

    @pytest.mark.asyncio
    async def test_async_added_to_hass(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test entity added to hass - should request initial state."""
        mock_knx_gateway._connected = True  # KNX is connected
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_on_remove = Mock(return_value=lambda: None)

        await light.async_added_to_hass()

        # Request current state from BOTH addresses
        assert mock_knx_gateway.async_read_group_address.call_count == 2

    @pytest.mark.asyncio
    async def test_turn_on(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test turning light on."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        await light.async_turn_on()

        mock_knx_gateway.async_send_telegram.assert_called_once()
        assert light.is_on is True

    @pytest.mark.asyncio
    async def test_turn_off(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test turning light off."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        await light.async_turn_off()

        mock_knx_gateway.async_send_telegram.assert_called_once()
        assert light.is_on is False

    def test_handle_knx_update(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test handling KNX status update."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        # Simulate KNX status update
        light._handle_knx_update("1/2/4", True)

        assert light.is_on is True

    @pytest.mark.asyncio
    async def test_will_remove_from_hass(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Test cleanup when entity is removed."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )

        await light.async_will_remove_from_hass()

        # Should unregister listeners
        assert mock_knx_gateway.unregister_listener.call_count >= 1


@pytest.mark.smoke
class TestLuxorLivingDimmableLight:
    """Test LuxorLivingDimmableLight class."""

    def test_init(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test dimmable light initialization."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )

        assert light.coordinator == mock_coordinator
        assert light.brightness == 255
        assert light._address_dim == "1/2/7"

    @pytest.mark.asyncio
    async def test_async_added_to_hass(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test dimmable light added to hass."""
        mock_knx_gateway._connected = True
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_on_remove = Mock(return_value=lambda: None)

        await light.async_added_to_hass()

        # Should request initial state
        assert mock_knx_gateway.async_read_group_address.call_count >= 2

    @pytest.mark.asyncio
    async def test_turn_on_with_brightness(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test turning on with specific brightness."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        await light.async_turn_on(brightness=128)

        mock_knx_gateway.async_send_telegram.assert_called_once()
        assert light.is_on is True

    def test_handle_brightness_update(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test handling KNX brightness update."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        # Simulate brightness update (50% = 50)
        light._handle_brightness_update("1/2/7", 50)

        assert light.is_on is True
        assert light.brightness == int(50 * 255 / 100)

    def test_handle_brightness_update_zero(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Test handling zero brightness update."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        # Simulate brightness update (0%)
        light._handle_brightness_update("1/2/7", 0)

        assert light.is_on is False
        assert light.brightness == 0


@pytest.mark.smoke
class TestLightRateLimiting:
    """Test rate limiting functionality for lights."""

    @pytest.fixture
    def light(self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway):
        """Create a light instance for testing."""
        return LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )

    def test_rate_limiting_not_triggered(self, light):
        """Test that rate limiting doesn't block normal usage."""
        # Should not be rate limited initially
        assert not light._is_rate_limited()
        assert not light._is_rate_limited()
        assert not light._is_rate_limited()
        assert not light._is_rate_limited()
        assert not light._is_rate_limited()

    def test_rate_limiting_triggered(self, light, monkeypatch):
        """Test that rate limiting blocks after 5 commands in 1 second."""
        import time

        # Mock time to control timestamps
        timestamps = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]  # 6 calls within 0.5s
        call_count = 0

        def mock_time():
            nonlocal call_count
            result = timestamps[min(call_count, len(timestamps) - 1)]
            call_count += 1
            return result

        monkeypatch.setattr(time, "time", mock_time)

        # First 5 calls should not be limited
        for i in range(5):
            assert not light._is_rate_limited(), f"Call {i+1} should not be limited"

        # 6th call should be limited
        assert light._is_rate_limited(), "6th call should be rate limited"

    @pytest.mark.asyncio
    async def test_turn_on_rate_limited(self, light, mock_knx_gateway):
        """Test that turn_on is blocked when rate limited."""
        # Trigger rate limiting
        for _ in range(6):
            light._is_rate_limited()

        # turn_on should not send telegram
        await light.async_turn_on()
        mock_knx_gateway.async_send_telegram.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_rate_limited(self, light, mock_knx_gateway):
        """Test that turn_off is blocked when rate limited."""
        # Trigger rate limiting
        for _ in range(6):
            light._is_rate_limited()

        # turn_off should not send telegram
        await light.async_turn_off()
        mock_knx_gateway.async_send_telegram.assert_not_called()


@pytest.mark.smoke
class TestLightMutationTargets:
    """Smoke tests targeting surviving mutants in LuxorLivingLight."""

    @pytest.mark.asyncio
    async def test_turn_on_sends_true_with_binary_type(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: send value True → False, type 'binary' → None."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()
        await light.async_turn_on()
        args = mock_knx_gateway.async_send_telegram.call_args[0]
        assert args[1] is True
        assert args[2] == "binary"

    @pytest.mark.asyncio
    async def test_turn_off_sends_false_with_binary_type(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: send value False → True, type 'binary' → None."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()
        await light.async_turn_off()
        args = mock_knx_gateway.async_send_telegram.call_args[0]
        assert args[1] is False
        assert args[2] == "binary"

    def test_fallback_address_on_from_schalten_onoff(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: 'OnOff' key mutation loses SchaltenOnOff fallback."""
        entity = Mock()
        entity.unique_id = "schalten_test"
        entity.name = "Schalten Light"
        entity.device_id = "dev1"
        entity.device_name = "Device 1"
        entity.entity_type = "switch_light"
        entity.datapoints = {"SchaltenOnOff": "2/3/4"}
        entity.parameters = {}
        entity.attributes = {}
        light = LuxorLivingLight(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert light._address_on == "2/3/4"

    def test_status_address_falls_back_to_status_at_onoff(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: 'StatusOnOff' key priority vs 'status@OnOff' fallback."""
        entity = Mock()
        entity.unique_id = "status_test"
        entity.name = "Status Light"
        entity.device_id = "dev1"
        entity.device_name = "Device 1"
        entity.entity_type = "switch_light"
        entity.datapoints = {"OnOff": "1/1/1", "status@OnOff": "1/1/2"}
        entity.parameters = {}
        entity.attributes = {}
        light = LuxorLivingLight(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        assert light._address_status == "1/1/2"

    def test_handle_knx_update_wrong_address_ignored(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: valid_addresses guard removed, any address updates state."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()
        light._handle_knx_update("9/9/9", True)
        assert light.is_on is False
        light.async_write_ha_state.assert_not_called()


@pytest.mark.smoke
class TestDimmableLightMutationTargets:
    """Smoke tests targeting surviving mutants in LuxorLivingDimmableLight."""

    @pytest.mark.asyncio
    async def test_turn_on_percent_conversion(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Kill: int(brightness * 100 / 255) arithmetic mutations."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()
        await light.async_turn_on(brightness=128)
        args = mock_knx_gateway.async_send_telegram.call_args[0]
        assert args[1] == int(128 * 100 / 255)
        assert args[2] == "percent"

    @pytest.mark.asyncio
    async def test_turn_on_full_brightness_sends_100_percent(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Kill: divisor 255 → 256 mutation."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()
        await light.async_turn_on(brightness=255)
        args = mock_knx_gateway.async_send_telegram.call_args[0]
        assert args[1] == 100

    def test_brightness_update_100_percent_maps_to_255(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Kill: int(value * 255 / 100) divisor/multiplier mutations."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()
        light._handle_brightness_update("1/2/7", 100)
        assert light.brightness == 255

    def test_brightness_update_zero_sets_is_on_false(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Kill: > 0 boundary mutation for is_on from brightness."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()
        light._handle_brightness_update("1/2/7", 0)
        assert light.is_on is False
        assert light.brightness == 0


@pytest.mark.smoke
class TestLightRegistrationMutants:
    """Kill surviving mutants about class attrs, super() args, register_listener, is_initial."""

    def test_color_mode_is_onoff(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: _attr_color_mode = ColorMode.ONOFF → None mutation."""
        from homeassistant.components.light import ColorMode

        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        assert light._attr_color_mode == ColorMode.ONOFF

    def test_supported_color_modes_contains_onoff(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: _attr_supported_color_modes = {ColorMode.ONOFF} → {} mutation."""
        from homeassistant.components.light import ColorMode

        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        assert ColorMode.ONOFF in light._attr_supported_color_modes

    def test_config_entry_stored_in_entity(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: super().__init__(coordinator, None, mapped_entity) mutation."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        assert light._config_entry is mock_config_entry

    def test_mapped_entity_stored_in_entity(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: super().__init__(coordinator, entry, None) mutation."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        assert light._mapped_entity is mock_mapped_entity

    @pytest.mark.asyncio
    async def test_register_listener_uses_real_addresses(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: register_listener(None, handler) mutations."""
        mock_knx_gateway._connected = True
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_on_remove = Mock(return_value=lambda: None)
        await light.async_added_to_hass()
        registered = [c[0][0] for c in mock_knx_gateway.register_listener.call_args_list]
        assert "1/2/3" in registered
        assert "1/2/4" in registered

    def test_listen_addresses_contain_real_addresses(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: _listen_addresses.append(None) mutation."""
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        assert "1/2/3" in light._listen_addresses
        assert "1/2/4" in light._listen_addresses

    @pytest.mark.asyncio
    async def test_same_address_not_registered_twice(
        self, mock_coordinator, mock_config_entry, mock_knx_gateway
    ):
        """Kill: _address_on != _address_status → or mutation (would register same addr twice)."""
        mock_knx_gateway._connected = True
        entity = Mock()
        entity.unique_id = "same_addr"
        entity.name = "Same Addr Light"
        entity.device_id = "d1"
        entity.device_name = "Dev"
        entity.entity_type = "switch_light"
        entity.datapoints = {"OnOff": "1/1/1", "StatusOnOff": "1/1/1"}  # same address!
        entity.parameters = {}
        entity.attributes = {}
        light = LuxorLivingLight(mock_coordinator, mock_config_entry, entity, mock_knx_gateway)
        light.async_on_remove = Mock(return_value=lambda: None)
        await light.async_added_to_hass()
        assert mock_knx_gateway.register_listener.call_count == 1

    @pytest.mark.asyncio
    async def test_async_added_reads_with_is_initial_true(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        """Kill: is_initial=True → is_initial=False mutation."""
        mock_knx_gateway._connected = True
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_on_remove = Mock(return_value=lambda: None)
        await light.async_added_to_hass()
        for call in mock_knx_gateway.async_read_group_address.call_args_list:
            assert call.kwargs.get("is_initial") is True


@pytest.mark.smoke
class TestDimmableLightRegistrationMutants:
    """Kill dimmable light registration and class attr mutants."""

    def test_dimmable_color_mode_is_brightness(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Kill: _attr_color_mode = ColorMode.BRIGHTNESS → None mutation."""
        from homeassistant.components.light import ColorMode

        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        assert light._attr_color_mode == ColorMode.BRIGHTNESS

    def test_dimmable_supported_modes_contains_brightness(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Kill: _attr_supported_color_modes = {ColorMode.BRIGHTNESS} → {} mutation."""
        from homeassistant.components.light import ColorMode

        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        assert ColorMode.BRIGHTNESS in light._attr_supported_color_modes

    def test_dimmable_initial_brightness_is_255(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Already tested but now @smoke — kill _attr_brightness = 255 → 0 mutation."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        assert light.brightness == 255

    @pytest.mark.asyncio
    async def test_dimmable_register_listener_for_dim_address(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Kill: register_listener(None, handler) for brightness address."""
        mock_knx_gateway._connected = True
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_on_remove = Mock(return_value=lambda: None)
        await light.async_added_to_hass()
        registered = [c[0][0] for c in mock_knx_gateway.register_listener.call_args_list]
        assert "1/2/7" in registered

    def test_dim_address_stored(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        """Kill: _address_dim = datapoints.get('Dimmen%') → None mutation."""
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        assert light._address_dim == "1/2/7"


@pytest.mark.smoke
class TestDimmerBrightnessFloor:
    """Dimmer must not send 0% for a non-zero brightness (would switch light off)."""

    @pytest.mark.asyncio
    async def test_brightness_1_does_not_send_zero(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        await light.async_turn_on(brightness=1)

        percent = mock_knx_gateway.async_send_telegram.call_args[0][1]
        assert percent >= 1, "brightness 1 must map to at least 1%, not 0% (off)"

    @pytest.mark.asyncio
    async def test_brightness_2_does_not_send_zero(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        await light.async_turn_on(brightness=2)

        percent = mock_knx_gateway.async_send_telegram.call_args[0][1]
        assert percent >= 1

    @pytest.mark.asyncio
    async def test_brightness_255_sends_100(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()

        await light.async_turn_on(brightness=255)

        percent = mock_knx_gateway.async_send_telegram.call_args[0][1]
        assert percent == 100


@pytest.mark.smoke
class TestDimmerTurnOnGuards:
    """Dimmer turn_on must honour rate-limit and availability guards like the base class."""

    @pytest.mark.asyncio
    async def test_dimmer_turn_on_respects_rate_limit(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()
        # Saturate the rate limiter
        for _ in range(6):
            light._is_rate_limited()
        mock_knx_gateway.async_send_telegram.reset_mock()

        await light.async_turn_on(brightness=128)

        mock_knx_gateway.async_send_telegram.assert_not_called()

    @pytest.mark.asyncio
    async def test_dimmer_turn_on_raises_when_unavailable(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        from homeassistant.exceptions import HomeAssistantError

        light = LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        light.async_write_ha_state = Mock()
        # Force unavailable
        light._raise_if_unavailable = Mock(side_effect=HomeAssistantError("unavailable"))

        with pytest.raises(HomeAssistantError):
            await light.async_turn_on(brightness=128)

        mock_knx_gateway.async_send_telegram.assert_not_called()


@pytest.mark.smoke
class TestLightListenerRegistrationTiming:
    """Listeners must be registered in async_added_to_hass (event loop), not __init__ (executor)."""

    def test_no_listener_registered_in_init(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        LuxorLivingLight(mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway)
        mock_knx_gateway.register_listener.assert_not_called()

    @pytest.mark.asyncio
    async def test_listeners_registered_after_added_to_hass(
        self, mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
    ):
        mock_knx_gateway._connected = True
        light = LuxorLivingLight(
            mock_coordinator, mock_config_entry, mock_mapped_entity, mock_knx_gateway
        )
        light.async_on_remove = Mock(return_value=lambda: None)

        await light.async_added_to_hass()

        assert mock_knx_gateway.register_listener.call_count >= 1

    def test_no_brightness_listener_registered_in_init(
        self, mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
    ):
        LuxorLivingDimmableLight(
            mock_coordinator, mock_config_entry, mock_dimmable_entity, mock_knx_gateway
        )
        mock_knx_gateway.register_listener.assert_not_called()
