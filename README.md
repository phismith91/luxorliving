# Support

If you find this project useful, consider buying me a coffee:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-Donate-FFDD00?style=flat-square&logo=buymeacoffee)](https://buymeacoffee.com/philsmith91)


# LUXORliving KNX Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/phismith91/luxorliving)](https://github.com/phismith91/luxorliving/releases)
[![License](https://img.shields.io/github/license/phismith91/luxorliving)](LICENSE)

## Support

If you find this project useful, consider buying me a coffee:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-Donate-FFDD00?style=flat-square&logo=buymeacoffee)](https://buymeacoffee.com/philsmith91)

## What is this Integration about

Integrate Theben LUXORliving (BAOS 777) KNX gateways with automatic entity discovery from LXP project files.

## Features

- **Automatic entity discovery** – Upload LXP file, entities are created automatically
- **KNX/IP native** – Tunneling and routing modes supported
- **Local polling updates** – State refresh via BAOS REST (configurable interval)
- **Config Flow UI** – Setup in <2 minutes via HA interface
- **HACS compatible** – One-click installation
- **🚀 Performance optimized** – Parallel entity creation, async operations
- **⚙️ Configurable discovery** – Adjustable auto-discovery timeout (0.5-10s)
- **📊 Performance monitoring** – Built-in benchmarking and regression detection
- **🛡️ Circuit breaker protection** – Resilient error handling with automatic recovery
- **💾 Smart caching** – LXP file caching with TTL and memory management
- **🏥 Health monitoring** – System health endpoint for diagnostics
- **⚡ Rate limiting** – Prevents "light shows" by blocking rapid on/off cycles (5+ in 1s)

**Working platforms:** Light, Switch, Cover, Climate, Binary Sensor, Sensor

## Current Release

## Current Release

<!-- RELEASE_NOTES_START -->


# 🎉 LUXORliving v0.6.0 (Final Release)



**Release Date:** 9. Januar 2026



### 🥈 Home Assistant Silver Compliance Features



This release implements features required for **Home Assistant Silver** quality scale compliance.



### ✨ Added



- **🔐 Re-Authentication Flow**

  - Repair flow is triggered after 3 consecutive authentication failures

  - User-friendly credential update UI and automatic reconnection

  - Integration reload without reconfiguration after successful re-auth



- **🌍 Multi-Language Support**

  - German (de), French (fr), English (en)

  - Localized config flow, repair messages and UI strings



- **📚 End-user Documentation**

  - Added examples: Automations, Dashboard configurations, Compatible devices list



### 🐛 Bug fixes



- Fixed test fixture issue in performance benchmark tests

- Fixed coordinator initialization for HA 2026.8+ (pass `config_entry` to DataUpdateCoordinator)



### 🔧 Technical Improvements



- `repairs.py` added for re-auth repair flows

- Coordinator now tracks authentication failures and creates repair issues

- Improved translations and `strings.json` coverage

- HACS package structure correction (files at zip root)



### 🧪 Testing & Quality



- **Tests:** 212/212 passing

- **Quality gates:** README/CHANGELOG validation, HACS install test, zip structure validation



### ⚡ Upgrade Notes



- Remove any previously installed beta copies and nested directories before installing

- Install v0.6.0 via HACS and restart Home Assistant



---



For full changelog see `CHANGELOG.md`.
<!-- RELEASE_NOTES_END -->

For full release history see [CHANGELOG.md](./CHANGELOG.md).


For full release history see [CHANGELOG.md](./CHANGELOG.md).



---



## Quick Start

### 1. Prerequisites

- Theben LUXORliving IP1 Gateway (BAOS 777)
- LXP project file (export from Theben LUXORPlug software)
- Home Assistant ≥ 2025.12.0

### 2. Installation

**HACS (recommended):**
1. Open HACS → Integrations → ⋮ (menu) → Custom repositories
2. Add `https://github.com/phismith91/luxorliving` as Integration
3. Click Download → Restart Home Assistant

**Manual:**
1. Copy `custom_components/luxor_living` to your HA config directory
2. Restart Home Assistant

### 3. Configuration

1. **Settings** → **Devices & Services** → **Add Integration** → **LUXORliving**
2. Upload LXP file (or enter path like `/config/luxor/project.lxp`)
3. Enter gateway IP (port 3671 is used automatically)
4. Select connection type: **Tunneling** (recommended) or Routing
5. Click Submit

Entities are created automatically based on your LXP project.

---

## Usage Examples

### Automation with Physical Switches

Physical KNX switches trigger HA automations instantly:

```yaml
automation:
  - alias: "Living room motion detected"
    trigger:
      - platform: state
        entity_id: binary_sensor.bewegungsmelder_wohnzimmer
        to: "on"
    action:
      - service: light.turn_on
        target:
          entity_id: light.deckenleuchte_wohnzimmer
```

### Lovelace Card

```yaml
type: entities
title: LUXORliving
entities:
  - entity: light.deckenleuchte_wohnzimmer
  - entity: switch.steckdose_kueche
  - entity: binary_sensor.bewegungsmelder_flur
```

---

## Troubleshooting

| Problem                    | Solution                                                               |
| -------------------------- | ---------------------------------------------------------------------- |
| Integration not loading    | Check logs: `tail -f /config/home-assistant.log \| grep luxor_living`  |
| LXP file not found         | Use absolute path (e.g., `/config/luxor/project.lxp`)                  |
| Gateway unreachable        | Verify IP address and port 3671, check firewall                        |
| Entities not created       | Check LXP file contains group addresses, restart HA                    |
| Tunneling connection fails | Try Routing mode or check BAOS authentication                          |
| Slow startup               | Check discovery timeout setting (Options → Configure)                  |
| Performance issues         | Run benchmark: `curl http://localhost:8123/api/luxor_living/benchmark` |
| Circuit breaker open       | Check network connectivity, circuit auto-recovers after timeout        |

**Enable debug logging:**
```yaml
logger:
  default: info
  logs:
    custom_components.luxor_living: debug
```

**Health check endpoint:**
```
GET http://your-ha-ip:8123/api/luxor_living/health
```

**Performance benchmarking:**
```bash
# Run full benchmark suite
curl -X POST http://your-ha-ip:8123/api/luxor_living/benchmark
```

---

## FAQ

**Q: Do I need ETS software?**  
A: No. Export LXP from Theben LUXORPlug software (included with gateway).

**Q: What's the difference between Tunneling and Routing?**  
A: Tunneling is recommended (authenticated, stable). Routing works without auth but may have firewall issues.

**Q: Can I test without hardware?**  
A: Yes. Enable "Simulation Mode" in integration options for dry-run testing.

**Q: Which group addresses are supported?**  
A: All DPT types in LXP file are parsed. Light (DPT 1.001, 5.001), Switch (DPT 1.001), Binary Sensors (DPT 1.x).

**Q: How long does initial state reading take?**  
A: ~30ms per entity via GroupValueRead. Example: 27 lights = ~800ms.

---

## Advanced Configuration

### Simulation Mode

Test without hardware by enabling in integration options:
**Settings** → **Devices & Services** → **LUXORliving** → **Options** → Enable **Simulation Mode**

### Multiple Gateways

Add multiple integrations for different gateways:
1. Add integration → Configure gateway 1
2. Add integration again → Configure gateway 2

Each gateway creates separate entities.

---

## Documentation

- [Documentation Index](docs/INDEX.md) – Complete documentation overview
- [Installation Guide](docs/INSTALLATION.md) – Detailed setup instructions
- [KNX Implementation](docs/KNX_IMPLEMENTATION.md) – Technical protocol details
- [Sensor Platform](docs/SENSOR_PLATFORM.md) – Sensor configuration and usage
- [Architecture Decisions](docs/ARCHITECTURE_DECISION.md) – Core design decisions
- [Release Operations](docs/RELEASE_OPERATIONS.md) – Release process and deployment

**For Developers:**
- [Security Policy](SECURITY.md) – Vulnerability reporting
- Test Suite: 209 tests – Run `pytest tests/ -v` for details

---

## License

This project is licensed under the [LICENSE](LICENSE).

---

<<<<<<< HEAD
=======


>>>>>>> 998ba72 (Docs: Document README mismatch incident and update README release block to v0.6.0)
## Credits

- [Theben AG](https://www.theben.de/) – LUXORliving system
- [xknx](https://github.com/XKNX/xknx) – KNX/IP communication library
- Home Assistant Community
