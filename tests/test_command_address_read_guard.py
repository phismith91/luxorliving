"""Regression tests for #217: reading a shared command group address switches lights off.

A binary sensor (push button) can be mapped onto the central-off / panic group
addresses. Every actuator listens on those addresses, and a read on them makes the
actuators report ``0`` which switches the lights off. Command addresses shared by
several actuators must therefore never be read.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.binary_sensor import LuxorLivingBinarySensor
from custom_components.luxor_living.knx_gateway import (
    LuxorKNXGateway,
    compute_no_read_addresses,
)
from custom_components.luxor_living.mapped_entity import MappedEntity

ZENTRAL_AUS = 10745  # 5/1/249
PANIK = 10744  # 5/1/248


def _entity(platform, name, datapoints):
    return MappedEntity(
        platform=platform,
        unique_id=f"uid_{name}",
        name=name,
        device_name="dev",
        device_id="dev1",
        entity_type="light" if platform == Platform.LIGHT else "binary_sensor",
        datapoints=datapoints,
        attributes={},
        parameters={},
    )


def _light(name, on, status):
    return _entity(
        Platform.LIGHT,
        name,
        {"OnOff": on, "StatusOnOff": status, "ZentralAus": ZENTRAL_AUS, "Panik": PANIK},
    )


def _connected_gateway():
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda f, *a: f(*a))
    gw = LuxorKNXGateway(
        hass=hass,
        host="192.168.1.100",
        port=3671,
        username="admin",
        password="pass",
        connection_type="tunneling",
        simulation_mode=False,
    )
    gw._connected = True
    gw._xknx = MagicMock()
    gw._xknx.telegrams = AsyncMock()
    gw._xknx.telegrams.put = AsyncMock()
    gw._xknx.connection_manager.cemi_count_outgoing_error = 0
    gw._xknx.telegram_queue.outgoing_queue.qsize.return_value = 0
    return gw


class TestComputeNoReadAddresses:
    def test_shared_central_addresses_are_blocked(self):
        entities = [_light("a", 2048, 2304), _light("b", 2049, 2305)]
        blocked = compute_no_read_addresses(entities)
        assert {"5/1/249", "5/1/248"} <= blocked

    def test_own_command_and_status_addresses_are_not_blocked(self):
        entities = [_light("a", 2048, 2304), _light("b", 2049, 2305)]
        blocked = compute_no_read_addresses(entities)
        assert "1/0/0" not in blocked  # 2048, lights without status fall back to reading it
        assert "1/1/0" not in blocked  # 2304

    def test_single_actuator_central_roles_still_blocked(self):
        blocked = compute_no_read_addresses([_light("a", 2048, 2304)])
        assert {"5/1/249", "5/1/248"} <= blocked

    def test_command_address_shared_by_two_actuators_is_blocked(self):
        group = 10496  # group switch address used by two lights
        e1 = _entity(Platform.LIGHT, "a", {"OnOff": group, "StatusOnOff": 2304})
        e2 = _entity(Platform.LIGHT, "b", {"OnOff": group, "StatusOnOff": 2305})
        assert "5/1/0" in compute_no_read_addresses([e1, e2])

    def test_sensor_datapoints_do_not_count_as_command_addresses(self):
        button = _entity(Platform.BINARY_SENSOR, "t5", {"OnOff": 2048})
        assert compute_no_read_addresses([button, _light("a", 2048, 2304)]) >= {"5/1/249"}
        assert "1/0/0" not in compute_no_read_addresses([button, _light("a", 2048, 2304)])


class TestGatewayRefusesBlockedReads:
    @pytest.mark.asyncio
    async def test_blocked_address_is_not_read_int_or_string(self):
        gw = _connected_gateway()
        gw.set_no_read_addresses({"5/1/249"})

        assert await gw.async_read_group_address(ZENTRAL_AUS, is_initial=True) is False
        assert await gw.async_read_group_address("5/1/249") is False
        gw._xknx.telegrams.put.assert_not_awaited()
        assert "5/1/249" not in gw._initial_read_pending

    @pytest.mark.asyncio
    async def test_other_addresses_are_still_read(self):
        gw = _connected_gateway()
        gw.set_no_read_addresses({"5/1/249"})

        assert await gw.async_read_group_address("1/1/0", is_initial=True) is True
        gw._xknx.telegrams.put.assert_awaited_once()


class TestCentralOffSensorEndToEnd:
    @pytest.mark.asyncio
    async def test_t5_binary_sensor_never_reads_central_addresses_on_startup(self):
        """Issue #217: HA restart switched all lights off through the T5 sensor read."""
        lights = [_light("a", 2048, 2304), _light("b", 2049, 2305)]
        gw = _connected_gateway()
        gw.set_no_read_addresses(compute_no_read_addresses(lights))

        for address in (ZENTRAL_AUS, PANIK):
            coordinator = MagicMock()
            coordinator.last_update_success = True
            coordinator.async_add_listener = MagicMock(return_value=lambda: None)
            entry = MagicMock()
            entry.runtime_data.knx_gateway = gw
            t5 = LuxorLivingBinarySensor(
                coordinator, entry, _entity(Platform.BINARY_SENSOR, "T5", {"OnOff": address})
            )
            await t5.async_added_to_hass()

        gw._xknx.telegrams.put.assert_not_awaited()
