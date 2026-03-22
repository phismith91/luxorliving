# LUXORliving KNX Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![CI](https://github.com/phismith91/luxorliving/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/phismith91/luxorliving/actions/workflows/ci-cd.yml)
[![Codecov](https://codecov.io/gh/phismith91/luxorliving/branch/main/graph/badge.svg)](https://codecov.io/gh/phismith91/luxorliving)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/phismith91/luxorliving?include_prereleases)](https://github.com/phismith91/luxorliving/releases)
[![License](https://img.shields.io/github/license/phismith91/luxorliving.svg)](https://github.com/phismith91/luxorliving/blob/main/LICENSE)
[![Tests: 296](https://img.shields.io/badge/Tests-296%20passing-brightgreen.svg)](https://github.com/phismith91/luxorliving/blob/main/docs/TESTS.md)

Home Assistant custom integration for **Theben LUXORliving KNX** systems. Connects via the BAOS 777 IP1 gateway using a LXP project file for automatic entity discovery — lights, covers, climate, sensors, switches and binary sensors, all created without any manual YAML.

---

## Quick Start

**Requirements:** Theben LUXORliving IP1 gateway · LXP project file · Home Assistant ≥ 2025.12.0

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
| 🏠 **User** — just want it working | [User Guide](docs/USER_GUIDE.md) |
| ⚙️ **Advanced User** — want to tune and extend | [Advanced Guide](docs/ADVANCED_GUIDE.md) |
| 🛠️ **Contributor** — want to develop or contribute | [Developer Guide](docs/DEVELOPER_GUIDE.md) |

**Reference:**
[Full Options & Features Reference](docs/REFERENCE.md) · [Compatible Devices](#) · [Automations](docs/AUTOMATIONS.md) · [Dashboard Examples](docs/DASHBOARD_EXAMPLES.md)

**Technical:**
[Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md) · [Architecture Decisions](docs/ARCHITECTURE_DECISION.md) · [Sensor Platform](docs/SENSOR_PLATFORM.md) · [Tests](docs/TESTS.md)

**Operations:**
[Release Operations](docs/RELEASE_OPERATIONS.md) · [Incident Response](docs/INCIDENT_RESPONSE_RUNBOOK.md) · [Changelog](CHANGELOG.md)

---

## Support

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-Donate-FFDD00?style=flat-square&logo=buymeacoffee)](https://buymeacoffee.com/philsmith91)

Found a bug? [Open an issue](https://github.com/phismith91/luxorliving/issues) · Security issue? See [SECURITY.md](SECURITY.md)

---

## License

[MIT](https://github.com/phismith91/luxorliving/blob/main/LICENSE) · Built with [xknx](https://github.com/XKNX/xknx) · Made for [Theben LUXORliving](https://www.theben.de/)
