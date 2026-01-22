# Home Assistant Update Preparation: 2026.1.x & OS 17.0

**Status:** Preparation Phase
**Target Versions:**
- Home Assistant Core: 2025.12.0 → 2026.1.2
- Home Assistant OS: 16.3 → 17.0

**Date:** 2026-01-22

---

## Executive Summary

This document outlines the preparation steps and impact analysis for updating:
1. **Home Assistant Core** from 2025.12.0 to 2026.1.2
2. **Home Assistant OS** from 16.3 to 17.0

### Impact Assessment
- **Luxor Living Integration:** ✅ Low Impact (no breaking changes affecting our integration)
- **HA OS Upgrade:** ⚠️ Moderate Impact (storage migration required, USB-Serial issues reported)
- **Testing Required:** Yes (full test suite + manual verification)

---

## Home Assistant Core Updates

### Version Path: 2025.12.0 → 2026.1.0 → 2026.1.1 → 2026.1.2

#### 2026.1.0 - Main Release (Jan 7, 2026)

**Breaking Changes:**
1. **Coolmaster Integration** - Climate entities use `medium` instead of `med` for fan mode
2. **Tailscale Integration** - "Supports hairpinning" binary sensor removed
3. **UniFi Protect Integration** - Select states changed to snake_case (`Mechanical` → `mechanical`)
4. **Telegram Bot Integration** - Extra/unused parameters no longer accepted
5. **VeSync Integration** - Fan mode `advancedSleep` → `advanced_sleep`

**API Changes for Developers:**
- New "choose selector" for integration developers
- ESPHome API action responses enabled (bidirectional JSON exchange)

#### 2026.1.1 - Patch Release

**Key Fixes:**
- Hikvision NVR binary sensors detection fixed
- ZHA bumped to 0.0.84
- pyOverkiz bumped to 1.19.4
- JSON serialization of time objects in anthropic tool results fixed
- Trigger selectors fixed
- Reverted voluptuous and voluptuous-openapi update

#### 2026.1.2 - Latest Patch Release

**Key Updates:**
- KNX frontend updated to 2026.1.15.112308
- Blueprint WebSocket commands require admin (security improvement)
- aiomealie bumped to 1.2.0
- Frontend updated to 20260107.2
- aioairzone updated to v1.0.5
- Airzone Q-Adapt select entities fixed
- Reverted to microVAD for assist pipeline
- opower bumped to 0.16.2

---

## Home Assistant OS 17.0

### Major Changes

#### ⚠️ CRITICAL: Platform Support Changes
**Dropped Support for 32-bit ARM:**
- Raspberry Pi 2/3/4 (32-bit)
- ODROID-XU4
- ASUS Tinker Board

**Impact:** Not applicable (assuming 64-bit platform)

#### Docker & Storage Changes
**Docker Upgrade:** v29.1.3 with containerd v2.2.0
- New installations use Docker containerd snapshotter by default
- **Migration Required** for existing installations: `ha docker migrate-storage-driver`
- **Storage Requirements:** Recommend 50% free space before migration
- **Expected Storage Increase:** 1-3 GB additional space

#### System Updates
- Linux kernel updated to latest version
- Console keyboard layout configurable via localectl
- IPv6 enabled for Home Assistant Add-ons by default

### Known Issues

⚠️ **Critical Issues:**
1. **USB-Serial Converters** - Issues reported on:
   - Home Assistant Yellow
   - Some USB-Serial converters on Raspberry Pi
   - **Mitigation:** Downgrade to OS 16.0 if affected

2. **Storage Usage Increase** - Expected 1-3 GB increase after migration

3. **Update Failures** - Some Proxmox VM users report "Remote I/O error"

4. **GPU Access** - Some users lost GPU access in Frigate after upgrade

---

## Luxor Living Integration Impact Analysis

### Affected Components: ✅ None Identified

Our integration does not use any of the changed integrations:
- ❌ Coolmaster (not used)
- ❌ Tailscale (not used)
- ❌ UniFi Protect (not used)
- ❌ Telegram Bot (not used)
- ❌ VeSync (not used)

### Dependency Analysis

**Current Requirements:** (from `requirements_dev.txt`)
```
homeassistant>=2025.12.0
xknx>=3.13.0
voluptuous>=0.15.2
defusedxml>=0.7.1
pytest>=8.3.4
pytest-cov>=6.0.0
pytest-homeassistant-custom-component>=0.17.0
```

**Potential Concerns:**
1. ✅ voluptuous - HA 2026.1.1 reverted voluptuous update, likely compatible
2. ✅ pytest-homeassistant-custom-component - Should be compatible with 2026.1.x

### API Compatibility
- No deprecated APIs used in our integration
- No use of changed selectors or entity states
- KNX/IP integration (xknx) not affected by core changes

---

## Testing Strategy

### Pre-Update Testing (Current: 2025.12.0)
1. ✅ Run full test suite
2. ✅ Verify all integration tests pass
3. ✅ Document baseline behavior

### Post-Update Testing (Target: 2026.1.2)

#### Automated Tests
1. Run full pytest suite
2. Verify coverage remains stable
3. Check for deprecation warnings

#### Manual Verification
1. **Climate Entity** - Test all state changes and attributes
2. **Config Flow** - Verify setup and configuration flows
3. **KNX Communication** - Test device discovery and communication
4. **Error Handling** - Verify error conditions handled correctly

#### Integration Points
1. Test HA Core event system
2. Verify entity registry interactions
3. Check service calls work correctly
4. Validate YAML configuration compatibility

---

## Update Execution Plan

### Phase 1: Local Development Environment
1. Create backup of current environment
2. Update `requirements_dev.txt`: `homeassistant>=2026.1.2`
3. Rebuild development environment
4. Run automated test suite
5. Perform manual verification

### Phase 2: CI/CD Validation
1. Push updated requirements to feature branch
2. Verify all CI checks pass:
   - Pre-commit checks
   - Code Quality
   - Test suite (Python 3.13)
   - HACS validation
   - hassfest validation
3. Review coverage reports

### Phase 3: Production Update
1. Merge feature branch to main
2. Tag release with updated HA requirements
3. Update README with supported HA versions
4. Notify users via release notes

### Phase 4: HA OS Update (if applicable)
⚠️ **Only if running on Home Assistant OS:**

1. **Pre-Update:**
   - Verify at least 50% free storage space
   - Create full backup
   - Document current USB-Serial device status

2. **Update:**
   - Update to Home Assistant OS 17.0
   - Run migration: `ha docker migrate-storage-driver`
   - Monitor storage usage

3. **Post-Update:**
   - Verify USB-Serial devices still working
   - Check integration functionality
   - Monitor system stability for 24h

4. **Rollback Plan:**
   - If USB-Serial issues: Downgrade to OS 16.0
   - Restore from backup if needed

---

## Security Considerations

### CVE-2025-67221 (orjson)
**Status:** ⚠️ Still Present
- Home Assistant 2026.1.2 pins `orjson==3.11.3`
- Fixed version: `orjson>=3.11.5`
- **Current Mitigation:** CVE allowlisted in CI (commit a70b600)
- **Tracking:** Issue #62
- **Next Steps:** Monitor upstream HA releases for orjson update

---

## Rollback Plan

### If Issues Occur Post-Update:

1. **Development Environment:**
   ```bash
   # Revert requirements_dev.txt
   homeassistant>=2025.12.0

   # Rebuild environment
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements_dev.txt
   ```

2. **CI/CD:**
   - Revert commit with HA version bump
   - Re-run CI to confirm stability

3. **Production HA OS:**
   - Restore from backup
   - Downgrade to OS 16.0 if USB-Serial issues

---

## Open Questions

1. **Production Environment Details:**
   - What hardware is running Home Assistant? (affects OS upgrade decision)
   - Are USB-Serial converters in use? (affects OS 17.0 compatibility)
   - Current storage capacity? (affects migration readiness)

2. **Update Timing:**
   - When should we schedule the update?
   - Is there a maintenance window available?
   - Should we wait for 2026.1.3 or later patches?

3. **Monitoring:**
   - What metrics should we monitor post-update?
   - Alert thresholds for storage usage?
   - Rollback trigger conditions?

---

## References

### Home Assistant Core
- [2026.1 Main Release](https://www.home-assistant.io/blog/2026/01/07/release-20261)
- [Full Changelog 2026.1](https://www.home-assistant.io/changelogs/core-2026.1/)
- [Release 2026.1.1](https://github.com/home-assistant/core/releases/tag/2026.1.1)
- [Release 2026.1.2](https://github.com/home-assistant/core/releases/tag/2026.1.2)

### Home Assistant OS
- [OS 17.0 Release](https://github.com/home-assistant/operating-system/releases)
- [OS 17.0 Discussion](https://github.com/home-assistant/operating-system/discussions/4487)
- [OS 17.0 RC1 Discussion](https://github.com/home-assistant/operating-system/discussions/4440)

### Related Issues
- [Issue #62 - CVE-2025-67221 (orjson)](https://github.com/phismith91/luxorliving/issues/62)
- [Closed PR #63 - Experimental HA bump](https://github.com/phismith91/luxorliving/pull/63)

---

## Next Steps

1. ✅ Review this document and answer open questions
2. ⏳ Create feature branch for HA 2026.1.2 update
3. ⏳ Update requirements and run local tests
4. ⏳ Submit PR and verify CI passes
5. ⏳ Schedule production update if all tests pass
6. ⏳ Monitor for orjson CVE fix in future HA releases

---

**Document Version:** 1.0
**Last Updated:** 2026-01-22
**Author:** Automated preparation by Claude Code
