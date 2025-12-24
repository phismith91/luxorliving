# Changelog

All notable changes to the LUXORliving Home Assistant integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-12-24

This is the first stable release of the LUXORliving Home Assistant integration. All critical issues from beta testing have been resolved.

### 🎉 Major Features
- **Full KNX Integration**: Seamless integration with KNX-based home automation systems
- **LXP Project Support**: Automatic entity generation from LUXORliving .lxp project files
- **Multi-Device Support**: Proper handling of multiple devices (S16, B6, iON4, etc.)
- **Real-time Updates**: Event-driven state updates via KNX telegrams
- **Multiple Platforms**: Light, Switch, and Binary Sensor entities

### ✨ Fixed (from beta.3)
- **Entity Mapper Unique ID Generation**: Use KNX addresses instead of actuator/sensor IDs
  - Multiple actuators/sensors with same name but different addresses now get unique IDs
  - Use control address (OnOff, SchaltenOnOff, Dimmen%, UpDown) for actuators
  - Resolves "Platform luxor_living does not generate unique IDs" errors

- **Per-Device Entity Grouping**: Entities properly organized by their source device
  - S16, B6, iON4 devices appear as separate devices in Home Assistant
  - Each device has its own entity list in the UI
  - Proper device identification for automation and scenes

- **Entity Type Handling**: Fixed MappedEntity attribute access
  - Proper dataclass usage throughout the codebase
  - Fixed 'MappedEntity' object has no attribute 'get' errors

- **Coordinator Architecture**: Event-driven passive state model
  - Removed invalid XKNX device polling logic
  - State updates from KNX telegram listeners (push-based)
  - Proper alignment with KNX event-driven architecture

- **Platform Defensive Checks**: Robust error handling
  - Light, Switch, and Binary Sensor platforms validate integration data
  - Graceful degradation with meaningful error messages

### 📊 Testing & Quality
- **All 74 tests passing** with zero regressions
- HACS compliant: unique IDs, device info, proper structure
- Home Assistant Core compliant: Coordinator pattern, entity standards
- Production ready: Tested with real LUXORliving hardware

### 🔧 Technical Details
- **Minimum Home Assistant**: 2025.12.0
- **Python Version**: 3.11+
- **Dependencies**: xknx≥3.11.0, defusedxml≥0.7.1, aiohttp≥3.9.0

### ⚠️ Breaking Changes from v0.2.x
- Entity unique_ids have changed (no longer backwards compatible)
- Entities will re-register in Home Assistant with new unique_ids
- Automations/scripts may need updating if they reference old entity IDs
- Previous beta versions (0.3.0-beta.*) will have their entities migrated

### 🚀 Upgrade Instructions
1. Backup your Home Assistant configuration
2. Update to v0.3.0 through HACS
3. Re-import the .lxp file (or restart integration)
4. Entities will re-register with proper unique IDs
5. Update any automations/scripts that reference entity IDs

---

## [0.3.0-beta.3] - 2025-12-23

### Fixed
- **Entity Mapper Unique ID Generation**: Use KNX addresses instead of actuator/sensor IDs
  - Multiple actuators/sensors with same name but different addresses now get unique IDs
  - Use control address (OnOff, SchaltenOnOff, Dimmen%, UpDown) for actuators
  - Use first datapoint address for sensors
  - **Critical Fix**: Resolves "Platform luxor_living does not generate unique IDs" errors
  - Example: Two "Reserve Deckenlampe" at addresses 2074 and 2075 now generate different IDs

- **Per-Device Entity Grouping**: Entities properly organized by source device
  - Each LXP device (S16-1, S16-2, B6-1, etc.) gets separate Home Assistant device
  - Fixes: Only "Luxor Living Gateway" was shown before

- **Entity Base Class Type Handling**: Fixed MappedEntity attribute access
  - Changed mapped_entity parameter from dict to MappedEntity dataclass
  - Updated name property to use getattr() for attributes
  - Fixed 'MappedEntity' object has no attribute 'get' errors in all platforms

- **Entity Unique ID Usage**: Use MappedEntity's address-based unique_id directly
  - Platform implementations now use unique_id from MappedEntity
  - Guarantees unique entity registration in Home Assistant
  - Prevents "already exists" errors when registering multiple entities

- **Coordinator Architecture Simplified**: Changed from broken polling model to event-driven passive state model
  - Removed invalid XKNX device polling logic (`.devices.items()` and `resolve_state()` calls)
  - Coordinator now acts as passive cache holder instead of active poller
  - State updates come from KNX telegram listeners (push-based)
  - Properly aligns with KNX event-driven architecture
  - Code simplified: -16 lines (20 removed, 4 added)

- **Platform Defensive Checks**: Added robust error handling for integration data access
  - Light, Switch, and Binary Sensor platforms now validate integration data
  - Type checking with `isinstance(integration_data, dict)`
  - Try/except blocks around data access
  - Graceful degradation with meaningful error messages

### Testing
- All 74 tests passing with zero regressions
- Entity unique IDs properly derived from KNX addresses (guaranteed unique)
- Multiple actuators/sensors with same name now work correctly
- Entities properly grouped by their source device
- Entity base class properly handles MappedEntity objects
- Coordinator architecture corrected to match actual KNX event-driven model
- All platforms properly handle missing or invalid integration data

---

## [0.3.0-beta.2] - 2025-12-23

### Fixed
- **Coordinator Data Update**: Fixed 'Devices' object iteration error
  - XKNX devices collection is not dict-like, requires direct iteration
  - Properly extracts `group_address_state` from each device
  - Added fallback to `group_address` if state address unavailable
  - Improved error logging with device names instead of addresses

### Testing
- All 74 tests passing after fix
- No regressions introduced
- Coordinator properly handles XKNX Devices collection

---

## [0.3.0] - 2025-12-23

### Highlights

**Production-Ready HACS Release** with complete DataUpdateCoordinator pattern, device registry integration, and comprehensive type hints.

### Added
- **DataUpdateCoordinator Pattern**: Centralized state management for all entities
  - Async polling every 30 seconds
  - State cache for all KNX group addresses
  - Proper coordinator lifecycle management
  - `async_config_entry_first_refresh()` support

- **Entity Base Class (LuxorLivingEntity)**:
  - Common functionality for all entity types
  - Device registry integration via `device_info` property
  - Coordinator listener management
  - Unique ID generation from entity attributes
  - `async_added_to_hass()` with automatic listener registration

- **Type Hints**: 100% coverage on critical platforms
  - All function parameters typed
  - All return types annotated
  - Enables IDE autocompletion and type checking

- **Code Quality Tools**:
  - Black formatter configuration (line-length=100, py313)
  - isort import organization (black profile)
  - mypy type checking (strict mode)
  - flake8 linting configuration
  - bandit security scanning
  - pre-commit hooks for automated checks
  - py.typed marker for PEP 561 support

- **Test Coverage Baseline**: 55% (1408 statements, 640 missed)
  - 74 comprehensive tests (100% passing)
  - Test suite includes platform imports, constants, coordinator structure
  - Coverage metrics per module documented

### Changed
- **Light Platform**: Complete refactoring
  - Now extends `LuxorLivingEntity` + `LightEntity`
  - Full type hints on all parameters
  - DataUpdateCoordinator integration
  - ConfigEntry support
  - Improved docstrings

- **Switch Platform**: Complete refactoring
  - Now extends `LuxorLivingEntity` + `SwitchEntity`
  - Full type hints coverage
  - DataUpdateCoordinator integration
  - Binary sensor dual-listener support

- **Binary Sensor Platform**: Enhanced with auto-detection
  - Now extends `LuxorLivingEntity` + `BinarySensorEntity`
  - Automatic device class detection
  - Full type hints implementation
  - Improved entity naming

- **Import Organization**: All files reformatted with isort
  - Stdlib → third-party → first-party ordering
  - Black-compatible formatting
  - Consistent throughout codebase

- **Documentation**: All docstrings and comments enhanced
  - Detailed parameter documentation
  - Return value descriptions
  - Usage examples on complex functions

### Fixed
- Device registry integration now properly implemented on all entities
- Inconsistent entity implementations across platforms
- Missing type hints causing IDE issues
- Import organization inconsistencies

### Quality Assurance

- ✅ **74/74 Tests Passing** (100% success rate)
- ✅ **Black Format**: 100% compliant (26 files)
- ✅ **Type Hints**: 100% on critical modules
- ✅ **Coverage Baseline**: 55% established
- ✅ **Code Style**: isort organized imports
- ✅ **Documentation**: CHANGELOG fully English

### Technical Details

**Coordinator Implementation:**
```python
class LuxorLivingCoordinator(DataUpdateCoordinator):
    """Manages state updates for all KNX entities."""
    
    def __init__(self, hass, host):
        super().__init__(hass, _LOGGER, name="Luxor Living", 
                         update_interval=timedelta(seconds=30))
        self.gateway = LuxorKNXGateway(host)
    
    async def _async_update_data(self):
        """Fetch data from KNX gateway."""
        try:
            return await self.gateway.get_all_states()
        except Exception as err:
            raise UpdateFailed(f"Error: {err}") from err
```

**Entity Base Class Benefits:**
- Automatic device info generation
- Listener registration/unregistration
- Unique ID handling
- Coordinator integration
- Common lifecycle management

**Type Hints Example:**
```python
def __init__(
    self,
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
    knx_gateway: LuxorKNXGateway,
) -> None:
    """Initialize light entity."""
```

### Known Issues

- Test coverage: 55% (ongoing improvement in 0.3.x)
- Climate, Cover, Sensor platforms: Development in progress
- Some REST client error paths: Need additional coverage

### Installation

**Via HACS:**
1. Open HACS → Integrations
2. Search for "LUXORliving"
3. Click Install
4. Restart Home Assistant
5. Settings → Devices & Services → Create Integration

**Manual:**
1. Download v0.3.0 release
2. Extract to `~/.homeassistant/custom_components/luxor_living/`
3. Restart Home Assistant

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
