#!/usr/bin/env python3
"""Test script for entity mapper."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from homeassistant.const import Platform

from custom_components.luxor_living.entity_mapper import EntityMapper
from custom_components.luxor_living.lxp_parser import LXPParser


def main():
    """Test the entity mapper."""
    lxp_file = Path("/home/phil/Nextcloud/Familie Schmidt_0.9.lxp")

    if not lxp_file.exists():
        print(f"❌ LXP file not found: {lxp_file}")
        return

    print(f"📄 Parsing: {lxp_file.name}")
    print("=" * 60)

    # Parse LXP
    parser = LXPParser(lxp_file)
    project = parser.parse()

    print(f"\n🏠 Project: {project.name}")
    print(f"📦 Devices: {len(project.devices)}")

    # Map entities
    print("\n🗺️  Mapping entities...")
    mapper = EntityMapper(project)
    entities = mapper.map_all()

    print("\n" + "=" * 60)
    print(f"✅ Mapped {len(entities)} entities")

    # Group by platform
    platforms = {}
    for entity in entities:
        if entity.platform not in platforms:
            platforms[entity.platform] = []
        platforms[entity.platform].append(entity)

    print("\n📊 By Platform:")
    for platform, ents in sorted(platforms.items(), key=lambda x: x[0].value):
        print(f"   {platform.value}: {len(ents)}")

    # Show lights
    lights = mapper.get_entities_by_platform(Platform.LIGHT)
    print(f"\n💡 Lights ({len(lights)}):")
    for light in lights[:10]:  # First 10
        dp_info = ", ".join([f"{k}: {v}" for k, v in light.datapoints.items()])
        print(f"   • {light.name}")
        print(f"     Type: {light.entity_type}")
        print(f"     Device: {light.device_name}")
        print(f"     Datapoints: {dp_info}")

    if len(lights) > 10:
        print(f"   ... and {len(lights) - 10} more")

    # Show binary sensors
    sensors = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
    if sensors:
        print(f"\n📡 Binary Sensors ({len(sensors)}):")
        for sensor in sensors[:5]:  # First 5
            print(f"   • {sensor.name} ({sensor.entity_type})")
            print(f"     Device: {sensor.device_name}")

    # Show switches
    switches = mapper.get_entities_by_platform(Platform.SWITCH)
    if switches:
        print(f"\n🔘 Switches ({len(switches)}):")
        for switch in switches[:5]:
            print(f"   • {switch.name}")
            print(f"     Device: {switch.device_name}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
