# Changelog

All notable changes to the LUXORliving Home Assistant integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- DataUpdateCoordinator pattern for centralized state management
- LuxorLivingEntity base class for common entity functionality
- Device registry integration for all platforms
- Type hints on all functions and parameters
- Code formatting with Black and isort
- Comprehensive test coverage (55% baseline established)
- py.typed marker for type checking support

### Changed
- Light platform refactored to use DataUpdateCoordinator
- Switch platform refactored to use DataUpdateCoordinator
- Binary Sensor platform refactored with auto-detection of device classes
- All platforms now extend LuxorLivingEntity base class
- Improved docstrings on all methods
- Import organization with isort

### Fixed
- Device registry integration missing in entities
- Inconsistent entity implementations across platforms
- Missing type hints causing IDE issues

## [0.2.12] - 2025-12-23

### Highlights

- **Log Enrichment**: GroupAddress→Entity and IndividualAddress→Device labels in log output for improved traceability
- **Dimmable Light Brightness**: Status% (2/3/0) read initially and monitored continuously
- **Event Loop Safety**: Robust callback scheduling with test-time fallback for HA-loop absence

### Added

- `knx_gateway.py`:
  - `set_group_address_labels()` - Sets GA→Entity label map for log enrichment
  - `set_individual_address_labels()` - Sets IA→Device label map for log enrichment
  - GA and IA labels in log output (📥 Received KNX telegram with Source IA Name and Destination GA Entity Name)
  - Fallback to direct callback invocation when HA Event Loop unavailable (test safety)

- `entity_mapper.py`:
  - `get_group_address_label_map()` - Creates GA→["Entity Name (ID)"] map
  - `get_individual_address_label_map()` - Creates IA→["Device Name (DeviceID)"] map

- `light.py`:
  - `LuxorLivingDimmableLight._address_dim_status` - Additional Status% address (2/3/0) listener
  - Initial read on Status% address for brightness initialization
  - `knx_address_dim_status` as extra attribute for dimmable lights

- Test Updates:
  - Dual listener tests for Light and Switch
  - KNX initial read tests (no REST-based initialization anymore)
  - Gateway callback scheduling tests with HA-loop fallback

### Changed

- Log output now contains human-readable names instead of only GroupAddress/IndividualAddress numbers
- Dimmable lights now listen to 2 addresses: `Dimmen%` (2/2/0) and `Status%` (2/3/0)
- Tests: Expectations adjusted for dual-listener architecture and KNX-only initial reads

### Fixed

- Brightness updates on dimmable lights now support both Dimmen% and Status% addresses
- HA Event Loop absence no longer causes callback scheduling failures (test compatibility)
- Log tracing now bidirectionally visible (who sends to whom)

### Removed

- REST-based initial reads (fully migrated to KNX reads)

### Quality

- ✅ **58/58 Tests Passing** (100%)
- ✅ **Code Quality Score:** 8.5/10
- ⚠️ **TLSv1 Deprecation Warnings** in rest_client.py (Minor)

### Technical Details

**Brightness Handling for Dimmable Lights:**
- Initial read sends telegrams to both addresses
- Listener registered on Dimmen% (2/2/0) and Status% (2/3/0)
- `_handle_brightness_update()` combines updates from both sources
- Percent-to-brightness conversion: `brightness = int((percent / 100) * 255)`

**Log Enrichment:**
- Gateway receives GA→Entity map on setup (`set_group_address_labels()`)
- Gateway receives IA→Device map on setup (`set_individual_address_labels()`)
- On telegram reception, labels are looked up from map and displayed
- Format: "📥 Received KNX telegram: Source IA: 9.0.12 (Device "Name"), Destination GA: 5/0/1 (Entity "light.badlicht")"

---

## [0.2.11] - 2025-12-20

### Added

- Dual KNX Listener Architecture for Light and Switch Entities
- Listeners on STATUS and CONTROL Group Addresses
- Initial reads on KNX addresses for state initialization
- `rest_client.py` for BAOS REST authentication and tunneling management
- Integration of XKNX v3.11.0 for KNX/IP communication

### Features

- ✅ Light platform with on/off and dimming
- ✅ Switch platform with on/off control
- ✅ Binary Sensor platform for motion detectors and contacts
- ✅ LXP parser for Theben LUXORliving projects
- ✅ Entity mapper for automatic entity creation from LXP

### Testing

- 46 tests for core functionality
- Simulation mode for tests without hardware
- Config flow tests

---

## [0.2.10] and earlier

See git history for details on older versions.

---

## Roadmap

### Q1 2026

- 📅 **Cover Platform** (blinds, roller shutters)
- 📅 **Climate Platform** (thermostats)
- 📅 **Sensor Platform** improvements

### Q2 2026

- 🔮 Multi-device support (multiple gateways)
- 🔮 Automation templates
- 🔮 Dashboard widgets

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards-compatible)
- **PATCH**: Bugfixes and improvements

---

For more information see [QUICKSTART.md](docs/QUICKSTART.md) and [docs/](docs/).
