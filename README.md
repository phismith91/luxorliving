# LUXORliving KNX Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![CI](https://github.com/phismith91/luxorliving/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/phismith91/luxorliving/actions/workflows/ci-cd.yml)
[![Codecov](https://codecov.io/gh/phismith91/luxorliving/branch/main/graph/badge.svg)](https://codecov.io/gh/phismith91/luxorliving)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/phismith91/luxorliving?include_prereleases)](https://github.com/phismith91/luxorliving/releases)
[![License](https://img.shields.io/github/license/phismith91/luxorliving.svg)](https://github.com/phismith91/luxorliving/blob/main/LICENSE)
[![Tests: 1037](https://img.shields.io/badge/Tests-1037%20passing-brightgreen.svg)](https://github.com/phismith91/luxorliving/blob/main/docs/TESTS.md)

Home Assistant custom integration for **Theben LUXORliving KNX** systems. Connects via the BAOS 777 IP1 gateway using a LXP project file for automatic entity discovery — lights, covers, climate, sensors and binary sensors, all created without any manual YAML.

---

## Quick Start

**Requirements:** Theben LUXORliving IP1 gateway · LXP project file · Home Assistant ≥ 2026.4.4

**1. Install via HACS**

Open HACS → Integrations → ⋮ → Custom repositories → add `https://github.com/phismith91/luxorliving` → Download → Restart HA.

**2. Add the Integration**

Settings → Devices & Services → Add Integration → **LUXORliving** → follow the config flow.

**3. Done**

Entities are discovered and created automatically from your LXP project file.

---

## Documentation

| Who are you? | Start here |
| --- | --- |
| 🏠 **User** — just want it working | [User Guide](https://github.com/phismith91/luxorliving/blob/main/docs/USER_GUIDE.md) |
| ⚙️ **Advanced User** — want to tune and extend | [Advanced Guide](https://github.com/phismith91/luxorliving/blob/main/docs/ADVANCED_GUIDE.md) |
| 🛠️ **Contributor** — want to develop or contribute | [Developer Guide](https://github.com/phismith91/luxorliving/blob/main/docs/DEVELOPER_GUIDE.md) |

**Reference:**
[Full Options & Features Reference](https://github.com/phismith91/luxorliving/blob/main/docs/REFERENCE.md) · [Automations](https://github.com/phismith91/luxorliving/blob/main/docs/AUTOMATIONS.md) · [Dashboard Examples](https://github.com/phismith91/luxorliving/blob/main/docs/DASHBOARD_EXAMPLES.md)

**Technical:**
[Architecture Overview](https://github.com/phismith91/luxorliving/blob/main/docs/ARCHITECTURE_OVERVIEW.md) · [Architecture Decisions](https://github.com/phismith91/luxorliving/blob/main/docs/ARCHITECTURE_DECISION.md) · [Sensor Platform](https://github.com/phismith91/luxorliving/blob/main/docs/SENSOR_PLATFORM.md) · [Tests](https://github.com/phismith91/luxorliving/blob/main/docs/TESTS.md)

**Operations:**
[Release Operations](https://github.com/phismith91/luxorliving/blob/main/docs/RELEASE_OPERATIONS.md) · [Incident Response](https://github.com/phismith91/luxorliving/blob/main/docs/INCIDENT_RESPONSE_RUNBOOK.md) · [Changelog](https://github.com/phismith91/luxorliving/blob/main/CHANGELOG.md)

<!-- RELEASE_NOTES_START -->
**Current release:** [v1.2.2-rc.1](https://github.com/phismith91/luxorliving/releases/tag/v1.2.2-rc.1) — pre-release: fixes cover tilt position being inverted (#197) — closed blinds reported tilt 100 instead of 0, and open/close-tilt commands sent the opposite KNX value from what they meant. Builds on the stable [v1.2.1](https://github.com/phismith91/luxorliving/releases/tag/v1.2.1) release.
<!-- RELEASE_NOTES_END -->

---

## Compatible Devices

Tested and confirmed working:

| Device | Function | HA platform |
| --- | --- | --- |
| S 4 / S 8 / S 16 | Switching actuator | `light` |
| D 2 / D 4 | Dimming actuator | `light` (with brightness) |
| J 4 / J 8 | Blind / shutter actuator | `cover` (position + tilt) |
| H 6 | Heating actuator | `climate` (setpoint + valve) |
| RTR 718 | Standalone room thermostat | `climate` (setpoint + current temp) |
| B 6 | Binary input module (6-channel) | `binary_sensor` |
| KNX weather station | Multi-sensor | `sensor` (temperature, wind, brightness) + `binary_sensor` (rain) |
| Motion detectors | Binary input | `binary_sensor` |
| Window / door contacts | Binary input | `binary_sensor` |

Not yet tested / known limitations:

| Device / feature | Status |
| --- | --- |
| Multi-gang switches with mixed functions | Not tested |
| Scene actuators | Not supported — no LXP role mapping |
| KNX-RF (wireless) devices | Not tested |
| Energy metering actuators | Not tested |

If your device works or doesn't work, please [open an issue](https://github.com/phismith91/luxorliving/issues) so we can update this list.

---

## Configuration Parameters

The integration is configured entirely via the UI config flow. Key parameters:

| Parameter | Where | Description |
| --- | --- | --- |
| **LXP project file** | Setup | The `.lxp` file exported from LUXORplug. Upload via file picker. |
| **Gateway host** | Setup | IP address of the BAOS 777 IP1 gateway (e.g. `192.168.1.3`). |
| **Port** | Setup | KNX/IP port — default `3671`. |
| **Username / Password** | Setup | BAOS 777 REST API credentials — factory default is `admin` / `admin`. |
| **Connection type** | Setup | `Tunneling` (point-to-point, recommended) or `Routing` (multicast). |
| **Push token** | Options | Optional token for the `/api/luxor_living/push` webhook endpoint. |
| **Push auth method** | Options | `none` · `token` (X-LUXOR-PUSH-TOKEN header) · `bearer` · `hmac` (SHA-256). |

The gateway password is stored in HA's encrypted config-entry storage — it is never logged in plain text.

---

## Known Limitations

| Limitation | Notes |
| --- | --- |
| **SSL certificate** | The BAOS 777 uses a factory self-signed certificate. Certificate verification is intentionally disabled; a custom CA is not supported by the hardware. |
| **Scene actuators** | No LXP role mapping exists for scenes — entities are not created. |
| **Multi-gang switches with mixed functions** | Not tested; entity detection relies on datapoint heuristics which may misidentify channels. |
| **KNX-RF wireless devices** | Parsed, but RF-only devices without wired group addresses may not produce entities. |
| **Energy metering actuators** | Not tested. |
| **LXP reload without HA restart** | Use the *Reload integration* service action. Changing the LXP file requires a reconfigure flow (no entities are removed from the registry automatically). |
| **No zeroconf auto-discovery** | Gateway must be configured manually; IP address is not auto-discovered at setup time. |

---

## Removing the Integration

1. Go to **Settings → Devices & Services → LUXORliving** → ⋮ → **Delete**.
2. HA removes all entities and the config entry automatically.
3. To fully clean up, restart HA after deletion so lingering KNX group address listeners are released.

If installed via HACS: open HACS → Integrations → LUXORliving → **Remove** after deleting the config entry.

---

## Support

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-Donate-FFDD00?style=flat-square&logo=buymeacoffee)](https://buymeacoffee.com/philsmith91)

Found a bug? [Open an issue](https://github.com/phismith91/luxorliving/issues) · Security issue? See [SECURITY.md](https://github.com/phismith91/luxorliving/blob/main/SECURITY.md)

---

## License

[MIT](https://github.com/phismith91/luxorliving/blob/main/LICENSE) · Built with [xknx](https://github.com/XKNX/xknx) · Made for [Theben LUXORliving](https://www.theben.de/)
