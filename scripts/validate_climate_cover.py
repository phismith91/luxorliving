#!/usr/bin/env python3
"""Validate Climate and Cover entity creation from Hauptwohnung.lxp."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.luxor_living.lxp_parser import LXPCache


async def main():
    """Validate climate and cover entities from Hauptwohnung.lxp."""
    lxp_file = Path(__file__).parent.parent / "docs" / "Hauptwohnung.lxp"

    if not lxp_file.exists():
        print(f"❌ LXP file not found: {lxp_file}")
        return 1

    print("=" * 80)
    print("Climate & Cover Platform Validation")
    print("=" * 80)
    print(f"LXP File: {lxp_file}")
    print()

    # Parse LXP
    cache = LXPCache()
    project = await cache.get_or_parse(lxp_file)

    # Find heating devices (H6)
    heating_devices = [d for d in project.devices if d.app_id == "18502"]
    climate_entities = []

    print("🔥 CLIMATE ENTITIES (H6 Heating Actuators)")
    print("-" * 80)

    for device in heating_devices:
        for actuator in device.actuators:
            dp_roles = {dp.role for dp in actuator.datapoints}

            if "Istwert" in dp_roles and "Sollwert" in dp_roles:
                climate_entities.append(
                    {
                        "device": device.name,
                        "actuator": actuator.name,
                        "channel": actuator.channel,
                        "datapoints": list(dp_roles),
                    }
                )

                print(f"✅ {device.name} - {actuator.name}")
                print(f"   Channel: {actuator.channel}")
                print(f"   Datapoints: {', '.join(sorted(dp_roles))}")
                print()

    # Find cover devices (J8/J4)
    cover_devices = [d for d in project.devices if d.app_id in ["18520", "18516"]]
    cover_entities = []

    print("🪟 COVER ENTITIES (J8/J4 Shutter/Blind Actuators)")
    print("-" * 80)

    for device in cover_devices:
        for actuator in device.actuators:
            dp_roles = {dp.role for dp in actuator.datapoints}

            if "UpDown" in dp_roles or "StepStop" in dp_roles:
                has_tilt = "Lamelle%" in dp_roles or "StatusLamelle%" in dp_roles
                device_type = "Blind (with tilt)" if has_tilt else "Shutter"

                cover_entities.append(
                    {
                        "device": device.name,
                        "actuator": actuator.name,
                        "channel": actuator.channel,
                        "type": device_type,
                        "datapoints": list(dp_roles),
                    }
                )

                print(f"✅ {device.name} - {actuator.name}")
                print(f"   Channel: {actuator.channel}")
                print(f"   Type: {device_type}")
                print(f"   Datapoints: {', '.join(sorted(dp_roles))}")
                print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Climate Entities: {len(climate_entities)}")
    print(f"  - Heating Zones: {len(climate_entities)}")
    print()
    print(f"Cover Entities: {len(cover_entities)}")
    shutters = [c for c in cover_entities if c["type"] == "Shutter"]
    blinds = [c for c in cover_entities if "Blind" in c["type"]]
    print(f"  - Shutters: {len(shutters)}")
    print(f"  - Blinds: {len(blinds)}")
    print()

    # Validation checks
    issues = []

    # Check for climate entities without required datapoints
    for entity in climate_entities:
        required = {"Istwert", "Sollwert"}
        missing = required - set(entity["datapoints"])
        if missing:
            issues.append(f"Climate entity '{entity['actuator']}' missing: {', '.join(missing)}")

    # Check for cover entities without required datapoints
    for entity in cover_entities:
        required = {"UpDown", "StepStop"}
        has_required = any(dp in entity["datapoints"] for dp in required)
        if not has_required:
            issues.append(f"Cover entity '{entity['actuator']}' missing UpDown or StepStop")

    if issues:
        print("⚠️  VALIDATION ISSUES")
        print("-" * 80)
        for issue in issues:
            print(f"  ❌ {issue}")
        print()
        return 1

    print("✅ All entities valid!")
    print()
    print("Expected Home Assistant Entities:")
    print(f"  - {len(climate_entities)} Climate entities (thermostats)")
    print(f"  - {len(cover_entities)} Cover entities (shutters/blinds)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
