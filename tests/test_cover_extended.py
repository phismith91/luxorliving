"""Extended tests for cover.py covering uncovered branches."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature
from homeassistant.const import Platform
from homeassistant.exceptions import HomeAssistantError

from custom_components.luxor_living.cover import LuxorCover, _create_cover_entity_sync
from custom_components.luxor_living.mapped_entity import MappedEntity


def _mapped(datapoints=None, name="Test Cover"):
    """Create a MappedEntity for cover tests.

    Accepts datapoints as a list of {"role": ..., "address": ...} dicts
    (legacy test format) and converts to the dict[str, int] format used by
    MappedEntity.  Address values are cast to int to match production data.
    """
    dp_dict = {dp["role"]: int(dp["address"]) for dp in (datapoints or [])}
    return MappedEntity(
        platform=Platform.COVER,
        unique_id="test_cover_001",
        name=name,
        device_name="Test Device",
        device_id="dev_001",
        entity_type="cover",
        datapoints=dp_dict,
        attributes={},
        parameters={},
    )


def _make_cover(datapoints=None, connected=True):
    coordinator = MagicMock()
    gateway = MagicMock()
    gateway.connected = connected
    gateway.async_send_telegram = AsyncMock(return_value=True)
    gateway.async_read_group_address = AsyncMock(return_value=True)
    gateway.register_listener = MagicMock()
    gateway.unregister_listener = MagicMock()

    entry = MagicMock()
    entry.entry_id = "entry_001"

    mapped = _mapped(datapoints)
    entity = LuxorCover(
        coordinator=coordinator,
        knx_gateway=gateway,
        mapped_entity=mapped,
        entry_id="entry_001",
    )
    entity.async_write_ha_state = MagicMock()
    return entity, gateway


# ── _create_cover_entity_sync ─────────────────────────────────────────────────


class TestCreateCoverEntitySync:
    def test_creates_luxor_cover(self):
        coordinator = MagicMock()
        gateway = MagicMock()
        entry = MagicMock()
        entry.entry_id = "e1"
        mapped = _mapped([])
        entity = _create_cover_entity_sync(coordinator, entry, mapped, gateway)
        assert isinstance(entity, LuxorCover)


# ── __init__ ──────────────────────────────────────────────────────────────────


class TestCoverInit:
    def test_shutter_without_tilt(self):
        entity, _ = _make_cover([{"role": "UpDown", "address": 200}])
        assert entity._attr_device_class == CoverDeviceClass.SHUTTER

    def test_blind_with_tilt(self):
        entity, _ = _make_cover(
            [
                {"role": "UpDown", "address": 200},
                {"role": "Lamelle%", "address": 204},
            ]
        )
        assert entity._attr_device_class == CoverDeviceClass.BLIND

    def test_set_position_feature_with_hoehe(self):
        entity, _ = _make_cover([{"role": "Höhe%", "address": 203}])
        assert entity._attr_supported_features & CoverEntityFeature.SET_POSITION

    def test_tilt_features_added_for_blind(self):
        entity, _ = _make_cover(
            [
                {"role": "UpDown", "address": 200},
                {"role": "Lamelle%", "address": 204},
            ]
        )
        assert entity._attr_supported_features & CoverEntityFeature.OPEN_TILT
        assert entity._attr_supported_features & CoverEntityFeature.SET_TILT_POSITION

    def test_no_tilt_features_for_shutter(self):
        entity, _ = _make_cover([{"role": "UpDown", "address": 200}])
        assert not (entity._attr_supported_features & CoverEntityFeature.OPEN_TILT)

    def test_initial_position_is_none(self):
        entity, _ = _make_cover([])
        assert entity._attr_current_cover_position is None

    def test_unique_id_set(self):
        entity, _ = _make_cover([])
        assert entity._attr_unique_id == "test_cover_001"


# ── available / _raise_if_unavailable ─────────────────────────────────────────


class TestAvailability:
    def test_available_when_connected(self):
        entity, _ = _make_cover(connected=True)
        assert entity.available is True

    def test_unavailable_when_disconnected(self):
        entity, _ = _make_cover(connected=False)
        assert entity.available is False

    def test_raises_when_unavailable(self):
        entity, _ = _make_cover(connected=False)
        with pytest.raises(HomeAssistantError):
            entity._raise_if_unavailable()

    def test_no_raise_when_available(self):
        entity, _ = _make_cover(connected=True)
        entity._raise_if_unavailable()  # must not raise


# ── open / close / stop ───────────────────────────────────────────────────────


class TestBasicCommands:
    @pytest.mark.asyncio
    async def test_open_sends_updown_0(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": 200}])
        await entity.async_open_cover()
        gateway.async_send_telegram.assert_awaited_once_with(200, 0, "binary")

    @pytest.mark.asyncio
    async def test_open_no_updown_does_nothing(self):
        entity, gateway = _make_cover([])
        await entity.async_open_cover()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_open_exception_is_caught(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": 200}])
        gateway.async_send_telegram = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_open_cover()  # must not raise

    @pytest.mark.asyncio
    async def test_close_sends_updown_1(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": 200}])
        await entity.async_close_cover()
        gateway.async_send_telegram.assert_awaited_once_with(200, 1, "binary")

    @pytest.mark.asyncio
    async def test_close_no_updown_does_nothing(self):
        entity, gateway = _make_cover([])
        await entity.async_close_cover()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_close_exception_is_caught(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": 200}])
        gateway.async_send_telegram = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_close_cover()  # must not raise

    @pytest.mark.asyncio
    async def test_stop_sends_stepstop_0(self):
        entity, gateway = _make_cover([{"role": "StepStop", "address": 201}])
        await entity.async_stop_cover()
        gateway.async_send_telegram.assert_awaited_once_with(201, 0, "binary")

    @pytest.mark.asyncio
    async def test_stop_no_stepstop_does_nothing(self):
        entity, gateway = _make_cover([])
        await entity.async_stop_cover()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_stop_exception_is_caught(self):
        entity, gateway = _make_cover([{"role": "StepStop", "address": 201}])
        gateway.async_send_telegram = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_stop_cover()  # must not raise


# ── set_cover_position ────────────────────────────────────────────────────────


class TestSetPosition:
    @pytest.mark.asyncio
    async def test_set_position_writes_address(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": 203}])
        await entity.async_set_cover_position(**{"position": 50})
        gateway.async_send_telegram.assert_awaited_once_with(203, 50, "percent")

    @pytest.mark.asyncio
    async def test_set_position_updates_state(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": 203}])
        await entity.async_set_cover_position(**{"position": 75})
        assert entity._attr_current_cover_position == 75
        assert entity._attr_is_closed is False

    @pytest.mark.asyncio
    async def test_set_position_0_marks_closed(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": 203}])
        await entity.async_set_cover_position(**{"position": 0})
        assert entity._attr_is_closed is True

    @pytest.mark.asyncio
    async def test_set_position_none_does_nothing(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": 203}])
        await entity.async_set_cover_position()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_position_no_address_does_nothing(self):
        entity, gateway = _make_cover([])
        await entity.async_set_cover_position(**{"position": 50})
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_position_exception_is_caught(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": 203}])
        gateway.async_send_telegram = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_set_cover_position(**{"position": 50})  # must not raise


# ── tilt commands ─────────────────────────────────────────────────────────────


class TestTiltCommands:
    @pytest.mark.asyncio
    async def test_open_tilt_sends_100(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": 200},
                {"role": "Lamelle%", "address": 204},
            ]
        )
        await entity.async_open_cover_tilt()
        gateway.async_send_telegram.assert_awaited_once_with(204, 100, "percent")

    @pytest.mark.asyncio
    async def test_open_tilt_no_tilt_does_nothing(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": 200}])
        await entity.async_open_cover_tilt()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_open_tilt_exception_is_caught(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": 200},
                {"role": "Lamelle%", "address": 204},
            ]
        )
        gateway.async_send_telegram = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_open_cover_tilt()  # must not raise

    @pytest.mark.asyncio
    async def test_close_tilt_sends_0(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": 200},
                {"role": "Lamelle%", "address": 204},
            ]
        )
        await entity.async_close_cover_tilt()
        gateway.async_send_telegram.assert_awaited_once_with(204, 0, "percent")

    @pytest.mark.asyncio
    async def test_close_tilt_no_tilt_does_nothing(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": 200}])
        await entity.async_close_cover_tilt()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_close_tilt_exception_is_caught(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": 200},
                {"role": "Lamelle%", "address": 204},
            ]
        )
        gateway.async_send_telegram = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_close_cover_tilt()  # must not raise

    @pytest.mark.asyncio
    async def test_stop_tilt_sends_stepstop(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": 200},
                {"role": "Lamelle%", "address": 204},
                {"role": "StepStop", "address": 201},
            ]
        )
        await entity.async_stop_cover_tilt()
        gateway.async_send_telegram.assert_awaited_once_with(201, 0, "binary")

    @pytest.mark.asyncio
    async def test_stop_tilt_no_tilt_does_nothing(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": 200}])
        await entity.async_stop_cover_tilt()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_stop_tilt_exception_is_caught(self):
        entity, gateway = _make_cover(
            [
                {"role": "Lamelle%", "address": 204},
                {"role": "StepStop", "address": 201},
            ]
        )
        gateway.async_send_telegram = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_stop_cover_tilt()  # must not raise

    @pytest.mark.asyncio
    async def test_set_tilt_position_writes_address(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": 200},
                {"role": "Lamelle%", "address": 204},
            ]
        )
        await entity.async_set_cover_tilt_position(**{"tilt_position": 45})
        gateway.async_send_telegram.assert_awaited_once_with(204, 45, "percent")

    @pytest.mark.asyncio
    async def test_set_tilt_no_tilt_does_nothing(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": 200}])
        await entity.async_set_cover_tilt_position(**{"tilt_position": 45})
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_tilt_none_position_does_nothing(self):
        entity, gateway = _make_cover(
            [
                {"role": "Lamelle%", "address": 204},
            ]
        )
        await entity.async_set_cover_tilt_position()
        gateway.async_send_telegram.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_tilt_exception_is_caught(self):
        entity, gateway = _make_cover(
            [
                {"role": "Lamelle%", "address": 204},
            ]
        )
        gateway.async_send_telegram = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_set_cover_tilt_position(**{"tilt_position": 45})  # must not raise


# ── _update_position ──────────────────────────────────────────────────────────


class TestUpdatePosition:
    @pytest.mark.asyncio
    async def test_reads_status_hoehe_when_available(self):
        entity, gateway = _make_cover(
            [
                {"role": "StatusHöhe%", "address": 202},
                {"role": "Höhe%", "address": 203},
            ]
        )
        await entity._update_position()
        gateway.async_read_group_address.assert_awaited_with(202)

    @pytest.mark.asyncio
    async def test_position_set_from_callback(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": 202}])
        entity._handle_position_update(202, 80)
        assert entity._attr_current_cover_position == 80
        assert entity._attr_is_closed is False

    @pytest.mark.asyncio
    async def test_position_0_marks_closed(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": 202}])
        entity._handle_position_update(202, 0)
        assert entity._attr_is_closed is True

    @pytest.mark.asyncio
    async def test_non_numeric_position_ignored(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": 202}])
        entity._handle_position_update(202, "invalid")
        assert entity._attr_current_cover_position is None

    @pytest.mark.asyncio
    async def test_update_position_sends_read_request(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": 202}])
        await entity._update_position()
        gateway.async_read_group_address.assert_awaited()

    @pytest.mark.asyncio
    async def test_async_update_calls_update_position(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": 202}])
        await entity.async_update()
        gateway.async_read_group_address.assert_awaited()
