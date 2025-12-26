# v0.3.6 - CRITICAL HOTFIX: DPT 9.xxx Conversion

**Release Date:** 2025-12-26  
**Type:** Critical Hotfix (IMMEDIATE UPDATE RECOMMENDED)

---

## 🚨 Critical Bug Fix

### DPT 9.xxx (2-byte Float) Conversion Completely Broken

**Problem:**
- v0.3.5 added the import for `DPT2ByteFloat` but used it incorrectly
- `from_knx()` method expects a `DPTArray` object, NOT raw `bytes()`
- Result: Exception caught silently → fallback to raw bytes → sensors broken

**Impact:**
- ❌ **Wetterstation sensors:** Showed `(5, 20)` instead of `13.0°C`
- ❌ **All DPT 9.xxx sensors broken:** Temperature, Wind Speed, Lux, Humidity, Pressure
- ❌ **ION discovery impossible:** Temperature telegram logging with 🌡️ emoji didn't trigger

**Fix:**
```python
# BEFORE (v0.3.5 - BROKEN):
value = DPT2ByteFloat().from_knx(bytes(raw_value))  # ❌ Wrong!

# AFTER (v0.3.6 - FIXED):
value = DPT2ByteFloat().from_knx(payload_value)  # ✅ DPTArray object
```

---

## ✅ What's Fixed

### Sensor Value Conversion
- **Wetterstation Außentemperatur:** `(5, 20)` → `13.0°C` ✅
- **Wetterstation Windgeschwindigkeit:** `(1, 211)` → `4.67 m/s` ✅
- **Wetterstation Helligkeit:** `(0, 100)` → `100.0 lux` ✅
- **All other DPT 9.xxx sensors** now properly convert

### Temperature Telegram Logging
```
🌡️  KNX Temperature: 9.0.12 → 5/0/2 = 13.0°C (Write)
```
- Enables **ION temperature discovery** via bus monitoring
- Filter logs by 🌡️ emoji to find temperature group addresses

---

## 📥 Installation

### HACS (Recommended)
1. HACS → Integrations → LUXORliving → **Update to v0.3.6**
2. Restart Home Assistant
3. Verify Wetterstation sensors show temperatures, not tuples

### Manual
```bash
cd /config/custom_components/
wget https://github.com/phismith91/luxorliving/archive/refs/tags/v0.3.6.tar.gz
tar -xzf v0.3.6.tar.gz --strip-components=2 luxorliving-0.3.6/custom_components/luxor_living
rm v0.3.6.tar.gz
```

---

## 🔍 Quality Metrics

- **Tests:** ✅ 86/86 passing
- **API Fix:** `DPTArray` object now correctly passed to `from_knx()`
- **Production Testing:** Verified on remote HA with live Wetterstation data

---

## 📝 Files Changed

- `custom_components/luxor_living/knx_gateway.py`:
  - Line 408: Fixed `from_knx(payload_value)` (was `bytes(raw_value)`)
  - Line 416: Fixed tuple conversion with `DPTArray()` wrapper

---

## 🎯 Next Steps

**v0.4.0 Preview (Feature Branch):**
- Auto-discovery for all DPT 9.xxx sensors (ION temperatures)
- Options Flow for sensor management
- No more manual bus monitoring required!

---

## ⚠️ Upgrade Notice

**Breaking Changes:** None  
**Migration Required:** No  
**Recommended Action:** Update immediately if using Wetterstation or any DPT 9.xxx sensors

---

**Full Changelog:** https://github.com/phismith91/luxorliving/compare/v0.3.5...v0.3.6
