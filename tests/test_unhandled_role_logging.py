"""Tests for unhandled-role logging in EntityMapper.

Verifies:
- Actuator/sensor with a known-but-intentionally-skipped role (Scene, ZentralAus)
  → no entity created, DEBUG log only (no WARNING).
- Actuator/sensor with a truly unknown role
  → no entity created, WARNING log containing the unknown role name.
- Scene role is explicitly None in PlatformDetector (not Platform.SCENE).
"""

import logging
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
from custom_components.luxor_living.platform_detector import PlatformDetector

# ── Helpers (mirrors test_entity_mapper_extended.py) ─────────────────────────


def _dp(role: str, address: int = 1) -> LXPDatapoint:
    dp = MagicMock(spec=LXPDatapoint)
    dp.role = role
    dp.address = address
    return dp


def _actuator(name: str, datapoints: list) -> LXPActuator:
    a = MagicMock(spec=LXPActuator)
    a.name = name
    a.channel = 1
    a.datapoints = datapoints
    a.on_icon = a.off_icon = a.use_case = ""
    a.parameters = {}
    return a


def _sensor(name: str, datapoints: list) -> LXPSensor:
    s = MagicMock(spec=LXPSensor)
    s.name = name
    s.channel = 1
    s.datapoints = datapoints
    s.sensor_type = 0
    s.parameters = {}
    return s


def _device(actuators=None, sensors=None) -> LXPDevice:
    d = MagicMock(spec=LXPDevice)
    d.name = "TestDevice"
    d.id = "dev_test"
    d.address = "1.1.1"
    d.serial_number = "SN0"
    d.actuators = actuators or []
    d.sensors = sensors or []
    return d


def _mapper(*devices: LXPDevice) -> EntityMapper:
    p = MagicMock(spec=LXPProject)
    p.devices = list(devices)
    return EntityMapper(p)


def _user_entities(mapper: EntityMapper):
    """Return only user-device entities, excluding the always-present System Health entry."""
    return [e for e in mapper.entities if e.entity_type != "health"]


# ── PlatformDetector: Scene explicitly None ───────────────────────────────────


@pytest.mark.smoke
def test_scene_role_is_not_mapped_to_platform():
    """Scene must be None — HA's own scene system supersedes KNX scene addresses."""
    detector = PlatformDetector()
    assert detector.detect_platform("Scene") is None
    assert "Scene" in PlatformDetector.ROLE_TO_PLATFORM


# ── Actuator: known-skipped role → DEBUG only, no WARNING ────────────────────


@pytest.mark.smoke
def test_scene_actuator_skipped_without_warning(caplog):
    """Actuator with only Scene datapoints: skipped, no WARNING emitted."""
    dev = _device(actuators=[_actuator("Szene Wohnzimmer", [_dp("Scene")])])
    with caplog.at_level(logging.DEBUG, logger="custom_components.luxor_living.entity_mapper"):
        mapper = _mapper(dev)

    assert _user_entities(mapper) == []
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert not warnings, f"Unexpected WARNING: {[r.message for r in warnings]}"


@pytest.mark.smoke
def test_zentral_aus_actuator_skipped_without_warning(caplog):
    """Actuator with ZentralAus role: skipped quietly (intentional, not an entity)."""
    dev = _device(actuators=[_actuator("Zentral Aus", [_dp("ZentralAus")])])
    with caplog.at_level(logging.DEBUG, logger="custom_components.luxor_living.entity_mapper"):
        mapper = _mapper(dev)

    assert _user_entities(mapper) == []
    assert not any(r.levelno >= logging.WARNING for r in caplog.records)


# ── Actuator: unknown role → WARNING with role name ──────────────────────────


@pytest.mark.smoke
def test_unknown_actuator_role_emits_warning(caplog):
    """Actuator with an unrecognised role emits a WARNING containing the role name."""
    unknown_role = "FutureRolleXYZ"
    dev = _device(actuators=[_actuator("Mystery Device", [_dp(unknown_role)])])
    with caplog.at_level(logging.WARNING, logger="custom_components.luxor_living.entity_mapper"):
        mapper = _mapper(dev)

    assert _user_entities(mapper) == []
    warning_messages = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
    assert any(
        unknown_role in msg for msg in warning_messages
    ), f"Expected WARNING mentioning '{unknown_role}', got: {warning_messages}"


# ── Sensor: unknown role → WARNING with role name ────────────────────────────


@pytest.mark.smoke
def test_unknown_sensor_role_emits_warning(caplog):
    """Sensor with an unrecognised role emits a WARNING containing the role name."""
    unknown_role = "SomeNewSensorType42"
    dev = _device(sensors=[_sensor("Mystery Sensor", [_dp(unknown_role)])])
    with caplog.at_level(logging.WARNING, logger="custom_components.luxor_living.entity_mapper"):
        mapper = _mapper(dev)

    assert _user_entities(mapper) == []
    warning_messages = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
    assert any(
        unknown_role in msg for msg in warning_messages
    ), f"Expected WARNING mentioning '{unknown_role}', got: {warning_messages}"


# ── Sanity: known roles still produce entities ────────────────────────────────


@pytest.mark.smoke
def test_known_role_still_creates_entity(caplog):
    """Regression guard: OnOff actuator must still produce a light entity."""
    dev = _device(actuators=[_actuator("Licht", [_dp("OnOff", 100)])])
    with caplog.at_level(logging.WARNING, logger="custom_components.luxor_living.entity_mapper"):
        mapper = _mapper(dev)

    entities = _user_entities(mapper)
    assert len(entities) == 1
    assert entities[0].platform == Platform.LIGHT
    assert not any(r.levelno >= logging.WARNING for r in caplog.records)
