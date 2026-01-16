#!/usr/bin/env python3
"""Audit script for Hauptwohnung.lxp file against our LXP parser."""

import asyncio
import os
import sys
from pathlib import Path

# Add the custom_components directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "luxor_living"))

from lxp_parser import LXPCache


async def audit_lxp_file():
    """Audit the Hauptwohnung.lxp file."""
    print("🔍 LXP Parser Audit für Hauptwohnung.lxp")
    print("=" * 50)

    # Path to the LXP file
    lxp_path = Path(__file__).parent / "docs" / "Hauptwohnung.lxp"

    if not lxp_path.exists():
        print(f"❌ LXP-Datei nicht gefunden: {lxp_path}")
        return

    print(f"📁 Analysiere Datei: {lxp_path}")
    print(f"📊 Dateigröße: {lxp_path.stat().st_size} Bytes")

    try:
        # Create parser instance
        cache = LXPCache()

        # Parse the project
        print("\n🔄 Parsing LXP-Datei...")
        project = await cache.get_or_parse(lxp_path, include_unaffected=True)

        print("✅ Parsing erfolgreich!")
        print(f"🏠 Projektname: {project.name}")
        print(f"🌐 Gateway: {project.gateway_address}:{project.gateway_port}")
        print(f"📱 Anzahl Geräte: {len(project.devices)}")

        # Analyze devices
        device_types = {}
        total_sensors = 0
        total_actuators = 0
        total_datapoints = 0

        print("\n📋 Geräte-Analyse:")
        print("-" * 30)

        for device in project.devices:
            # Categorize device by app_id
            app_id = device.app_id
            if app_id not in device_types:
                device_types[app_id] = []
            device_types[app_id].append(device)

            sensors_count = len(device.sensors)
            actuators_count = len(device.actuators)
            datapoints_count = sum(len(s.datapoints) for s in device.sensors) + sum(
                len(a.datapoints) for a in device.actuators
            )

            print(f"• {device.name}")
            print(f"  Seriennummer: {device.serial_number}")
            print(f"  App ID: {app_id}, Adresse: {device.address}")
            print(f"  Sensoren: {sensors_count}, Aktuatoren: {actuators_count}")
            print(f"  Datenpunkte: {datapoints_count}")

            total_sensors += sensors_count
            total_actuators += actuators_count
            total_datapoints += datapoints_count

        print("\n📊 Zusammenfassung:")
        print(f"• Geräte gesamt: {len(project.devices)}")
        print(f"• Sensoren gesamt: {total_sensors}")
        print(f"• Aktuatoren gesamt: {total_actuators}")
        print(f"• Datenpunkte gesamt: {total_datapoints}")

        print("\n🔢 Gerätetypen nach App ID:")
        for app_id, devices in device_types.items():
            print(f"• App ID {app_id}: {len(devices)} Geräte")

        # Check for common issues
        print("\n⚠️  Qualitätsprüfungen:")
        issues = []

        # Check for devices without datapoints
        devices_without_datapoints = [
            d for d in project.devices if not d.sensors and not d.actuators
        ]
        if devices_without_datapoints:
            issues.append(f"Geräte ohne Datenpunkte: {len(devices_without_datapoints)}")
            print(f"⚠️  Geräte ohne Datenpunkte gefunden ({len(devices_without_datapoints)}):")
            for d in devices_without_datapoints:
                print(f"  - {d.name} (Adresse: {d.address}, App ID: {d.app_id})")

        # Check for sensors/actuators without datapoints
        sensors_without_datapoints = sum(
            1 for d in project.devices for s in d.sensors if not s.datapoints
        )
        if sensors_without_datapoints:
            issues.append(f"Sensoren ohne Datenpunkte: {sensors_without_datapoints}")

        actuators_without_datapoints = sum(
            1 for d in project.devices for a in d.actuators if not a.datapoints
        )
        if actuators_without_datapoints:
            issues.append(f"Aktuatoren ohne Datenpunkte: {actuators_without_datapoints}")

        # Check for duplicate addresses
        addresses = [d.address for d in project.devices]
        duplicates = set([x for x in addresses if addresses.count(x) > 1])
        if duplicates:
            issues.append(f"Duplizierte Adressen: {duplicates}")

        if not issues:
            print("✅ Keine Probleme gefunden!")
        else:
            print("⚠️  Gefundene Probleme:")
            for issue in issues:
                print(f"  - {issue}")

        # Performance test
        print("\n⏱️  Performance-Test:")
        import time

        start_time = time.time()
        for _ in range(5):  # Parse 5 times
            await cache.get_or_parse(lxp_path, include_unaffected=True)
        end_time = time.time()
        avg_time = (end_time - start_time) / 5
        print(f"Durchschnittliche Parse-Zeit: {avg_time:.3f}s")

        # Compare with existing test data
        print("\n🧪 Vergleich mit Testdaten:")
        test_lxp_path = Path(__file__).parent / "tests" / "test_data" / "sample_project.lxp"
        if test_lxp_path.exists():
            test_parser = LXPCache(test_lxp_path, include_unaffected=True)
            test_project = await test_parser.parse()

            print(f"• Test-Projekt: {test_project.name}")
            print(f"  Geräte: {len(test_project.devices)}")
            print(f"  Sensoren: {sum(len(d.sensors) for d in test_project.devices)}")
            print(f"  Aktuatoren: {sum(len(d.actuators) for d in test_project.devices)}")

            print(f"• Hauptwohnung-Projekt: {project.name}")
            print(f"  Geräte: {len(project.devices)}")
            print(f"  Sensoren: {total_sensors}")
            print(f"  Aktuatoren: {total_actuators}")

            if len(project.devices) > len(test_project.devices):
                print("📈 Hauptwohnung hat mehr Geräte als Testdaten")
            else:
                print("📉 Hauptwohnung hat weniger Geräte als Testdaten")
        else:
            print("⚠️  Test-LXP-Datei nicht gefunden")

        print("\n✅ Audit abgeschlossen!")
        return True

    except Exception as e:
        print(f"❌ Fehler beim Parsing: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(audit_lxp_file())
    sys.exit(0 if success else 1)
