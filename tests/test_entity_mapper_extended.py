"""Extended tests for EntityMapper covering uncovered branches."""

from unittest.mock import MagicMock

import pytest
from homeassistant.const import Platform

from custom_components.luxor_living.entity_mapper import EntityMapper
from custom_components.luxor_living.lxp_parser import (
    LXPActuator,
    LXPDatapoint,
    LXPDevice,
    LXPProject,
    LXPSensor,
)
from custom_components.luxor_living.mapped_entity import MappedEntity

# ── Helpers ───────────────────────────────────────────────────────────────────


def _datapoint(role: str, address: int) -> LXPDatapoint:
    dp = MagicMock(spec=LXPDatapoint)
    dp.role = role
    dp.address = address
    return dp


def _actuator(
    name: str, channel: int, datapoints: list, on_icon="", off_icon="", use_case=""
) -> LXPActuator:
    a = MagicMock(spec=LXPActuator)
    a.name = name
    a.channel = channel
    a.datapoints = datapoints
    a.on_icon = on_icon
    a.off_icon = off_icon
    a.use_case = use_case
    a.parameters = {}
    return a


def _sensor(name: str, channel: int, datapoints: list, sensor_type: int = 0) -> LXPSensor:
    s = MagicMock(spec=LXPSensor)
    s.name = name
    s.channel = channel
    s.datapoints = datapoints
    s.sensor_type = sensor_type
    s.parameters = {}
    return s


def _device(name: str, actuators=None, sensors=None, device_id="dev_001") -> LXPDevice:
    d = MagicMock(spec=LXPDevice)
    d.name = name
    d.id = device_id
    d.address = "1.1.1"
    d.serial_number = "SN123"
    d.actuators = actuators or []
    d.sensors = sensors or []
    return d


def _project(devices: list) -> LXPProject:
    p = MagicMock(spec=LXPProject)
    p.devices = devices
    return p


def _mapper(devices: list, overrides: dict | None = None) -> EntityMapper:
    return EntityMapper(_project(devices), overrides=overrides)


# ── Actuator mapping ──────────────────────────────────────────────────────────


class TestActuatorMapping:
    def test_maps_onoff_to_light(self):
        dp = _datapoint("OnOff", 0x0800)
        actuator = _actuator("Lampe", 1, [dp])
        device = _device("Gerät", actuators=[actuator])
        mapper = _mapper([device])
        lights = mapper.get_entities_by_platform(Platform.LIGHT)
        assert any(e.name == "Lampe" for e in lights)

    def test_maps_schalten_onoff_to_light(self):
        dp = _datapoint("SchaltenOnOff", 0x0900)
        actuator = _actuator("Switch2", 2, [dp])
        device = _device("Gerät", actuators=[actuator])
        mapper = _mapper([device])
        lights = mapper.get_entities_by_platform(Platform.LIGHT)
        assert any(e.name == "Switch2" for e in lights)

    def test_maps_dimmen_to_dimmable_light(self):
        dp_onoff = _datapoint("OnOff", 0x0800)
        dp_dim = _datapoint("Dimmen%", 0x0801)
        actuator = _actuator("Dimmer", 1, [dp_onoff, dp_dim])
        device = _device("Gerät", actuators=[actuator])
        mapper = _mapper([device])
        lights = mapper.get_entities_by_platform(Platform.LIGHT)
        assert any(e.entity_type == "dimmable_light" for e in lights)

    def test_maps_updown_to_cover(self):
        dp = _datapoint("UpDown", 0x0A00)
        actuator = _actuator("Jalousie", 1, [dp])
        device = _device("Gerät", actuators=[actuator])
        mapper = _mapper([device])
        covers = mapper.get_entities_by_platform(Platform.COVER)
        assert any(e.name == "Jalousie" for e in covers)

    def test_skips_actuator_without_known_roles(self):
        dp = _datapoint("UnknownRole", 0x0001)
        actuator = _actuator("NoMap", 1, [dp])
        device = _device("Gerät", actuators=[actuator])
        mapper = _mapper([device])
        # Should not add this actuator (only health entity from mapper)
        non_health = [e for e in mapper.entities if e.entity_type != "health"]
        assert len(non_health) == 0

    def test_strips_device_name_prefix_from_actuator(self):
        dp = _datapoint("OnOff", 0x0800)
        actuator = _actuator("Gerät Lampe", 1, [dp])
        device = _device("Gerät", actuators=[actuator])
        mapper = _mapper([device])
        entities = mapper.get_entities_by_platform(Platform.LIGHT)
        assert any(e.name == "Lampe" for e in entities)

    def test_actuator_name_fallback_to_channel(self):
        dp = _datapoint("OnOff", 0x0800)
        actuator = _actuator("", 3, [dp])
        device = _device("MyDev", actuators=[actuator])
        mapper = _mapper([device])
        entities = mapper.get_entities_by_platform(Platform.LIGHT)
        assert any("Ch3" in e.name for e in entities)

    def test_unique_id_uses_control_address(self):
        dp = _datapoint("OnOff", 0x0800)
        actuator = _actuator("Licht", 1, [dp])
        device = _device("Dev", actuators=[actuator], device_id="dev_x")
        mapper = _mapper([device])
        entities = [e for e in mapper.entities if e.entity_type != "health"]
        assert entities[0].unique_id == "dev_x_2048"  # 0x0800 = 2048

    def test_status_dim_makes_dimmable_light(self):
        dp = _datapoint("status@Dim", 0x0802)
        dp2 = _datapoint("OnOff", 0x0800)
        actuator = _actuator("DimLight", 1, [dp2, dp])
        device = _device("Gerät", actuators=[actuator])
        mapper = _mapper([device])
        lights = mapper.get_entities_by_platform(Platform.LIGHT)
        assert any(e.entity_type == "dimmable_light" for e in lights)


# ── Sensor mapping ────────────────────────────────────────────────────────────


class TestSensorMapping:
    def test_maps_status_onoff_to_binary_sensor(self):
        dp = _datapoint("status@OnOff", 0x1000)
        sensor = _sensor("Status", 1, [dp])
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        bsensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
        non_health = [e for e in bsensors if e.entity_type != "health"]
        assert any(e.entity_type == "binary_sensor" for e in non_health)

    def test_maps_master_slave_to_motion(self):
        dp1 = _datapoint("OnOff", 0x1000)
        dp2 = _datapoint("MasterSlave", 0x1001)
        sensor = _sensor("Motion", 1, [dp1, dp2])
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        bsensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
        non_health = [e for e in bsensors if e.entity_type != "health"]
        assert any(e.entity_type == "motion" for e in non_health)

    def test_maps_sensor_type_1_to_motion(self):
        dp = _datapoint("OnOff", 0x1000)
        sensor = _sensor("PIR", 1, [dp], sensor_type=1)
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        bsensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
        non_health = [e for e in bsensors if e.entity_type != "health"]
        assert any(e.entity_type == "motion" for e in non_health)

    def test_maps_onoff_sensor_to_switch_by_default(self):
        dp = _datapoint("OnOff", 0x1000)
        sensor = _sensor("WallSwitch", 1, [dp])
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        # Sensors with OnOff and no MasterSlave/sensor_type=1 → switch platform
        switches = mapper.get_entities_by_platform(Platform.SWITCH)
        assert len(switches) > 0

    def test_maps_onoff_to_binary_with_override(self):
        dp = _datapoint("OnOff", 0x1000)
        sensor = _sensor("Btn", 1, [dp])
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device], overrides={"map_onoff_to_binary": True})
        bsensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
        non_health = [e for e in bsensors if e.entity_type != "health"]
        assert len(non_health) > 0

    def test_skips_sensor_without_datapoints(self):
        sensor = _sensor("Empty", 1, [])
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        non_health = [e for e in mapper.entities if e.entity_type != "health"]
        assert len(non_health) == 0

    def test_skips_sensor_without_known_roles(self):
        dp = _datapoint("SomeUnknown", 0x2000)
        sensor = _sensor("Unknown", 1, [dp])
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        non_health = [e for e in mapper.entities if e.entity_type != "health"]
        assert len(non_health) == 0

    def test_strips_device_name_prefix_from_sensor(self):
        dp = _datapoint("status@OnOff", 0x1000)
        sensor = _sensor("Dev Status", 1, [dp])
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        bsensors = [e for e in mapper.entities if e.entity_type == "binary_sensor"]
        assert any(e.name == "Status" for e in bsensors)

    def test_sensor_name_fallback_to_channel(self):
        dp = _datapoint("status@OnOff", 0x1000)
        sensor = _sensor("", 2, [dp])
        device = _device("SomeDev", sensors=[sensor])
        mapper = _mapper([device])
        non_health = [e for e in mapper.entities if e.entity_type != "health"]
        assert any("Ch2" in e.name for e in non_health)


# ── Wetterstation mapping ─────────────────────────────────────────────────────


class TestWetterstationMapping:
    def test_maps_wetterstation_temperature(self):
        dp = _datapoint("Temperatur", 0x3000)
        sensor = _sensor("Temp", 1, [dp])
        device = _device("Wetterstation EG", sensors=[sensor])
        mapper = _mapper([device])
        sensors = mapper.get_entities_by_platform(Platform.SENSOR)
        assert any("Wetterstation" in e.name for e in sensors)

    def test_skips_regen_role(self):
        dp = _datapoint("Regen", 0x3001)
        sensor = _sensor("Rain", 1, [dp])
        device = _device("Wetterstation EG", sensors=[sensor])
        mapper = _mapper([device])
        non_health = [e for e in mapper.entities if e.entity_type != "health"]
        assert len(non_health) == 0

    def test_skips_duplicate_wetterstation_entity(self):
        dp = _datapoint("Temperatur", 0x3000)
        sensor1 = _sensor("Temp", 1, [dp])
        sensor2 = _sensor("Temp2", 2, [dp])  # Same address → duplicate unique_id
        device = _device("Wetterstation EG", sensors=[sensor1, sensor2])
        mapper = _mapper([device])
        sensors = mapper.get_entities_by_platform(Platform.SENSOR)
        # Should only have one entity for that address
        uids = [e.unique_id for e in sensors]
        assert len(uids) == len(set(uids))

    def test_maps_multiple_wetterstation_roles(self):
        roles = ["Temperatur", "Windgeschwindigkeit", "HelligkeitMitte"]
        datapoints = [_datapoint(r, 0x3000 + i) for i, r in enumerate(roles)]
        sensor = _sensor("Weather", 1, datapoints)
        device = _device("Wetterstation Dach", sensors=[sensor])
        mapper = _mapper([device])
        sensors = mapper.get_entities_by_platform(Platform.SENSOR)
        assert len(sensors) == len(roles)


# ── Query methods ─────────────────────────────────────────────────────────────


class TestQueryMethods:
    def setup_method(self):
        dp = _datapoint("OnOff", 0x0800)
        actuator = _actuator("Licht", 1, [dp])
        self.device = _device("Dev", actuators=[actuator], device_id="dev1")
        self.mapper = _mapper([self.device])

    def test_get_entities_by_platform(self):
        result = self.mapper.get_entities_by_platform(Platform.SWITCH)
        assert all(e.platform == Platform.SWITCH for e in result)

    def test_get_entity_by_unique_id_found(self):
        entity = self.mapper.entities[0]
        result = self.mapper.get_entity_by_unique_id(entity.unique_id)
        assert result is entity

    def test_get_entity_by_unique_id_not_found(self):
        result = self.mapper.get_entity_by_unique_id("nonexistent")
        assert result is None

    def test_get_group_address_label_map(self):
        ga_map = self.mapper.get_group_address_label_map()
        assert isinstance(ga_map, dict)
        # At least one entry for the light datapoint
        assert len(ga_map) >= 1

    def test_get_individual_address_label_map(self):
        ia_map = self.mapper.get_individual_address_label_map()
        assert isinstance(ia_map, dict)
        # Device has knx_address "1.1.1"
        assert "1.1.1" in ia_map

    def test_get_individual_address_label_map_skips_empty_ia(self):
        dp = _datapoint("OnOff", 0x0800)
        act = _actuator("L", 1, [dp])
        dev = MagicMock(spec=LXPDevice)
        dev.name = "D"
        dev.id = "d_no_ia"
        dev.address = None  # No KNX address
        dev.serial_number = "X"
        dev.actuators = [act]
        dev.sensors = []
        mapper = _mapper([dev])
        ia_map = mapper.get_individual_address_label_map()
        assert "None" not in ia_map


# ── Override error handling ───────────────────────────────────────────────────


class TestOverrideErrorHandling:
    def test_override_exception_is_caught(self):
        """If override_handler raises, mapper should log and continue."""
        from custom_components.luxor_living.override_handler import OverrideHandler

        dp = _datapoint("OnOff", 0x0800)
        actuator = _actuator("L", 1, [dp])
        device = _device("Dev", actuators=[actuator])
        project = _project([device])

        bad_handler = MagicMock(spec=OverrideHandler)
        bad_handler.apply_overrides = MagicMock(side_effect=RuntimeError("boom"))

        mapper = EntityMapper(project, override_handler=bad_handler)
        # Should not raise
        assert len(mapper.entities) > 0

    def test_health_entity_always_added(self):
        mapper = _mapper([])
        health = [e for e in mapper.entities if e.entity_type == "health"]
        assert len(health) == 1
        assert health[0].name == "System Health"
