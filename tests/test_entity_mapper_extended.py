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


def _device(
    name: str,
    actuators=None,
    sensors=None,
    device_id="dev_001",
    device_type="",
) -> LXPDevice:
    d = MagicMock(spec=LXPDevice)
    d.name = name
    d.id = device_id
    d.address = "1.1.1"
    d.serial_number = "SN123"
    d.actuators = actuators or []
    d.sensors = sensors or []
    d.device_type = device_type
    d.app_id = ""
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

    def test_maps_onoff_sensor_to_binary_sensor_by_default(self):
        """Sensors are input devices — OnOff always maps to binary_sensor, never switch."""
        dp = _datapoint("OnOff", 0x1000)
        sensor = _sensor("Contact", 1, [dp])
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        bsensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
        non_health = [e for e in bsensors if e.entity_type != "health"]
        assert len(non_health) > 0
        switches = mapper.get_entities_by_platform(Platform.SWITCH)
        assert len(switches) == 0

    def test_onoff_and_status_onoff_together_maps_to_binary_sensor(self):
        """B6 channels report both OnOff and status@OnOff — must be binary_sensor, not switch."""
        dp_onoff = _datapoint("OnOff", 0x1000)
        dp_status = _datapoint("status@OnOff", 0x1001)
        sensor = _sensor("B6 Kanal", 1, [dp_onoff, dp_status])
        device = _device("B6-1", sensors=[sensor])
        mapper = _mapper([device])
        bsensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
        non_health = [e for e in bsensors if e.entity_type != "health"]
        assert len(non_health) == 1
        assert non_health[0].entity_type == "binary_sensor"
        switches = mapper.get_entities_by_platform(Platform.SWITCH)
        assert len(switches) == 0

    def test_b6_rauchmelder_channel_is_binary_sensor(self):
        """B6 smoke detector channel (sensorCase=12, OnOff only) → binary_sensor."""
        dp = _datapoint("OnOff", 0x2B10)
        sensor = _sensor("B6-1 C4 - Rauchmelder", 3, [dp], sensor_type=0)
        sensor.parameters = {"sensorCase": "12", "sensorTyp": "0", "kontaktCase": "0"}
        device = _device("B6-1", sensors=[sensor])
        mapper = _mapper([device])
        bsensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
        non_health = [e for e in bsensors if e.entity_type != "health"]
        assert len(non_health) == 1
        switches = mapper.get_entities_by_platform(Platform.SWITCH)
        assert len(switches) == 0

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

    def test_maps_regen_to_binary_sensor(self):
        dp = _datapoint("Regen", 0x3001)
        sensor = _sensor("Rain", 1, [dp])
        device = _device("Wetterstation EG", sensors=[sensor])
        mapper = _mapper([device])
        binary_sensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
        regen_entity = next(
            (e for e in binary_sensors if "Regen" in e.name or e.entity_type == "regen"), None
        )
        assert regen_entity is not None, "Expected a binary_sensor entity for the Regen role"

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

    def test_helligkeit_roles_map_to_physically_correct_position(self):
        """Confirmed via #141: LXP role text does not match physical sensor position.

        Only HelligkeitMitte is actually swapped (it's physically "Links");
        HelligkeitLinks and HelligkeitRechts are physically correct as-is.
        The rc.9 fix rotated all three one step too far — Marcus's rc.9 report
        showed Rechts/Vorne inverted, proving Links/Rechts should not move:
          role HelligkeitMitte  (addr 10244) is physically "Links"
          role HelligkeitLinks  (addr 10243) is physically "Vorne"
          role HelligkeitRechts (addr 10245) is physically "Rechts"
        """
        roles = ["HelligkeitMitte", "HelligkeitLinks", "HelligkeitRechts"]
        datapoints = [
            _datapoint(
                r, 10244 if r == "HelligkeitMitte" else 10243 if r == "HelligkeitLinks" else 10245
            )
            for r in roles
        ]
        sensor = _sensor("Weather", 1, datapoints)
        device = _device("Wetterstation Dach", sensors=[sensor])
        mapper = _mapper([device])
        sensors = mapper.get_entities_by_platform(Platform.SENSOR)

        by_addr = {addr: e.name for e in sensors for addr in e.datapoints.values()}
        assert "Links" in by_addr[10244]
        assert "Vorne" in by_addr[10243]
        assert "Rechts" in by_addr[10245]


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


# ── Climate mapping ───────────────────────────────────────────────────────────


class TestClimateMapping:
    def test_maps_rtr_sensor_to_climate(self):
        """Sensor with activateRTR=1, Istwert, Sollwert → Platform.CLIMATE."""
        dp_ist = _datapoint("Istwert", 8449)
        dp_soll = _datapoint("Sollwert", 8193)
        dp_status = _datapoint("status@Sollwert", 8961)
        dp_switch = _datapoint("UmschaltenHeitzenKühlen", 10247)
        sensor = _sensor("iON8 Wohnzimmer (°C)", 0, [dp_ist, dp_soll, dp_status, dp_switch])
        sensor.parameters = {"activateRTR": "1", "heatingCoolingFormat": "1"}
        device = _device("iON8 Wohnzimmer", sensors=[sensor])
        mapper = _mapper([device])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 1
        assert climate_entities[0].entity_type == "climate"

    def test_rtr_climate_has_correct_datapoints(self):
        """RTR sensor climate entity contains all heating datapoints."""
        dp_ist = _datapoint("Istwert", 8449)
        dp_soll = _datapoint("Sollwert", 8193)
        dp_status = _datapoint("status@Sollwert", 8961)
        sensor = _sensor("RTR", 0, [dp_ist, dp_soll, dp_status])
        sensor.parameters = {"activateRTR": "1"}
        device = _device("Panel", sensors=[sensor])
        mapper = _mapper([device])
        entity = mapper.get_entities_by_platform(Platform.CLIMATE)[0]
        assert entity.datapoints["Istwert"] == 8449
        assert entity.datapoints["Sollwert"] == 8193
        assert entity.datapoints["status@Sollwert"] == 8961

    def test_sensor_without_activate_rtr_not_mapped_to_climate(self):
        """Sensor without activateRTR=1 is not mapped to climate even with Istwert/Sollwert."""
        dp_ist = _datapoint("Istwert", 8449)
        dp_soll = _datapoint("Sollwert", 8193)
        sensor = _sensor("Plain Sensor", 0, [dp_ist, dp_soll])
        sensor.parameters = {}
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 0

    def test_maps_heating_actuator_to_climate(self):
        """Actuator with heizungsart, Istwert, Sollwert → Platform.CLIMATE."""
        dp_ist = _datapoint("Istwert", 8456)
        dp_soll = _datapoint("Sollwert", 8200)
        dp_status = _datapoint("StatusSollwert", 8968)
        actuator = _actuator("Infrarot Heizung", 0, [dp_ist, dp_soll, dp_status])
        actuator.parameters = {"heizungsart": "51", "maxSollwert": "15"}
        device = _device("H6 Spielzimmer", actuators=[actuator])
        mapper = _mapper([device])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 1
        assert climate_entities[0].entity_type == "climate"

    def test_actuator_without_heizungsart_not_mapped_to_climate(self):
        """Actuator with Istwert/Sollwert but no heizungsart parameter is not climate."""
        dp_ist = _datapoint("Istwert", 8456)
        dp_soll = _datapoint("Sollwert", 8200)
        actuator = _actuator("Unknown Actuator", 0, [dp_ist, dp_soll])
        actuator.parameters = {}
        device = _device("Dev", actuators=[actuator])
        mapper = _mapper([device])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 0

    def test_rtr_and_h6_sharing_istwert_both_get_entities(self):
        """iON RTR and H6 sharing an Istwert are separate devices — both get an entity.

        Wall panel and valve driver are independent physical units.
        """
        shared_istwert = 8456
        dp_ist_s = _datapoint("Istwert", shared_istwert)
        dp_soll_s = _datapoint("Sollwert", 8200)
        dp_status_s = _datapoint("status@Sollwert", 8968)
        sensor = _sensor("RTR Panel", 0, [dp_ist_s, dp_soll_s, dp_status_s])
        sensor.parameters = {"activateRTR": "1"}
        dp_ist_a = _datapoint("Istwert", shared_istwert)
        dp_soll_a = _datapoint("Sollwert", 8200)
        dp_status_a = _datapoint("StatusSollwert", 8968)
        actuator = _actuator("H6 Valve", 0, [dp_ist_a, dp_soll_a, dp_status_a])
        actuator.parameters = {"heizungsart": "230"}
        sensor_device = _device("iON Panel", sensors=[sensor], device_id="panel_dev")
        actuator_device = _device("H6", actuators=[actuator], device_id="h6_dev")
        mapper = _mapper([sensor_device, actuator_device])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 2


class TestR718ThermostatMapping:
    def test_maps_r718_to_climate(self):
        """R718 sensor with Istwert+Sollwert+status@Sollwert but no activateRTR → Platform.CLIMATE."""
        dp_ist = _datapoint("Istwert", 7680)
        dp_soll = _datapoint("Sollwert", 7424)
        dp_status = _datapoint("status@Sollwert", 7936)
        sensor = _sensor("7 R718 105", 0, [dp_ist, dp_soll, dp_status])
        sensor.parameters = {"abgleichwert": "0"}
        device = _device("7 R718 105", sensors=[sensor])
        mapper = _mapper([device])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 1
        assert climate_entities[0].entity_type == "climate"

    def test_r718_climate_has_correct_datapoints(self):
        """R718 climate entity exposes all three thermostat datapoints."""
        dp_ist = _datapoint("Istwert", 7680)
        dp_soll = _datapoint("Sollwert", 7424)
        dp_status = _datapoint("status@Sollwert", 7936)
        sensor = _sensor("R718", 0, [dp_ist, dp_soll, dp_status])
        sensor.parameters = {"abgleichwert": "0"}
        device = _device("R718 Dev", sensors=[sensor])
        mapper = _mapper([device])
        entity = mapper.get_entities_by_platform(Platform.CLIMATE)[0]
        assert entity.datapoints["Istwert"] == 7680
        assert entity.datapoints["Sollwert"] == 7424
        assert entity.datapoints["status@Sollwert"] == 7936

    def test_r718_with_umschalten_has_umschalten_datapoint(self):
        """R718 with UmschaltenHeitzenKühlen datapoint passes it through to entity."""
        dp_ist = _datapoint("Istwert", 7680)
        dp_soll = _datapoint("Sollwert", 7424)
        dp_status = _datapoint("status@Sollwert", 7936)
        dp_umschalten = _datapoint("UmschaltenHeitzenKühlen", 8192)
        sensor = _sensor("R718", 0, [dp_ist, dp_soll, dp_status, dp_umschalten])
        sensor.parameters = {"abgleichwert": "0"}
        device = _device("R718 Dev", sensors=[sensor])
        mapper = _mapper([device])
        entity = mapper.get_entities_by_platform(Platform.CLIMATE)[0]
        assert entity.datapoints["UmschaltenHeitzenKühlen"] == 8192

    def test_sensor_with_only_istwert_and_sollwert_not_r718(self):
        """Sensor with Istwert+Sollwert but no status@Sollwert is not mapped as R718 climate."""
        dp_ist = _datapoint("Istwert", 7680)
        dp_soll = _datapoint("Sollwert", 7424)
        sensor = _sensor("Plain Temp", 0, [dp_ist, dp_soll])
        sensor.parameters = {}
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 0

    def test_activate_rtr_zero_with_status_sollwert_maps_as_r718(self):
        """activateRTR=0 (not '1') + status@Sollwert → treated as R718, not iON RTR."""
        dp_ist = _datapoint("Istwert", 7680)
        dp_soll = _datapoint("Sollwert", 7424)
        dp_status = _datapoint("status@Sollwert", 7936)
        sensor = _sensor("Thermostat", 0, [dp_ist, dp_soll, dp_status])
        sensor.parameters = {"activateRTR": "0"}
        device = _device("Dev", sensors=[sensor])
        mapper = _mapper([device])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 1
        assert climate_entities[0].platform == Platform.CLIMATE

    def test_r718_and_h6_sharing_istwert_both_get_entities(self):
        """R718 and H6 sharing KNX addresses must both produce a climate entity.

        Regression fix for issue #141 (introduced in v1.1.7).
        """
        shared = 7680
        dp_ist_s = _datapoint("Istwert", shared)
        dp_soll_s = _datapoint("Sollwert", 7424)
        dp_status_s = _datapoint("status@Sollwert", 7936)
        sensor = _sensor("R718", 0, [dp_ist_s, dp_soll_s, dp_status_s])
        sensor.parameters = {"abgleichwert": "0"}
        dp_ist_a = _datapoint("Istwert", shared)
        dp_soll_a = _datapoint("Sollwert", 7424)
        actuator = _actuator("H6", 0, [dp_ist_a, dp_soll_a])
        actuator.parameters = {"heizungsart": "230"}
        s_dev = _device("R718 Dev", sensors=[sensor], device_id="r718_dev")
        a_dev = _device("H6 Dev", actuators=[actuator], device_id="h6_dev")
        mapper = _mapper([s_dev, a_dev])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 2
        unique_ids = {e.unique_id for e in climate_entities}
        assert len(unique_ids) == 2


class TestH6WithinDeviceDedup:
    """Within a single H6 device, channels sharing the same Istwert address must produce one entity."""

    def test_two_h6_channels_same_istwert_one_entity(self):
        shared_istwert = 8457
        act_ch2 = _actuator(
            "Chauffage salon 1",
            2,
            [_datapoint("Istwert", shared_istwert), _datapoint("Sollwert", 8201)],
        )
        act_ch2.parameters = {"heizungsart": "230"}
        act_ch5 = _actuator(
            "Chauffage salon 2",
            5,
            [_datapoint("Istwert", shared_istwert), _datapoint("Sollwert", 8201)],
        )
        act_ch5.parameters = {"heizungsart": "230"}
        device = _device("511 H6", actuators=[act_ch2, act_ch5], device_id="h6_511")
        mapper = _mapper([device])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 1

    def test_two_h6_devices_same_istwert_two_entities(self):
        act1 = _actuator("Zone A", 0, [_datapoint("Istwert", 8457), _datapoint("Sollwert", 8200)])
        act1.parameters = {"heizungsart": "230"}
        act2 = _actuator("Zone A′", 0, [_datapoint("Istwert", 8457), _datapoint("Sollwert", 8201)])
        act2.parameters = {"heizungsart": "230"}
        dev1 = _device("H6 A", actuators=[act1], device_id="h6_A")
        dev2 = _device("H6 B", actuators=[act2], device_id="h6_B")
        mapper = _mapper([dev1, dev2])
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate_entities) == 2


class TestUniqueIdCollisionGuard:
    """Same-platform unique_id collisions must be disambiguated.

    HA's entity registry silently drops the second entity of a platform when
    two entities share a unique_id (real case: S1 Garage in the Kennel project,
    light 'Prise eau garage' + binary_sensor 'Eingang C1' both on address 2089).
    """

    def test_same_platform_collision_gets_channel_suffix(self):
        act1 = _actuator("Light A", 1, [_datapoint("OnOff", 2089)])
        act2 = _actuator("Light B", 2, [_datapoint("OnOff", 2089)])
        device = _device("S1 Garage", actuators=[act1, act2], device_id="s1")
        mapper = _mapper([device])
        lights = mapper.get_entities_by_platform(Platform.LIGHT)
        assert len(lights) == 2
        uids = {e.unique_id for e in lights}
        assert len(uids) == 2, f"unique_ids collide: {uids}"
        # First claimant keeps the legacy id so existing registries stay intact
        assert lights[0].unique_id == "s1_2089"
        assert lights[1].unique_id == "s1_2089_ch2"

    def test_cross_platform_same_address_uids_unchanged(self):
        """Cross-platform duplicates are HA-legal and must stay byte-stable.

        Renaming either would orphan already-registered entities.
        """
        act = _actuator("Prise eau garage", 1, [_datapoint("OnOff", 2089)])
        sen = _sensor("Eingang C1", 3, [_datapoint("OnOff", 2089)])
        device = _device("S1 Garage", actuators=[act], sensors=[sen], device_id="s1")
        mapper = _mapper([device])
        light = mapper.get_entities_by_platform(Platform.LIGHT)[0]
        binary = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)[0]
        assert light.unique_id == "s1_2089"
        assert binary.unique_id == "s1_2089"

    def test_no_suffix_when_no_collision(self):
        act1 = _actuator("Light A", 1, [_datapoint("OnOff", 2089)])
        act2 = _actuator("Light B", 2, [_datapoint("OnOff", 2090)])
        device = _device("S1 Garage", actuators=[act1, act2], device_id="s1")
        mapper = _mapper([device])
        lights = mapper.get_entities_by_platform(Platform.LIGHT)
        assert {e.unique_id for e in lights} == {"s1_2089", "s1_2090"}

    def test_triple_collision_stays_unique(self):
        acts = [_actuator(f"Light {i}", i, [_datapoint("OnOff", 2089)]) for i in (1, 2, 3)]
        device = _device("S1 Garage", actuators=acts, device_id="s1")
        mapper = _mapper([device])
        lights = mapper.get_entities_by_platform(Platform.LIGHT)
        uids = [e.unique_id for e in lights]
        assert len(set(uids)) == 3, f"unique_ids collide: {uids}"
        assert uids[0] == "s1_2089"


class TestAppIdBasedDeviceCategory:
    """entity_mapper skips input_only and unsupported devices via device_type."""

    def test_input_only_device_produces_no_entities(self):
        """T4 (input_only) yields zero entities regardless of datapoints."""
        dp = _datapoint("OnOff", 2048)
        sensor = _sensor("T4 Ch1", 1, [dp])
        device = _device("T4 Panel", sensors=[sensor], device_type="T4")
        mapper = _mapper([device])
        # Health entity is always added; subtract it
        non_health = [e for e in mapper.entities if e.entity_type != "health"]
        assert len(non_health) == 0

    def test_unsupported_device_produces_no_entities(self):
        """M130 (unsupported) yields zero entities."""
        dp = _datapoint("OnOff", 3072)
        sensor = _sensor("M130 Ch1", 1, [dp])
        device = _device("M130 Meter", sensors=[sensor], device_type="M130")
        mapper = _mapper([device])
        non_health = [e for e in mapper.entities if e.entity_type != "health"]
        assert len(non_health) == 0

    def test_unknown_device_type_falls_through_to_heuristics(self):
        """Empty device_type falls through to existing heuristic detection."""
        dp = _datapoint("OnOff", 2048)
        actuator = _actuator("Switch", 1, [dp])
        device = _device("Unknown Dev", actuators=[actuator], device_type="")
        mapper = _mapper([device])
        non_health = [e for e in mapper.entities if e.entity_type != "health"]
        assert len(non_health) == 1

    def test_known_supported_device_type_falls_through_to_heuristics(self):
        """Known but supported type (e.g. H6) still uses heuristic for entity details."""
        dp_ist = _datapoint("Istwert", 1024)
        dp_soll = _datapoint("Sollwert", 1280)
        actuator = _actuator("H6 Ch1", 1, [dp_ist, dp_soll])
        actuator.parameters = {"heizungsart": "230"}
        device = _device("H6 Dev", actuators=[actuator], device_type="H6")
        mapper = _mapper([device])
        climate = mapper.get_entities_by_platform(Platform.CLIMATE)
        assert len(climate) == 1
