#!/usr/bin/env python3
"""Analyze LXP file to show datapoint addresses."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def analyze_lxp(lxp_file):
    """Analyze LXP file and show all datapoint addresses."""
    tree = ET.parse(lxp_file)
    root = tree.getroot()

    # Namespace
    ns = {"lxp": "http://www.luxor.de/LuxorPlug"}

    print(f"\n🔍 Analyzing: {lxp_file}\n")
    print("=" * 80)

    # Find all devices
    devices = root.findall(".//lxp:Device", ns)

    for device in devices:
        device_name = device.get("Name", "Unknown")
        device_id = device.get("Id", "Unknown")

        print(f"\n📦 Device: {device_name} (ID: {device_id})")
        print("-" * 80)

        # Find all actuators
        actuators = device.findall(".//lxp:Actuator", ns)
        for actuator in actuators:
            act_name = actuator.get("Name", "Unknown")
            act_id = actuator.get("Id", "Unknown")
            act_type = actuator.get("ActuatorType", "Unknown")

            print(f"\n  💡 Actuator: {act_name} (ID: {act_id}, Type: {act_type})")

            # Find datapoints
            datapoints = actuator.findall(".//lxp:Datapoint", ns)
            if datapoints:
                print("     Datapoints:")
                for dp in datapoints:
                    role = dp.get("Role", "Unknown")
                    address = dp.get("Address", "Unknown")
                    print(f"       • {role}: {address}")
            else:
                print("     ⚠️  No datapoints found!")

        # Find all sensors
        sensors = device.findall(".//lxp:Sensor", ns)
        for sensor in sensors:
            sens_name = sensor.get("Name", "Unknown")
            sens_id = sensor.get("Id", "Unknown")
            sens_type = sensor.get("SensorType", "Unknown")

            print(f"\n  🔘 Sensor: {sens_name} (ID: {sens_id}, Type: {sens_type})")

            # Find datapoints
            datapoints = sensor.findall(".//lxp:Datapoint", ns)
            if datapoints:
                print("     Datapoints:")
                for dp in datapoints:
                    role = dp.get("Role", "Unknown")
                    address = dp.get("Address", "Unknown")
                    print(f"       • {role}: {address}")
            else:
                print("     ⚠️  No datapoints found!")

    print("\n" + "=" * 80)
    print("\n✅ Analysis complete!\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_lxp.py <path_to_lxp_file>")
        sys.exit(1)

    lxp_file = Path(sys.argv[1])

    if not lxp_file.exists():
        print(f"❌ File not found: {lxp_file}")
        sys.exit(1)

    analyze_lxp(lxp_file)
