#!/usr/bin/env python3
"""Script to switch LUXORliving integration to KNX Tunneling mode."""

import json
import sys
from pathlib import Path


def set_tunneling(gateway_ip: str):
    """Change connection type to tunneling and set gateway IP."""
    storage_file = Path.home() / ".homeassistant/.storage/core.config_entries"

    if not storage_file.exists():
        print(f"❌ Config file not found: {storage_file}")
        return False

    with open(storage_file) as f:
        data = json.load(f)

    changed = False
    for entry in data["data"]["entries"]:
        if entry["domain"] == "luxor_living":
            old_type = entry["data"].get("connection_type", "unknown")
            old_host = entry["data"].get("host", "unknown")

            # Update to tunneling
            entry["data"]["connection_type"] = "tunneling"
            entry["data"]["host"] = gateway_ip
            entry["data"]["port"] = 3671  # Standard KNX/IP port

            changed = True

            print("✅ LUXORliving Konfiguration aktualisiert:")
            print(f"   Connection Type: {old_type} → tunneling")
            print(f"   Host: {old_host} → {gateway_ip}")
            print("   Port: 3671")
            break

    if not changed:
        print("❌ Keine LUXORliving Config Entry gefunden!")
        return False

    # Save changes
    with open(storage_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n💾 Änderungen gespeichert in: {storage_file}")
    print("\n⚠️  WICHTIG: Home Assistant neu starten!")
    print("    pkill -f 'hass -c' && sleep 2 && ./scripts/start_homeassistant.sh")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 set_tunneling.py <GATEWAY_IP>")
        print("\nBeispiel:")
        print("  python3 set_tunneling.py 192.168.1.3")
        print("\nDeine aktuelle Konfiguration:")

        storage_file = Path.home() / ".homeassistant/.storage/core.config_entries"
        with open(storage_file) as f:
            data = json.load(f)

        for entry in data["data"]["entries"]:
            if entry["domain"] == "luxor_living":
                print(f"  Connection Type: {entry['data'].get('connection_type')}")
                print(f"  Host: {entry['data'].get('host')}")
                print(f"  Port: {entry['data'].get('port')}")

        sys.exit(1)

    gateway_ip = sys.argv[1]

    # Validate IP format (basic check)
    parts = gateway_ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        print(f"❌ Ungültige IP-Adresse: {gateway_ip}")
        sys.exit(1)

    success = set_tunneling(gateway_ip)
    sys.exit(0 if success else 1)
