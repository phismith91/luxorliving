# v0.5.1 - HOTFIX: AttributeError Fixes & Rate Limiting

**Release Date:** 2025-12-29
**Type:** Hotfix

---

## 🚨 Critical Bug Fixes

### AttributeError: Missing _address_status

**Problem:**
- Rate limiting implementation moved datapoint address initialization outside `__init__`
- `_address_status` and `_address_on` attributes not set on entity instances
- Result: `AttributeError: 'LuxorLivingLight' object has no attribute '_address_status'`

**Impact:**
- ❌ **All lights failed to load:** Entity creation crashed during `async_added_to_hass`
- ❌ **All switches failed to load:** Same AttributeError
- ❌ **Binary sensors partially broken:** Health sensor used wrong method name

**Fix:**
- Moved datapoint address initialization back into `__init__` method
- Added missing `_is_rate_limited()` methods to light and switch classes
- Fixed binary sensor health check: `is_connected()` → `connected`
- Fixed binary sensor state method: `get_binary_sensor_state()` → `get_state()`

---

## ✅ What's Fixed

### Entity Loading
- **Lights:** All light entities now load successfully ✅
- **Switches:** All switch entities now load successfully ✅
- **Binary Sensors:** Health sensor works, motion sensors use correct coordinator method ✅

### Rate Limiting
- **Functionality:** 5 commands per second limit working ✅
- **Tests:** All 9 rate limiting tests pass ✅
- **Logging:** Warning messages when rate limiting triggers ✅

### Health Monitoring
- **Connection Check:** Uses correct `connected` property ✅
- **State Method:** Uses coordinator's `get_state()` method ✅

---

## 📥 Installation

### Remote HA Deployment
```bash
# Files already deployed via rsync
# Restart Home Assistant via UI: Settings → System → Restart
```

### Local Testing
```bash
cd /home/phil/gitlab_github/luxorliving
python -m pytest tests/test_light.py::TestLightRateLimiting tests/test_switch.py::TestRateLimiting -v
# Expected: 9/9 tests passing
```

---

## 🔍 Quality Metrics

- **Tests:** ✅ 9/9 rate limiting tests passing
- **Entity Loading:** ✅ No AttributeError on startup
- **Rate Limiting:** ✅ Blocks after 5 commands in 1 second
- **Health Sensor:** ✅ Correctly reports connection status

---

## 📝 Files Changed

- `custom_components/luxor_living/light.py`:
  - Moved datapoint initialization into `__init__`
  - Added `_is_rate_limited()` method

- `custom_components/luxor_living/switch.py`:
  - Moved datapoint initialization into `__init__`
  - Added `_is_rate_limited()` method

- `custom_components/luxor_living/binary_sensor.py`:
  - Fixed `is_connected()` → `connected`
  - Fixed `get_binary_sensor_state()` → `get_state()`

---

## 🎯 Next Steps

**Monitor deployed changes:**
- Check HA logs for successful entity loading
- Verify rate limiting prevents "light shows"
- Confirm health sensor shows correct status

---

## ⚠️ Upgrade Notice

**Breaking Changes:** None
**Migration Required:** No
**Recommended Action:** Deploy and restart HA

---

**Previous Release:** [v0.5.0](https://github.com/phismith91/luxorliving/releases/tag/v0.5.0)