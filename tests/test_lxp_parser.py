#!/usr/bin/env python3
"""Test script for LXP parser."""
import sys
from pathlib import Path

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.luxor_living.lxp_parser import LXPParser


def main():
    """Test the LXP parser."""
    import sys

    # Check if file provided as argument
    if len(sys.argv) > 1:
        lxp_file = Path(sys.argv[1])
    else:
        lxp_file = Path(__file__).parent.parent / "data" / "test_project.lxp"

        if not lxp_file.exists():
            lxp_file = Path("/home/phil/Nextcloud/Familie Schmidt_0.9.lxp")

        if not lxp_file.exists():
            lxp_file = Path("/home/phil/Nextcloud/Familie Schmidt_0.8.lxp")

    if not lxp_file.exists():
        print(f"❌ LXP file not found: {lxp_file}")
        return

    print(f"📄 Parsing: {lxp_file.name}")
    print("=" * 60)

    parser = LXPParser(lxp_file)
    project = parser.parse()

    print(f"\n🏠 Project: {project.name}")
    print(f"🌐 Gateway: {project.gateway_address}:{project.gateway_port}")
    print(f"📦 Devices: {len(project.devices)}")
    print("\n" + "=" * 60)

    for device in project.devices:
        print(f"\n📟 Device: {device.name} ({device.serial_number})")
        print(f"   Address: {device.address}")

        if device.actuators:
            print(f"   🔌 Actuators: {len(device.actuators)}")
            for act in device.actuators:
                print(f"      • {act.name} (Ch {act.channel})")
                for dp in act.datapoints:
                    print(f"         - {dp.role}: {dp.address}")

        if device.sensors:
            print(f"   📡 Sensors: {len(device.sensors)}")
            for sens in device.sensors:
                print(f"      • {sens.name} (Ch {sens.channel})")
                for dp in sens.datapoints:
                    print(f"         - {dp.role}: {dp.address}")

    print("\n" + "=" * 60)
    print(f"✅ Successfully parsed {len(project.devices)} devices!")

    # Statistics
    total_actuators = sum(len(d.actuators) for d in project.devices)
    total_sensors = sum(len(d.sensors) for d in project.devices)
    total_datapoints = sum(len(a.datapoints) for d in project.devices for a in d.actuators) + sum(
        len(s.datapoints) for d in project.devices for s in d.sensors
    )

    print(f"\n📊 Statistics:")
    print(f"   Actuators: {total_actuators}")
    print(f"   Sensors: {total_sensors}")
    print(f"   Datapoints: {total_datapoints}")


if __name__ == "__main__":
    main()
