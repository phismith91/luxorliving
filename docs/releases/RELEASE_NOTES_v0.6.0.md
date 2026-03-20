# 🎉 LUXORliving v0.6.0 (Final Release)

**Release Date:** 9. Januar 2026

### 🥈 Home Assistant Silver Compliance Features

This release implements features required for **Home Assistant Silver** quality
scale compliance.

### ✨ Added

- **🔐 Re-Authentication Flow**
  - Repair flow is triggered after 3 consecutive authentication failures
  - User-friendly credential update UI and automatic reconnection
  - Integration reload without reconfiguration after successful re-auth

- **🌍 Multi-Language Support**
  - German (de), French (fr), English (en)
  - Localized config flow, repair messages and UI strings

- **📚 End-user Documentation**
  - Added examples: Automations, Dashboard configurations, Compatible devices
    list

### 🐛 Bug fixes

- Fixed test fixture issue in performance benchmark tests
- Fixed coordinator initialization for HA 2026.8+ (pass `config_entry` to
  DataUpdateCoordinator)

### 🔧 Technical Improvements

- `repairs.py` added for re-auth repair flows
- Coordinator now tracks authentication failures and creates repair issues
- Improved translations and `strings.json` coverage
- HACS package structure correction (files at zip root)

### 🧪 Testing & Quality

- **Tests:** 212/212 passing
- **Quality gates:** README/CHANGELOG validation, HACS install test, zip
  structure validation

### ⚡ Upgrade Notes

- Remove any previously installed beta copies and nested directories before
  installing
- Install v0.6.0 via HACS and restart Home Assistant

---

For full changelog see `CHANGELOG.md`.
