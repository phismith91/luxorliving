#!/usr/bin/env python3
"""Test integration setup."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.luxor_living.entity_mapper import EntityMapper
from custom_components.luxor_living.lxp_parser import LXPParser


def main():
    """Test full integration flow."""
    # Find LXP file - try multiple locations
    possible_paths = [
        Path(__file__).parent.parent / "Familie Schmidt_0.9.lxp",
        Path.home() / "Nextcloud/Projekte_Rechner/Madeira/Schmidt_Madeira_V0.8.lxp",
        Path.home() / "Nextcloud/Projekte_Rechner/Madeira/Madeira.lxp",
    ]

    lxp_file = None
    for path in possible_paths:
        if path.exists():
            lxp_file = path
            break

    if not lxp_file:
        print(f"❌ No LXP file found. Tried:")
        for path in possible_paths:
            print(f"   - {path}")
        return

    print(f"✅ Found LXP file: {lxp_file}")

    # Parse LXP
    print("\n📖 Parsing LXP file...")
    parser = LXPParser(str(lxp_file))
    project = parser.parse()

    print(f"   Project: {project.name}")
    print(f"   Devices: {len(project.devices)}")

    # Count total datapoints
    total_datapoints = 0
    for device in project.devices:
        for sensor in device.sensors:
            total_datapoints += len(sensor.datapoints)
        for actuator in device.actuators:
            total_datapoints += len(actuator.datapoints)

    print(f"   Datapoints: {total_datapoints}")

    # Create mapper
    print("\n🗺️  Creating entity mapper...")
    mapper = EntityMapper(project)
    entities = mapper.entities  # Use entities attribute directly

    print(f"   Total entities: {len(entities)}")

    # Count by platform
    from homeassistant.const import Platform

    platform_counts = {}
    for entity in entities:
        platform = entity.platform
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    print("\n📊 Entity breakdown:")
    for platform, count in sorted(platform_counts.items(), key=lambda x: str(x[0])):
        print(f"   {platform.value}: {count}")

    # Show sample entities
    print("\n💡 Sample Light entities:")
    lights = mapper.get_entities_by_platform(Platform.LIGHT)
    for light in lights[:5]:
        print(f"   - {light.name} ({light.entity_type})")
        print(f"     Device: {light.device_name}")
        print(f"     Datapoints: {list(light.datapoints.keys())}")

    print("\n🔌 Sample Switch entities:")
    switches = mapper.get_entities_by_platform(Platform.SWITCH)
    for switch in switches[:5]:
        print(f"   - {switch.name}")
        print(f"     Device: {switch.device_name}")
        print(f"     Datapoints: {list(switch.datapoints.keys())}")

    print("\n📡 Binary Sensor entities:")
    sensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
    for sensor in sensors:
        print(f"   - {sensor.name} ({sensor.entity_type})")
        print(f"     Device: {sensor.device_name}")
        print(f"     Datapoints: {list(sensor.datapoints.keys())}")

    print("\n✅ Integration test completed successfully!")


if __name__ == "__main__":
    main()
