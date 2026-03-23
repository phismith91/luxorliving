"""Extended tests for cover.py covering uncovered branches."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature
from homeassistant.exceptions import HomeAssistantError

from custom_components.luxor_living.cover import LuxorCover, _create_cover_entity_sync


def _mapped(datapoints=None, name="Test Cover"):
    return {
        "unique_id": "test_cover_001",
        "name": name,
        "device_id": "dev_001",
        "device_name": "Test Device",
        "device_model": "J8",
        "datapoints": datapoints or [],
    }


def _make_cover(datapoints=None, connected=True):
    coordinator = MagicMock()
    gateway = MagicMock()
    gateway.connected = connected
    gateway.write_group_address = AsyncMock()
    gateway.read_group_address = AsyncMock(return_value=None)

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
        entity, _ = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
        assert entity._attr_device_class == CoverDeviceClass.SHUTTER

    def test_blind_with_tilt(self):
        entity, _ = _make_cover(
            [
                {"role": "UpDown", "address": "2/0/0"},
                {"role": "Lamelle%", "address": "2/0/4"},
            ]
        )
        assert entity._attr_device_class == CoverDeviceClass.BLIND

    def test_set_position_feature_with_hoehe(self):
        entity, _ = _make_cover([{"role": "Höhe%", "address": "2/0/3"}])
        assert entity._attr_supported_features & CoverEntityFeature.SET_POSITION

    def test_tilt_features_added_for_blind(self):
        entity, _ = _make_cover(
            [
                {"role": "UpDown", "address": "2/0/0"},
                {"role": "Lamelle%", "address": "2/0/4"},
            ]
        )
        assert entity._attr_supported_features & CoverEntityFeature.OPEN_TILT
        assert entity._attr_supported_features & CoverEntityFeature.SET_TILT_POSITION

    def test_no_tilt_features_for_shutter(self):
        entity, _ = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
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
        entity, gateway = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
        await entity.async_open_cover()
        gateway.write_group_address.assert_awaited_once_with("2/0/0", 0)

    @pytest.mark.asyncio
    async def test_open_no_updown_does_nothing(self):
        entity, gateway = _make_cover([])
        await entity.async_open_cover()
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_open_exception_is_caught(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
        gateway.write_group_address = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_open_cover()  # must not raise

    @pytest.mark.asyncio
    async def test_close_sends_updown_1(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
        await entity.async_close_cover()
        gateway.write_group_address.assert_awaited_once_with("2/0/0", 1)

    @pytest.mark.asyncio
    async def test_close_no_updown_does_nothing(self):
        entity, gateway = _make_cover([])
        await entity.async_close_cover()
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_close_exception_is_caught(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
        gateway.write_group_address = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_close_cover()  # must not raise

    @pytest.mark.asyncio
    async def test_stop_sends_stepstop_0(self):
        entity, gateway = _make_cover([{"role": "StepStop", "address": "2/0/1"}])
        await entity.async_stop_cover()
        gateway.write_group_address.assert_awaited_once_with("2/0/1", 0)

    @pytest.mark.asyncio
    async def test_stop_no_stepstop_does_nothing(self):
        entity, gateway = _make_cover([])
        await entity.async_stop_cover()
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_stop_exception_is_caught(self):
        entity, gateway = _make_cover([{"role": "StepStop", "address": "2/0/1"}])
        gateway.write_group_address = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_stop_cover()  # must not raise


# ── set_cover_position ────────────────────────────────────────────────────────


class TestSetPosition:
    @pytest.mark.asyncio
    async def test_set_position_writes_address(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": "2/0/3"}])
        await entity.async_set_cover_position(**{"position": 50})
        gateway.write_group_address.assert_awaited_once_with("2/0/3", 50)

    @pytest.mark.asyncio
    async def test_set_position_updates_state(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": "2/0/3"}])
        await entity.async_set_cover_position(**{"position": 75})
        assert entity._attr_current_cover_position == 75
        assert entity._attr_is_closed is False

    @pytest.mark.asyncio
    async def test_set_position_0_marks_closed(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": "2/0/3"}])
        await entity.async_set_cover_position(**{"position": 0})
        assert entity._attr_is_closed is True

    @pytest.mark.asyncio
    async def test_set_position_none_does_nothing(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": "2/0/3"}])
        await entity.async_set_cover_position()
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_position_no_address_does_nothing(self):
        entity, gateway = _make_cover([])
        await entity.async_set_cover_position(**{"position": 50})
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_position_exception_is_caught(self):
        entity, gateway = _make_cover([{"role": "Höhe%", "address": "2/0/3"}])
        gateway.write_group_address = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_set_cover_position(**{"position": 50})  # must not raise


# ── tilt commands ─────────────────────────────────────────────────────────────


class TestTiltCommands:
    @pytest.mark.asyncio
    async def test_open_tilt_sends_100(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": "2/0/0"},
                {"role": "Lamelle%", "address": "2/0/4"},
            ]
        )
        await entity.async_open_cover_tilt()
        gateway.write_group_address.assert_awaited_once_with("2/0/4", 100)

    @pytest.mark.asyncio
    async def test_open_tilt_no_tilt_does_nothing(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
        await entity.async_open_cover_tilt()
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_open_tilt_exception_is_caught(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": "2/0/0"},
                {"role": "Lamelle%", "address": "2/0/4"},
            ]
        )
        gateway.write_group_address = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_open_cover_tilt()  # must not raise

    @pytest.mark.asyncio
    async def test_close_tilt_sends_0(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": "2/0/0"},
                {"role": "Lamelle%", "address": "2/0/4"},
            ]
        )
        await entity.async_close_cover_tilt()
        gateway.write_group_address.assert_awaited_once_with("2/0/4", 0)

    @pytest.mark.asyncio
    async def test_close_tilt_no_tilt_does_nothing(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
        await entity.async_close_cover_tilt()
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_close_tilt_exception_is_caught(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": "2/0/0"},
                {"role": "Lamelle%", "address": "2/0/4"},
            ]
        )
        gateway.write_group_address = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_close_cover_tilt()  # must not raise

    @pytest.mark.asyncio
    async def test_stop_tilt_sends_stepstop(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": "2/0/0"},
                {"role": "Lamelle%", "address": "2/0/4"},
                {"role": "StepStop", "address": "2/0/1"},
            ]
        )
        await entity.async_stop_cover_tilt()
        gateway.write_group_address.assert_awaited_once_with("2/0/1", 0)

    @pytest.mark.asyncio
    async def test_stop_tilt_no_tilt_does_nothing(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
        await entity.async_stop_cover_tilt()
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_stop_tilt_exception_is_caught(self):
        entity, gateway = _make_cover(
            [
                {"role": "Lamelle%", "address": "2/0/4"},
                {"role": "StepStop", "address": "2/0/1"},
            ]
        )
        gateway.write_group_address = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_stop_cover_tilt()  # must not raise

    @pytest.mark.asyncio
    async def test_set_tilt_position_writes_address(self):
        entity, gateway = _make_cover(
            [
                {"role": "UpDown", "address": "2/0/0"},
                {"role": "Lamelle%", "address": "2/0/4"},
            ]
        )
        await entity.async_set_cover_tilt_position(**{"tilt_position": 45})
        gateway.write_group_address.assert_awaited_once_with("2/0/4", 45)

    @pytest.mark.asyncio
    async def test_set_tilt_no_tilt_does_nothing(self):
        entity, gateway = _make_cover([{"role": "UpDown", "address": "2/0/0"}])
        await entity.async_set_cover_tilt_position(**{"tilt_position": 45})
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_tilt_none_position_does_nothing(self):
        entity, gateway = _make_cover(
            [
                {"role": "Lamelle%", "address": "2/0/4"},
            ]
        )
        await entity.async_set_cover_tilt_position()
        gateway.write_group_address.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_tilt_exception_is_caught(self):
        entity, gateway = _make_cover(
            [
                {"role": "Lamelle%", "address": "2/0/4"},
            ]
        )
        gateway.write_group_address = AsyncMock(side_effect=RuntimeError("err"))
        await entity.async_set_cover_tilt_position(**{"tilt_position": 45})  # must not raise


# ── _update_position ──────────────────────────────────────────────────────────


class TestUpdatePosition:
    @pytest.mark.asyncio
    async def test_reads_status_hoehe_when_available(self):
        entity, gateway = _make_cover(
            [
                {"role": "StatusHöhe%", "address": "2/0/2"},
                {"role": "Höhe%", "address": "2/0/3"},
            ]
        )
        gateway.read_group_address = AsyncMock(return_value=60)
        await entity._update_position()
        gateway.read_group_address.assert_awaited_with("2/0/2")

    @pytest.mark.asyncio
    async def test_position_set_from_read_value(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": "2/0/2"}])
        gateway.read_group_address = AsyncMock(return_value=80)
        await entity._update_position()
        assert entity._attr_current_cover_position == 80
        assert entity._attr_is_closed is False

    @pytest.mark.asyncio
    async def test_position_0_marks_closed(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": "2/0/2"}])
        gateway.read_group_address = AsyncMock(return_value=0)
        await entity._update_position()
        assert entity._attr_is_closed is True

    @pytest.mark.asyncio
    async def test_none_position_not_updated(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": "2/0/2"}])
        gateway.read_group_address = AsyncMock(return_value=None)
        await entity._update_position()
        assert entity._attr_current_cover_position is None

    @pytest.mark.asyncio
    async def test_exception_in_update_is_caught(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": "2/0/2"}])
        gateway.read_group_address = AsyncMock(side_effect=RuntimeError("err"))
        await entity._update_position()  # must not raise

    @pytest.mark.asyncio
    async def test_async_update_calls_update_position(self):
        entity, gateway = _make_cover([{"role": "StatusHöhe%", "address": "2/0/2"}])
        gateway.read_group_address = AsyncMock(return_value=None)
        await entity.async_update()
        gateway.read_group_address.assert_awaited()
