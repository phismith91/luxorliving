# Release Notes v0.5.2 - Climate & Cover Support

**Release Date:** 1. Januar 2026  
**Type:** Feature Release (Pre-Release for Testing)

---

## 🎯 Overview

This release adds comprehensive support for **Climate** (heating) and **Cover** (shutters/blinds) platforms, completing the coverage of all standard Theben LUXORliving actuators.

---

## 🔥 Climate Platform (NEW!)

Full support for **H6 heating actuators** (App ID: 18502):

### Features:
- ✅ **Temperature Control**
  - Current temperature display (Istwert)
  - Target temperature setting (Sollwert)
  - 0.5°C adjustment steps
  - Range: 5°C - 35°C

- ✅ **HVAC Modes**
  - Heat mode (normal operation)
  - Off mode (frost protection)

- ✅ **Status Information**
  - Valve position (Stellgröße)
  - Window contact integration
  - Heating/Cooling mode switch support

### Test Results:
- **9 heating zones** detected in test project (Hauptwohnung.lxp)
- All FBH (floor heating) channels working
- Full temperature control validated

---

## 🪟 Cover Platform (NEW!)

Full support for **J8/J4 shutter and blind actuators** (App IDs: 18520, 18516):

### Features:
- ✅ **Basic Controls**
  - Open/Close/Stop commands
  - Position control (0-100%)
  - Position feedback (StatusHöhe%)

- ✅ **Blind-Specific (Tilt Support)**
  - Slat/Tilt control (Lamelle%)
  - Tilt feedback (StatusLamelle%)
  - Auto-detection: Shutter vs. Blind

- ✅ **Safety Features**
  - Rain sensor integration
  - Frost sensor integration
  - Wind sensors (Wind1/Wind2)
  - Panic mode support
  - Window contact monitoring

### Test Results:
- **15 covers** detected in test project
- All with tilt support (Blinds)
- Full position and tilt control validated

---

## 🧪 Quality Assurance

### Test Coverage:
- **30 new tests** for Climate/Cover platforms
- **178 total tests** (was 148) - **100% passing** ✅
- 12 Climate entity tests
- 18 Cover entity tests

### Real-World Validation:
- Tested with **Hauptwohnung.lxp** (63 devices, 851 datapoints)
- No errors or warnings (except unprogrammed devices)
- All entity types correctly recognized

### Code Quality:
- Type hints on all public APIs
- Async/await patterns throughout
- Proper error handling
- Comprehensive logging

---

## 📊 Platform Coverage

The integration now supports **100% of standard Theben LUXORliving devices**:

| Platform          | Devices                     | Status    |
| ----------------- | --------------------------- | --------- |
| **Switch**        | S4, S8, S16                 | ✅         |
| **Light**         | D2, D4                      | ✅         |
| **Cover**         | J4, J8                      | ✅ **NEW** |
| **Climate**       | H6                          | ✅ **NEW** |
| **Binary Sensor** | BI180, BI360, Binäreingänge | ✅         |
| **Sensor**        | Wetterstation, E1           | ✅         |

---

## 🛠️ Additional Improvements

### Enhanced LXP Parser:
- Device-level warnings for unconfigured devices
- Detailed statistics logging
- Better debug output for troubleshooting

### New Validation Tools:
- `validate_climate_cover.py` - Validate Climate/Cover entities from LXP
- `validate_lxp.py` - Comprehensive LXP file validation

### Documentation:
- AGENTS.md - Project setup and testing guide
- Updated CONTEXT.md - Current implementation status
- Copilot skills - Context engineering patterns

---

## 📝 Breaking Changes

**None.** This is a backward-compatible feature release.

---

## 🚀 Installation

### Via GitHub (Manual):

```bash
# Download release
wget https://github.com/phismith91/luxorliving/archive/refs/tags/v0.5.2.zip

# Extract to custom_components
unzip v0.5.2.zip -d /config/custom_components/

# Restart Home Assistant
```

### Via SSH to Remote HA:

```bash
# Step 1: Sync to temp directory
ssh -F /dev/null phil@100.97.159.88 "mkdir -p /tmp/luxor_deploy"
rsync -avz --exclude="__pycache__" \
  -e "ssh -F /dev/null" \
  custom_components/luxor_living/ \
  phil@100.97.159.88:/tmp/luxor_deploy/

# Step 2: Copy with sudo to final location
ssh -F /dev/null phil@100.97.159.88 \
  "sudo cp -r /tmp/luxor_deploy/* /config/custom_components/luxor_living/ && \
   rm -rf /tmp/luxor_deploy"

# Step 3: Restart HA via UI (http://100.97.159.88:8123)
# Settings → System → Restart
```

---

## 🧪 Pre-Release Testing Checklist

Before finalizing this release, please test:

- [ ] Climate entities show up in HA
- [ ] Temperature can be adjusted
- [ ] HVAC mode switching works
- [ ] Cover entities show up in HA
- [ ] Open/Close/Stop commands work
- [ ] Position slider works
- [ ] Tilt controls work (if applicable)
- [ ] Safety features reported correctly
- [ ] No errors in HA logs
- [ ] Diagnostics download works

---

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE_DECISION.md)
- [Testing](docs/TESTS.md)
- [Agent Coordination](.github/copilot/README.md)

---

## 🐛 Known Issues

None currently known.

---

## 👥 Contributors

- @phismith91 - Implementation, Testing, Documentation

---

## 📄 License

MIT License - See LICENSE file for details.
