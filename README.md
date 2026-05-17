# LUXORliving KNX Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![CI](https://github.com/phismith91/luxorliving/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/phismith91/luxorliving/actions/workflows/ci-cd.yml)
[![Codecov](https://codecov.io/gh/phismith91/luxorliving/branch/main/graph/badge.svg)](https://codecov.io/gh/phismith91/luxorliving)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/phismith91/luxorliving?include_prereleases)](https://github.com/phismith91/luxorliving/releases)
[![License](https://img.shields.io/github/license/phismith91/luxorliving.svg)](https://github.com/phismith91/luxorliving/blob/main/LICENSE)
[![Tests: 765](https://img.shields.io/badge/Tests-765%20passing-brightgreen.svg)](https://github.com/phismith91/luxorliving/blob/main/docs/TESTS.md)

Home Assistant custom integration for **Theben LUXORliving KNX** systems. Connects via the BAOS 777 IP1 gateway using a LXP project file for automatic entity discovery — lights, covers, climate, sensors, switches and binary sensors, all created without any manual YAML.

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
**Current release:** [v1.1.7](https://github.com/phismith91/luxorliving/releases/tag/v1.1.7) — RTR 718 thermostat support · B6 binary input fix · Rain sensor live state
<!-- RELEASE_NOTES_END -->

---

## Compatible Devices

Tested and confirmed working:

| Device | Function | HA platform |
| --- | --- | --- |
| S 4 / S 8 / S 16 | Switching actuator | `switch` / `light` |
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

## Support

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-Donate-FFDD00?style=flat-square&logo=buymeacoffee)](https://buymeacoffee.com/philsmith91)

Found a bug? [Open an issue](https://github.com/phismith91/luxorliving/issues) · Security issue? See [SECURITY.md](https://github.com/phismith91/luxorliving/blob/main/SECURITY.md)

---

## License

[MIT](https://github.com/phismith91/luxorliving/blob/main/LICENSE) · Built with [xknx](https://github.com/XKNX/xknx) · Made for [Theben LUXORliving](https://www.theben.de/)
