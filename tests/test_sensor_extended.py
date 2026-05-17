"""Extended tests for sensor.py covering uncovered branches."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.luxor_living.sensor import (
    LuxorLivingDiscoveredSensor,
    LuxorLivingSensor,
)


def _make_mapped_entity(entity_type="temperature", datapoints=None, attributes=None):
    me = MagicMock()
    me.unique_id = f"test_{entity_type}"
    me.name = f"Test {entity_type.title()}"
    me.device_name = "Wetterstation"
    me.device_id = "dev_001"
    me.entity_type = entity_type
    me.parameters = {}
    me.attributes = attributes or {}
    me.datapoints = datapoints or {}
    return me


def _make_sensor(entity_type="temperature", datapoints=None, attributes=None):
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    coordinator.async_request_refresh = AsyncMock()

    gateway = MagicMock()
    gateway.connected = True
    gateway.simulation_mode = False
    gateway.register_listener = MagicMock()
    gateway.unregister_listener = MagicMock()
    gateway.async_read_group_address = AsyncMock(return_value=True)

    entry = MagicMock()
    entry.runtime_data = MagicMock()
    entry.runtime_data.knx_gateway = gateway

    mapped = _make_mapped_entity(entity_type, datapoints, attributes)
    entity = LuxorLivingSensor(coordinator, entry, mapped, gateway)
    entity.async_write_ha_state = MagicMock()
    return entity, gateway


# ── LuxorLivingSensor.__init__ ────────────────────────────────────────────────


class TestSensorInit:
    def test_temperature_uses_temperature_datapoint(self):
        entity, _ = _make_sensor("temperature", datapoints={"Temperature": "5/0/1"})
        assert entity._datapoint_address == "5/0/1"

    def test_humidity_uses_humidity_datapoint(self):
        entity, _ = _make_sensor("humidity", datapoints={"Humidity": "5/0/2"})
        assert entity._datapoint_address == "5/0/2"

    def test_pressure_uses_pressure_datapoint(self):
        entity, _ = _make_sensor("pressure", datapoints={"Pressure": "5/0/3"})
        assert entity._datapoint_address == "5/0/3"

    def test_co2_uses_co2_datapoint(self):
        entity, _ = _make_sensor("co2", datapoints={"CO2": "5/0/4"})
        assert entity._datapoint_address == "5/0/4"

    def test_brightness_uses_brightness_datapoint(self):
        entity, _ = _make_sensor("brightness", datapoints={"Brightness": "5/0/5"})
        assert entity._datapoint_address == "5/0/5"

    def test_windspeed_uses_windspeed_datapoint(self):
        entity, _ = _make_sensor("windspeed", datapoints={"WindSpeed": "5/0/6"})
        assert entity._datapoint_address == "5/0/6"

    def test_rainvolume_uses_rainvolume_datapoint(self):
        entity, _ = _make_sensor("rainvolume", datapoints={"RainVolume": "5/0/7"})
        assert entity._datapoint_address == "5/0/7"

    def test_airquality_uses_airquality_datapoint(self):
        entity, _ = _make_sensor("airquality", datapoints={"AirQuality": "5/0/8"})
        assert entity._datapoint_address == "5/0/8"

    def test_unknown_type_falls_back_to_first_datapoint(self):
        entity, _ = _make_sensor("custom", datapoints={"SomeRole": "5/0/9"})
        assert entity._datapoint_address == "5/0/9"

    def test_unknown_type_no_datapoints_is_none(self):
        entity, _ = _make_sensor("custom", datapoints={})
        assert entity._datapoint_address is None

    def test_device_class_set_from_description(self):
        from homeassistant.components.sensor import SensorDeviceClass

        entity, _ = _make_sensor("temperature")
        # Known types use entity_description instead of _attr_device_class
        assert entity.entity_description.device_class == SensorDeviceClass.TEMPERATURE

    def test_unit_set_from_description(self):
        from homeassistant.const import UnitOfTemperature

        entity, _ = _make_sensor("temperature")
        # Known types carry the unit via entity_description
        assert entity.entity_description.native_unit_of_measurement == UnitOfTemperature.CELSIUS

    def test_unknown_type_device_class_set_from_attributes(self):
        from homeassistant.components.sensor import SensorDeviceClass

        entity, _ = _make_sensor(
            "custom_type",
            attributes={"device_class": SensorDeviceClass.TEMPERATURE},
        )
        # Unknown types still fall back to _attr_* from LXP attributes
        assert entity._attr_device_class == SensorDeviceClass.TEMPERATURE

    def test_unknown_type_unit_set_from_attributes(self):
        entity, _ = _make_sensor(
            "custom_type",
            attributes={"unit_of_measurement": "°C"},
        )
        assert entity._attr_native_unit_of_measurement == "°C"


# ── async_added_to_hass ───────────────────────────────────────────────────────


class TestAsyncAddedToHass:
    @pytest.mark.asyncio
    async def test_registers_knx_listener(self):
        entity, gateway = _make_sensor("temperature", datapoints={"Temperature": "5/0/1"})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        gateway.register_listener.assert_called_once_with("5/0/1", entity._on_telegram)

    @pytest.mark.asyncio
    async def test_sends_initial_read(self):
        entity, gateway = _make_sensor("temperature", datapoints={"Temperature": "5/0/1"})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        gateway.async_read_group_address.assert_awaited_once_with("5/0/1", is_initial=True)

    @pytest.mark.asyncio
    async def test_no_listener_when_no_address(self):
        entity, gateway = _make_sensor("custom", datapoints={})
        entity.async_on_remove = MagicMock()
        await entity.async_added_to_hass()
        gateway.register_listener.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_read_state_exception_is_caught(self):
        entity, gateway = _make_sensor("temperature", datapoints={"Temperature": "5/0/1"})
        gateway.async_read_group_address = AsyncMock(side_effect=RuntimeError("KNX error"))
        await entity._async_read_state()  # must not raise

    @pytest.mark.asyncio
    async def test_async_read_state_no_address_returns_early(self):
        entity, gateway = _make_sensor("custom", datapoints={})
        await entity._async_read_state()  # _datapoint_address is None → early return
        gateway.async_read_group_address.assert_not_awaited()


# ── async_will_remove_from_hass ───────────────────────────────────────────────


class TestAsyncWillRemoveFromHass:
    @pytest.mark.asyncio
    async def test_unregisters_listener(self):
        entity, gateway = _make_sensor("temperature", datapoints={"Temperature": "5/0/1"})
        await entity.async_will_remove_from_hass()
        gateway.unregister_listener.assert_called_once_with("5/0/1", entity._on_telegram)

    @pytest.mark.asyncio
    async def test_no_unregister_when_no_address(self):
        entity, gateway = _make_sensor("custom", datapoints={})
        await entity.async_will_remove_from_hass()
        gateway.unregister_listener.assert_not_called()


# ── _on_telegram ──────────────────────────────────────────────────────────────


class TestOnTelegram:
    def test_updates_state_with_float(self):
        entity, _ = _make_sensor("temperature", datapoints={"Temperature": "5/0/1"})
        entity._on_telegram("5/0/1", 21.5)
        assert entity._attr_native_value == 21.5
        entity.async_write_ha_state.assert_called_once()

    def test_updates_state_with_int(self):
        entity, _ = _make_sensor("temperature", datapoints={"Temperature": "5/0/1"})
        entity._on_telegram("5/0/1", 42)
        assert entity._attr_native_value == 42

    def test_skips_none_value(self):
        entity, _ = _make_sensor("temperature", datapoints={"Temperature": "5/0/1"})
        entity._on_telegram("5/0/1", None)
        assert entity._attr_native_value is None
        entity.async_write_ha_state.assert_not_called()


# ── _normalize_value ──────────────────────────────────────────────────────────


class TestNormalizeValue:
    def test_float_passthrough(self):
        result = LuxorLivingSensor._normalize_value(21.5)
        assert result == 21.5

    def test_bool_passthrough(self):
        result = LuxorLivingSensor._normalize_value(True)
        assert result is True

    def test_none_passthrough(self):
        result = LuxorLivingSensor._normalize_value(None)
        assert result is None

    def test_two_byte_tuple_decoded(self):
        result = LuxorLivingSensor._normalize_value((0x0C, 0x04))
        assert isinstance(result, float)

    def test_two_byte_list_decoded(self):
        result = LuxorLivingSensor._normalize_value([0x0C, 0x04])
        assert isinstance(result, float)

    def test_invalid_two_byte_returns_raw(self):
        # Pass non-numeric values that trigger a DPT2ByteFloat decode error
        result = LuxorLivingSensor._normalize_value(("x", "y"))
        # Should return the raw tuple unchanged on decode error
        assert result == ("x", "y")


# ── LuxorLivingDiscoveredSensor ───────────────────────────────────────────────


def _make_discovered_sensor(sensor_type="temperature", last_value=21.5):
    coordinator = MagicMock()
    entry = MagicMock()
    entry.entry_id = "entry_001"
    gateway = MagicMock()
    gateway.register_listener = MagicMock()
    gateway.unregister_listener = MagicMock()
    sensor_info = {
        "address": "5/1/10",
        "type": sensor_type,
        "last_value": last_value,
    }
    entity = LuxorLivingDiscoveredSensor(coordinator, entry, sensor_info, gateway)
    entity.async_write_ha_state = MagicMock()
    return entity, gateway


class TestDiscoveredSensor:
    def test_unique_id_uses_entry_and_address(self):
        entity, _ = _make_discovered_sensor()
        assert "entry_001" in entity._attr_unique_id
        assert "5_1_10" in entity._attr_unique_id

    def test_name_includes_type_and_address(self):
        entity, _ = _make_discovered_sensor("temperature")
        assert "Temperature" in entity._attr_name
        assert "5/1/10" in entity._attr_name

    def test_initial_value_set(self):
        entity, _ = _make_discovered_sensor(last_value=22.3)
        assert entity._attr_native_value == 22.3

    def test_temperature_type_attributes(self):
        from homeassistant.components.sensor import SensorDeviceClass

        entity, _ = _make_discovered_sensor("temperature")
        assert entity._attr_device_class == SensorDeviceClass.TEMPERATURE

    def test_humidity_type_attributes(self):
        from homeassistant.components.sensor import SensorDeviceClass

        entity, _ = _make_discovered_sensor("humidity")
        assert entity._attr_device_class == SensorDeviceClass.HUMIDITY

    def test_illuminance_type_attributes(self):
        from homeassistant.components.sensor import SensorDeviceClass

        entity, _ = _make_discovered_sensor("illuminance")
        assert entity._attr_device_class == SensorDeviceClass.ILLUMINANCE

    def test_pressure_type_attributes(self):
        from homeassistant.components.sensor import SensorDeviceClass

        entity, _ = _make_discovered_sensor("pressure")
        assert entity._attr_device_class == SensorDeviceClass.PRESSURE

    def test_generic_type_no_device_class(self):
        entity, _ = _make_discovered_sensor("generic_sensor")
        assert entity._attr_device_class is None

    @pytest.mark.asyncio
    async def test_async_added_registers_listener(self):
        entity, gateway = _make_discovered_sensor()
        await entity.async_added_to_hass()
        gateway.register_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_telegram_update_sets_float_value(self):
        entity, gateway = _make_discovered_sensor()
        await entity.async_added_to_hass()
        # Trigger the registered callback
        cb = gateway.register_listener.call_args[0][1]
        cb("5/1/10", 23.5)
        assert entity._attr_native_value == 23.5
        entity.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_telegram_update_ignores_non_float(self):
        entity, gateway = _make_discovered_sensor()
        await entity.async_added_to_hass()
        cb = gateway.register_listener.call_args[0][1]
        cb("5/1/10", True)  # bool, not float
        assert entity._attr_native_value == 21.5  # unchanged

    @pytest.mark.asyncio
    async def test_async_will_remove_unregisters(self):
        entity, gateway = _make_discovered_sensor()
        # Must add first so the callback reference is stored
        await entity.async_added_to_hass()
        await entity.async_will_remove_from_hass()
        # register + unregister both called exactly once with the same callback
        gateway.register_listener.assert_called_once()
        gateway.unregister_listener.assert_called_once()
        reg_cb = gateway.register_listener.call_args[0][1]
        unreg_cb = gateway.unregister_listener.call_args[0][1]
        assert reg_cb is unreg_cb, "unregister must use exact same callback reference"

    async def test_async_will_remove_noop_when_never_added(self):
        """async_will_remove_from_hass must not crash if called without async_added_to_hass."""
        entity, gateway = _make_discovered_sensor()
        # _knx_callback is None — must not raise
        await entity.async_will_remove_from_hass()
        gateway.unregister_listener.assert_not_called()
