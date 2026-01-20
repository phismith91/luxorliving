# v0.6.1-beta.7 Release Notes

**Release Date:** 20. Januar 2026

**GitHub Release:** [v0.6.1-beta.7](https://github.com/phismith91/luxorliving/releases/tag/v0.6.1-beta.7)

---

## Overview

**v0.6.1-beta.7** is a critical fix release for **v0.6.1-beta.6** that corrects the ZIP file structure for HACS compatibility.

### What was fixed

In v0.6.1-beta.6, the release ZIP was incorrectly built with a nested directory structure:
```
luxor_living.zip
└── luxor_living/
    ├── manifest.json        ← WRONG: nested!
    ├── __init__.py
    └── ...
```

This caused HACS installation to fail because HACS unpacks directly into `custom_components/`, creating the broken path `custom_components/luxor_living/luxor_living/`.

**v0.6.1-beta.7 fixes this:**
```
luxor_living.zip
├── manifest.json            ← CORRECT: at root!
├── __init__.py
├── config_flow.py
└── ...
```

---

## Installation

### Via HACS (Recommended)

1. Open **HACS** → **Integrations**
2. Click **LUXORliving**
3. Click **Install** (pre-release: toggle enabled)
4. Restart Home Assistant
5. Go to **Settings** → **Devices & Services** → **Create Integration**
6. Search for **LUXORliving** and configure

### Manual Installation

```bash
# Download the ZIP
wget https://github.com/phismith91/luxorliving/releases/download/v0.6.1-beta.7/luxor_living.zip

# Extract directly into custom_components
unzip -d ~/.homeassistant/custom_components/ luxor_living.zip

# Verify extraction
ls ~/.homeassistant/custom_components/luxor_living/manifest.json  # Must exist
```

---

## Testing Results

✅ **All 301 tests passing**  
✅ **ZIP structure validated** (manifest.json at root)  
✅ **HACS compatibility verified**  
✅ **Code quality checks green**  
✅ **Security scans passed**

---

## Files Changed

- `custom_components/luxor_living/manifest.json` — Version bumped to 0.6.1-beta.7
- `.github/workflows/ci-cd.yml` — Fixed ZIP build command for correct HACS structure
- `docs/RELEASE_OPERATIONS.md` — Added explicit ZIP structure requirements
- `docs/ARCHITECTURE.md` — Added NO-GO items for release process
- `CHANGELOG.md` — Release notes added

---

## Known Limitations

- Pre-release version (beta) — use for testing only
- HACS auto-updates not yet available for pre-releases (manual update required)

---

## Support & Reporting

For issues or questions:

- **GitHub Issues:** [luxorliving/issues](https://github.com/phismith91/luxorliving/issues)
- **HACS Repository:** [phismith91/luxorliving](https://github.com/phismith91/luxorliving)

---

## Next Steps

- Install v0.6.1-beta.7 and test HACS integration discovery
- Verify all entity platforms load correctly
- Report any issues on GitHub

Enjoy LUXORliving! 🎉
