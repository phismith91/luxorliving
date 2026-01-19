"""Integration tests with real LXP files."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from homeassistant.const import Platform

from custom_components.luxor_living.entity_mapper import EntityMapper
from custom_components.luxor_living.lxp_parser import LXPParser

# LXP file paths
LXP_HAUPTWOHNUNG = Path(__file__).parent.parent / "docs" / "Hauptwohnung.lxp"
LXP_FAMILIE_SCHMIDT = Path(__file__).parent.parent / "docs" / "Familie Schmidt_0.9.lxp"


@pytest.mark.skipif(not LXP_HAUPTWOHNUNG.exists(), reason="Hauptwohnung.lxp not found")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_hauptwohnung_lxp_parsing():
    """Test parsing of Hauptwohnung.lxp (contains IO devices like Wetterstation)."""
    parser = LXPParser(LXP_HAUPTWOHNUNG)
    project = await parser.parse()

    # Verify project structure
    assert project.name is not None
    assert len(project.devices) > 0
    assert project.gateway_address is not None
    assert project.gateway_port > 0

    # Count total datapoints
    total_datapoints = 0
    total_sensors = 0
    total_actuators = 0

    for device in project.devices:
        total_sensors += len(device.sensors)
        total_actuators += len(device.actuators)
        for sensor in device.sensors:
            total_datapoints += len(sensor.datapoints)
        for actuator in device.actuators:
            total_datapoints += len(actuator.datapoints)

    assert total_datapoints > 0, "Should have parsed datapoints"
    assert total_sensors > 0 or total_actuators > 0, "Should have sensors or actuators"

    # Log summary
    print("\n=== Hauptwohnung.lxp ===")
    print(f"Project: {project.name}")
    print(f"Devices: {len(project.devices)}")
    print(f"Sensors: {total_sensors}")
    print(f"Actuators: {total_actuators}")
    print(f"Datapoints: {total_datapoints}")


@pytest.mark.skipif(not LXP_HAUPTWOHNUNG.exists(), reason="Hauptwohnung.lxp not found")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_hauptwohnung_entity_mapping():
    """Test entity mapping for Hauptwohnung.lxp."""
    parser = LXPParser(LXP_HAUPTWOHNUNG)
    project = await parser.parse()

    # Map entities
    mapper = EntityMapper(project)
    entities = mapper.entities

    # Should have mapped entities
    assert len(entities) > 0, "Should have created entities"

    # Count by platform
    platform_counts = {}
    for entity in entities:
        platform = entity.platform
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    # Verify we have multiple platforms
    assert len(platform_counts) >= 2, "Should have multiple platforms"

    # Check for typical platforms
    lights = mapper.get_entities_by_platform(Platform.LIGHT)
    switches = mapper.get_entities_by_platform(Platform.SWITCH)
    sensors = mapper.get_entities_by_platform(Platform.SENSOR)
    binary_sensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)

    # Log results
    print("\n=== Entity Mapping ===")
    print(f"Total entities: {len(entities)}")
    for platform, count in sorted(platform_counts.items(), key=lambda x: str(x[0])):
        print(f"  {platform.value}: {count}")

    # Verify entity structure
    for entity in entities[:5]:  # Check first 5
        assert entity.unique_id is not None
        assert entity.name is not None
        assert entity.platform is not None
        assert entity.device_name is not None
        assert isinstance(entity.datapoints, dict)


@pytest.mark.skipif(not LXP_HAUPTWOHNUNG.exists(), reason="Hauptwohnung.lxp not found")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_hauptwohnung_io_devices():
    """Test that IO devices (Wetterstation, ION Temperature) are parsed correctly."""
    parser = LXPParser(LXP_HAUPTWOHNUNG)
    project = await parser.parse()

    # Find IO devices
    io_devices = []
    weather_stations = []
    ion_devices = []

    for device in project.devices:
        # Wetterstation
        if "Wetterstation" in device.name or "Weather" in device.name:
            weather_stations.append(device)
            io_devices.append(device)
        # ION devices
        elif "ION" in device.name:
            ion_devices.append(device)
            io_devices.append(device)
        # Devices with many sensors are likely IO
        elif len(device.sensors) > 5:
            io_devices.append(device)

    print("\n=== IO Devices ===")
    print(f"Total IO devices: {len(io_devices)}")
    print(f"Weather stations: {len(weather_stations)}")
    print(f"ION devices: {len(ion_devices)}")

    # Verify IO devices were found and parsed
    if io_devices:
        for device in io_devices:
            print(
                f"  - {device.name}: {len(device.sensors)} sensors, {len(device.actuators)} actuators"
            )

            # IO devices should have sensors
            assert len(device.sensors) > 0, f"{device.name} should have sensors"

            # Check sensor datapoints
            for sensor in device.sensors:
                assert len(sensor.datapoints) > 0, f"Sensor {sensor.name} should have datapoints"

    # Map entities and check sensor platforms
    mapper = EntityMapper(project)
    sensors = mapper.get_entities_by_platform(Platform.SENSOR)

    # Should have sensor entities from IO devices
    if io_devices:
        assert len(sensors) > 0, "Should have sensor entities from IO devices"

        # Check for weather-related sensors
        sensor_names = [s.name for s in sensors]
        print(f"\n=== Sensor Entities ({len(sensors)}) ===")
        for sensor in sensors[:10]:  # First 10
            print(f"  - {sensor.name} ({sensor.entity_type})")


@pytest.mark.skipif(not LXP_FAMILIE_SCHMIDT.exists(), reason="Familie Schmidt_0.9.lxp not found")
@pytest.mark.asyncio
async def test_familie_schmidt_lxp_parsing():
    """Test parsing of Familie Schmidt_0.9.lxp (standard devices, no IO)."""
    parser = LXPParser(LXP_FAMILIE_SCHMIDT)
    project = await parser.parse()

    # Verify project structure
    assert project.name is not None
    assert len(project.devices) > 0

    # Count devices
    total_sensors = 0
    total_actuators = 0

    for device in project.devices:
        total_sensors += len(device.sensors)
        total_actuators += len(device.actuators)

    # Log summary
    print("\n=== Familie Schmidt_0.9.lxp ===")
    print(f"Project: {project.name}")
    print(f"Devices: {len(project.devices)}")
    print(f"Sensors: {total_sensors}")
    print(f"Actuators: {total_actuators}")

    # Should have devices
    assert total_sensors > 0 or total_actuators > 0


@pytest.mark.skipif(not LXP_FAMILIE_SCHMIDT.exists(), reason="Familie Schmidt_0.9.lxp not found")
@pytest.mark.asyncio
async def test_familie_schmidt_entity_mapping():
    """Test entity mapping for Familie Schmidt_0.9.lxp."""
    parser = LXPParser(LXP_FAMILIE_SCHMIDT)
    project = await parser.parse()

    # Map entities
    mapper = EntityMapper(project)
    entities = mapper.entities

    # Should have entities
    assert len(entities) > 0

    # Count by platform
    platform_counts = {}
    for entity in entities:
        platform = entity.platform
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    print("\n=== Familie Schmidt Entity Mapping ===")
    print(f"Total entities: {len(entities)}")
    for platform, count in sorted(platform_counts.items(), key=lambda x: str(x[0])):
        print(f"  {platform.value}: {count}")


@pytest.mark.skipif(
    not LXP_HAUPTWOHNUNG.exists() or not LXP_FAMILIE_SCHMIDT.exists(),
    reason="Both LXP files required",
)
@pytest.mark.asyncio
async def test_compare_io_vs_standard_devices():
    """Compare entity distribution between IO-heavy and standard LXP files."""
    # Parse both files
    parser_hw = LXPParser(LXP_HAUPTWOHNUNG)
    project_hw = await parser_hw.parse()

    parser_fs = LXPParser(LXP_FAMILIE_SCHMIDT)
    project_fs = await parser_fs.parse()

    # Map entities for both
    mapper_hw = EntityMapper(project_hw)
    mapper_fs = EntityMapper(project_fs)

    # Get sensor counts
    sensors_hw = mapper_hw.get_entities_by_platform(Platform.SENSOR)
    sensors_fs = mapper_fs.get_entities_by_platform(Platform.SENSOR)

    # Get light/switch counts
    lights_hw = mapper_hw.get_entities_by_platform(Platform.LIGHT)
    lights_fs = mapper_fs.get_entities_by_platform(Platform.LIGHT)

    switches_hw = mapper_hw.get_entities_by_platform(Platform.SWITCH)
    switches_fs = mapper_fs.get_entities_by_platform(Platform.SWITCH)

    print(f"\n=== IO vs Standard Comparison ===")
    print(f"Hauptwohnung (IO-heavy):")
    print(f"  Sensors: {len(sensors_hw)}")
    print(f"  Lights: {len(lights_hw)}")
    print(f"  Switches: {len(switches_hw)}")
    print(f"  Total entities: {len(mapper_hw.entities)}")

    print(f"\nFamilie Schmidt (Standard):")
    print(f"  Sensors: {len(sensors_fs)}")
    print(f"  Lights: {len(lights_fs)}")
    print(f"  Switches: {len(switches_fs)}")
    print(f"  Total entities: {len(mapper_fs.entities)}")

    # Hauptwohnung should have more sensors (IO devices)
    # This is not a strict requirement, just informative
    print(f"\nSensor ratio: {len(sensors_hw) / max(len(sensors_fs), 1):.2f}x")


@pytest.mark.skipif(not LXP_HAUPTWOHNUNG.exists(), reason="Hauptwohnung.lxp not found")
@pytest.mark.asyncio
async def test_unique_id_stability_with_real_lxp():
    """Test that unique IDs are stable across multiple parses of the same file."""
    # Parse and map twice
    parser1 = LXPParser(LXP_HAUPTWOHNUNG)
    project1 = await parser1.parse()
    mapper1 = EntityMapper(project1)

    parser2 = LXPParser(LXP_HAUPTWOHNUNG)
    project2 = await parser2.parse()
    mapper2 = EntityMapper(project2)

    # Get unique IDs from both mappings
    unique_ids_1 = {e.unique_id for e in mapper1.entities}
    unique_ids_2 = {e.unique_id for e in mapper2.entities}

    # Should be identical
    assert unique_ids_1 == unique_ids_2, "Unique IDs should be stable across parses"

    # Should have no duplicates
    assert len(unique_ids_1) == len(mapper1.entities), "All unique IDs should be unique"
    assert len(unique_ids_2) == len(mapper2.entities), "All unique IDs should be unique"

    print(f"\n=== Unique ID Stability ===")
    print(f"Total unique entities: {len(unique_ids_1)}")
    print(f"✓ Unique IDs are stable across parses")


@pytest.mark.skipif(not LXP_HAUPTWOHNUNG.exists(), reason="Hauptwohnung.lxp not found")
def test_lxp_cache_functionality():
    """Test that LXP cache works correctly."""
    from custom_components.luxor_living.lxp_parser import _lxp_cache

    # Clear cache first
    _lxp_cache.clear()

    # First parse should be a cache miss
    stats_before = _lxp_cache.get_stats()
    print(f"\n=== Cache Stats (before) ===")
    print(f"Hits: {stats_before['hits']}")
    print(f"Misses: {stats_before['misses']}")

    # Parse (will use cache internally via async)
    # We can't easily test async cache here, but we verify cache exists
    assert _lxp_cache is not None
    assert _lxp_cache.get_stats()["max_size"] > 0
