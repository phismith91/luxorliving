# Home Assistant Core Integration Readiness Assessment

**Date:** 23. Dezember 2025  
**Integration:** LUXORliving v0.3.0-beta.1  
**Target:** Home Assistant Core (homeassistant/components/)

---

## Executive Summary

**Core Readiness:** ⚠️ **NOT READY - Significant Work Required**  
**Current State:** Community integration (HACS)  
**Effort Estimate:** 3-4 weeks of focused development  
**Blocking Issues:** 5 critical items must be fixed

**Core Compliance Score: 3.5/10**

| Category | Score | Status |
|----------|-------|--------|
| **Code Architecture** | 2/10 | ❌ No coordinator pattern |
| **Testing** | 2/10 | ❌ 52% coverage (need 80%+) |
| **Type Hints** | 4/10 | ⚠️ Partial implementation |
| **Device Registry** | 0/10 | ❌ Not implemented |
| **Documentation** | 2/10 | ❌ No HA.io page |
| **Code Style** | 6/10 | ⚠️ Good but incomplete |

---

## ❌ BLOCKING ISSUES (Must Fix for Core)

### 1. Missing DataUpdateCoordinator Pattern (CRITICAL)

**Issue:** Integration directly instantiates `LuxorKNXGateway` without using `DataUpdateCoordinator`

**Current Code (__init__.py):**
```python
async def async_setup_entry(hass, entry):
    knx_gateway = LuxorKNXGateway(...)
    await knx_gateway.async_setup()
    hass.data[DOMAIN][entry.entry_id] = {"gateway": knx_gateway}
```

**Core Requirement:**
```python
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class LuxorLivingCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host):
        super().__init__(
            hass,
            _LOGGER,
            name="Luxor Living",
            update_interval=timedelta(seconds=30),
        )
        self.gateway = LuxorKNXGateway(host)
    
    async def _async_update_data(self):
        try:
            # Fetch data from KNX
            return await self.gateway.get_all_states()
        except Exception as err:
            raise UpdateFailed(f"Error: {err}") from err

async def async_setup_entry(hass, entry):
    coordinator = LuxorLivingCoordinator(hass, entry.data[CONF_HOST])
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
```

**Impact:** Entities must be linked to coordinator for proper state sync  
**Effort:** 1-2 days

---

### 2. Missing Device Registry Integration (CRITICAL)

**Issue:** Entities don't implement `device_info` property with proper device registry

**Current Code (light.py):**
```python
class LuxorLivingLight(LightEntity):
    # ❌ No device_info property
    # Entities appear as orphaned in device registry
```

**Core Requirement:**
```python
from homeassistant.helpers.device_registry import DeviceInfo

class LuxorLivingEntity(LightEntity):
    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._gateway_id)},
            name="Luxor Living Gateway",
            manufacturer="Theben",
            model="BAOS 777",
            hw_version="1.0",
            sw_version="7.x",
        )

class LuxorLivingLight(LuxorLivingEntity):
    @property
    def device_info(self) -> DeviceInfo:
        parent = super().device_info
        parent["via_device"] = (DOMAIN, self._gateway_id)
        return parent
```

**Impact:** Entities linked to devices in HA UI  
**Files:** light.py, switch.py, binary_sensor.py, entity_mapper.py  
**Effort:** 1 day

---

### 3. Insufficient Test Coverage (CRITICAL)

**Current State:** 52% coverage (623/1198 statements)  
**Core Requirement:** 80%+ coverage (HA core-components/tester requirement)  
**Gap:** ~228 statements need test coverage

**Missing Tests:**
- ❌ config_flow error handling (invalid_auth, cannot_connect flows)
- ❌ knx_gateway telegram handling edge cases
- ❌ entity_mapper DPT type detection
- ❌ lxp_parser file corruption handling
- ❌ binary_sensor state updates
- ❌ sensor platform (currently stub)
- ❌ climate platform (currently stub)
- ❌ cover platform (currently stub)

**Core Test Requirements:**
```python
# tests/test_config_flow.py - MUST cover all error paths
async def test_step_user_cannot_connect(hass):
    result = await hass.config_entries.flow.async_init(...)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "unreachable.local", ...}
    )
    assert result["type"] == FlowResult.FORM
    assert result["errors"]["base"] == "cannot_connect"

# tests/test_init.py - MUST cover setup/unload
async def test_async_setup_entry(hass, mock_coordinator):
    entry = MockConfigEntry(...)
    result = await hass.config_entries.async_setup(entry.entry_id)
    assert result
    assert hass.data[DOMAIN][entry.entry_id]

async def test_async_unload_entry(hass, setup_integration):
    entry = setup_integration
    result = await hass.config_entries.async_unload(entry.entry_id)
    assert result
    assert entry.entry_id not in hass.data[DOMAIN]
```

**Files to Add:**
- `tests/test_entity_integration.py` - Entity coordinator linkage
- `tests/test_device_registry.py` - Device info generation
- `tests/test_knx_protocols.py` - All telegram types
- `tests/test_lxp_edge_cases.py` - File parsing edge cases

**Effort:** 3-4 days

---

### 4. Missing Type Hints (CRITICAL)

**Current State:** Many functions missing return type hints and parameter types

**Examples (light.py):**
```python
# ❌ Missing return type
def __init__(self, mapped_entity, knx_gateway):  # No types!
    
# ❌ Missing parameter types  
def _handle_knx_update(self, group_address, value):
    
# ✅ Good examples (some functions have hints)
async def async_added_to_hass(self) -> None:
```

**Core Requirement:** 100% type hint coverage on all functions

**Files to Fix:**
- light.py: 15+ functions missing hints
- switch.py: 10+ functions missing hints  
- knx_gateway.py: 20+ functions missing hints
- entity_mapper.py: 10+ functions missing hints
- lxp_parser.py: 15+ functions missing hints
- config_flow.py: 5+ functions missing hints

**Pattern Fix:**
```python
# Before
def __init__(self, mapped_entity, knx_gateway):

# After
from __future__ import annotations
from typing import Any
from homeassistant.components.light import LightEntity

def __init__(
    self, 
    mapped_entity: MappedEntity,  # Import MappedEntity type
    knx_gateway: LuxorKNXGateway,
) -> None:
```

**Effort:** 2 days

---

### 5. Missing Home Assistant Core Documentation (CRITICAL)

**Issue:** No documentation page on home-assistant.io (required for official integrations)

**Required:**
- Create `/components/luxor_living/` folder in HA docs
- Document configuration options (YAML deprecated, Config Flow required)
- Document supported platforms and features
- Document known limitations
- Create troubleshooting section

**Example Structure:**
```
docs/components/luxor_living/index.md
- Overview
- Installation (Core only, not HACS)
- Configuration (Config Flow)
- Supported Platforms (lights, switches, binary sensors)
- Entities Created
- Automations Examples
- Troubleshooting

docs/components/luxor_living/images/
- installation-screenshot.png
- entities-screenshot.png
```

**Effort:** 1 day

---

## ⚠️ HIGH PRIORITY (Must Fix Before Submission)

### 1. Entity Base Class Organization (HIGH)

**Issue:** Light and Switch classes duplicate code, no shared base class

**Current:**
```python
# light.py - 321 lines, lots of duplication
class LuxorLivingLight(LightEntity):
    def __init__(self, mapped_entity, knx_gateway): ...
    async def async_added_to_hass(self): ...
    def _handle_knx_update(self, ...): ...

# switch.py - 201 lines, same pattern
class LuxorLivingSwitch(SwitchEntity):
    def __init__(self, mapped_entity, knx_gateway): ...
    async def async_added_to_hass(self): ...
    def _handle_knx_update(self, ...): ...
```

**Required for Core:**
```python
# entity.py - NEW FILE - Shared base class
from homeassistant.helpers.entity import Entity

class LuxorLivingEntity(Entity):
    """Base entity with common functionality."""
    
    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        mapped_entity: MappedEntity,
    ) -> None:
        self.coordinator = coordinator
        self._mapped_entity = mapped_entity
    
    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(...)
    
    async def async_added_to_hass(self) -> None:
        # Coordinator listener
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
        # KNX listener
        self.coordinator.gateway.register_listener(...)
    
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

# light.py - SIMPLIFIED
class LuxorLivingLight(LuxorLivingEntity, LightEntity):
    # Only Light-specific code
    ...

# switch.py - SIMPLIFIED
class LuxorLivingSwitch(LuxorLivingEntity, SwitchEntity):
    # Only Switch-specific code
    ...
```

**Effort:** 1 day

---

### 2. Code Style & Formatting (HIGH)

**Missing:**
- ❌ No Black formatter check
- ❌ No isort import sorting
- ❌ Inconsistent docstring formats
- ❌ No `py.typed` marker file

**Required:**
```bash
# Install
pip install black isort

# Format code
black custom_components/luxor_living/ --line-length=88
isort custom_components/luxor_living/ --profile black

# Create marker
touch custom_components/luxor_living/py.typed
```

**Effort:** 0.5 days (mostly automated)

---

### 3. CHANGELOG.md Format (HIGH)

**Current:** German changelog with ✨ emoji

**Core Requirement:** English, [Keep a Changelog](https://keepachangelog.com/) format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2025-12-23

### Added
- Initial release with Light, Switch, Binary Sensor platforms
- Config Flow setup via Home Assistant UI
- Automatic entity discovery from LXP project files
- KNX/IP Tunneling and Routing modes

### Changed
- Refactored to use DataUpdateCoordinator pattern
- Improved device registry integration

### Fixed
- Version consistency for Core integration
```

**Effort:** 0.5 days

---

## 📋 Medium Priority (Before v1.0.0)

### 1. Complete Missing Platforms (MEDIUM)

**Current Stubs:**
- sensor.py: Empty, needs temperature/brightness support
- climate.py: Empty, needs thermostat support
- cover.py: Empty, needs blinds/shutter support

**Each platform needs:**
- ~100 lines of implementation
- 15+ test cases
- Entity class with device_info
- Coordinator integration

**Effort:** 3-4 days

---

### 2. Add Integration Translations (MEDIUM)

**Required:**
- `strings/en.json` (currently named `strings.json` in root)
- Move to proper location: `custom_components/luxor_living/strings/en.json`

**Effort:** 0.5 days

---

## Summary: Path to Home Assistant Core

### Phase 1: Critical Fixes (1-2 weeks)
1. ✅ Add DataUpdateCoordinator pattern
2. ✅ Implement device registry (device_info)
3. ✅ Add type hints to all functions
4. ✅ Increase test coverage to 80%+
5. ✅ Create HA.io documentation page

**Deliverable:** v0.4.0 (Pre-Core version)

### Phase 2: Code Quality (3-4 days)
1. ✅ Refactor entity base classes
2. ✅ Format with Black/isort
3. ✅ Update CHANGELOG.md
4. ✅ Migrate translations

**Deliverable:** v1.0.0 (Ready for Core PR)

### Phase 3: Submission (1-2 weeks)
1. Create discussion in home-assistant/core
2. Open PR against home-assistant/core
3. Address code review feedback
4. Merge and release

**Timeline:** ~1 month total from current state

---

## Next Steps

To proceed with Core integration:

1. **Immediate (This Week):**
   ```bash
   # Create coordinator.py
   # Add device_info to all entities
   # Add type hints (automated or manual)
   ```

2. **Week 2:**
   ```bash
   # Write tests for 80% coverage
   # Complete entity base class refactoring
   # Create HA.io documentation
   ```

3. **Week 3-4:**
   ```bash
   # Test Core submission locally
   # Prepare PR for home-assistant/core
   # Address feedback and iterate
   ```

---

## Recommendation

**Current Status:** ✅ Excellent HACS integration, ❌ Not ready for Core

**Suggestion:**
1. Stay in HACS for v0.3.x-v0.4.x
2. Use feedback from HACS users
3. Refactor for Core requirements in v1.0.0 milestone
4. Submit to Core after v1.0.0 release

**Benefits of waiting:**
- Real-world usage validates design
- Fixes edge cases discovered by users
- Stronger submission with mature codebase
- Better chance of acceptance

