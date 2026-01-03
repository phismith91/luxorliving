"""Tests for entity_mapper module - Comprehensive coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import Platform

from custom_components.luxor_living.entity_mapper import EntityMapper, MappedEntity
from custom_components.luxor_living.lxp_parser import (
    LXPActuator,
    LXPDatapoint,
    LXPDevice,
    LXPProject,
    LXPSensor,
)


def test_mapper_role_to_platform_mapping():
    """Test role to platform mapping constants."""
    from custom_components.luxor_living.entity_mapper import EntityMapper

    # Verify key mappings
    assert EntityMapper.ROLE_TO_PLATFORM["OnOff"] == Platform.LIGHT
    assert EntityMapper.ROLE_TO_PLATFORM["Dimmen%"] == Platform.LIGHT
    assert EntityMapper.ROLE_TO_PLATFORM["UpDown"] == Platform.COVER
    assert EntityMapper.ROLE_TO_PLATFORM["Temperature"] == Platform.SENSOR
    assert EntityMapper.ROLE_TO_PLATFORM["MasterSlave"] == Platform.BINARY_SENSOR
    assert EntityMapper.ROLE_TO_PLATFORM["Setpoint"] == Platform.CLIMATE


def test_mapper_role_to_unit_mapping():
    """Test role to unit of measurement mapping."""
    from custom_components.luxor_living.entity_mapper import EntityMapper

    # Verify unit mappings
    assert EntityMapper.ROLE_TO_UNIT["Temperature"] == "°C"
    assert EntityMapper.ROLE_TO_UNIT["Humidity"] == "%"
    assert EntityMapper.ROLE_TO_UNIT["Pressure"] == "hPa"
    assert EntityMapper.ROLE_TO_UNIT["CO2"] == "ppm"
    assert EntityMapper.ROLE_TO_UNIT["Brightness"] == "lx"


def test_mapped_entity_dataclass():
    """Test MappedEntity dataclass creation."""
    entity = MappedEntity(
        platform=Platform.LIGHT,
        unique_id="test_123",
        name="Test Light",
        device_name="Test Device",
        device_id="device_123",
        entity_type="dimmer",
        datapoints={"OnOff": 1, "Dimmen%": 2},
        attributes={"icon": "mdi:lightbulb"},
        parameters={"timer": "5"},
    )

    assert entity.platform == Platform.LIGHT
    assert entity.unique_id == "test_123"
    assert entity.name == "Test Light"
    assert entity.device_name == "Test Device"
    assert entity.device_id == "device_123"
    assert entity.entity_type == "dimmer"
    assert entity.datapoints == {"OnOff": 1, "Dimmen%": 2}
    assert entity.attributes == {"icon": "mdi:lightbulb"}
    assert entity.parameters == {"timer": "5"}


def test_entity_mapper_with_empty_project():
    """Test EntityMapper with a project with no devices."""
    with patch.object(EntityMapper, "map_all", return_value=[]):
        project = MagicMock(spec=LXPProject)
        project.devices = []

        mapper = EntityMapper(project)
        mapper.entities = []

        assert mapper.entities == []
        assert mapper.get_entities_by_platform(Platform.LIGHT) == []


def test_get_entities_by_platform():
    """Test getting entities filtered by platform."""
    project = MagicMock(spec=LXPProject)
    project.devices = []

    with patch.object(EntityMapper, "map_all", return_value=[]):
        mapper = EntityMapper(project)

        # Manually set entities
        mapper.entities = [
            MappedEntity(
                platform=Platform.LIGHT,
                unique_id="light_1",
                name="Light 1",
                device_name="Device",
                device_id="dev_1",
                entity_type="light",
                datapoints={},
                attributes={},
                parameters={},
            ),
            MappedEntity(
                platform=Platform.SWITCH,
                unique_id="switch_1",
                name="Switch 1",
                device_name="Device",
                device_id="dev_1",
                entity_type="switch",
                datapoints={},
                attributes={},
                parameters={},
            ),
            MappedEntity(
                platform=Platform.LIGHT,
                unique_id="light_2",
                name="Light 2",
                device_name="Device",
                device_id="dev_1",
                entity_type="light",
                datapoints={},
                attributes={},
                parameters={},
            ),
        ]

        lights = mapper.get_entities_by_platform(Platform.LIGHT)
        switches = mapper.get_entities_by_platform(Platform.SWITCH)
        covers = mapper.get_entities_by_platform(Platform.COVER)

        assert len(lights) == 2
        assert len(switches) == 1
        assert len(covers) == 0

        # Verify all lights are Platform.LIGHT
        for light in lights:
            assert light.platform == Platform.LIGHT


def test_get_entity_by_unique_id():
    """Test getting entity by unique ID."""
    project = MagicMock(spec=LXPProject)
    project.devices = []

    with patch.object(EntityMapper, "map_all", return_value=[]):
        mapper = EntityMapper(project)

        mapper.entities = [
            MappedEntity(
                platform=Platform.LIGHT,
                unique_id="unique_123",
                name="Test Light",
                device_name="Device",
                device_id="dev_1",
                entity_type="light",
                datapoints={},
                attributes={},
                parameters={},
            ),
        ]

        # Find by unique_id
        entity = mapper.get_entity_by_unique_id("unique_123")
        assert entity is not None
        assert entity.unique_id == "unique_123"
        assert entity.name == "Test Light"

        # Not found
        not_found = mapper.get_entity_by_unique_id("nonexistent")
        assert not_found is None


def test_determine_platform_light():
    """Test _determine_platform for light entities."""
    project = MagicMock(spec=LXPProject)
    project.devices = []

    with patch.object(EntityMapper, "map_all", return_value=[]):
        mapper = EntityMapper(project)

        # OnOff only -> Light
        platform = mapper._determine_platform({"OnOff": 1})
        assert platform == Platform.LIGHT

        # OnOff + Dimmen% -> Light
        platform = mapper._determine_platform({"OnOff": 1, "Dimmen%": 2})
        assert platform == Platform.LIGHT


def test_determine_platform_cover():
    """Test _determine_platform for cover entities."""
    project = MagicMock(spec=LXPProject)
    project.devices = []

    with patch.object(EntityMapper, "map_all", return_value=[]):
        mapper = EntityMapper(project)

        # UpDown -> Cover
        platform = mapper._determine_platform({"UpDown": 10})
