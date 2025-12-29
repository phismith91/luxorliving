# LUXORliving v0.3.5 - HOTFIX

**Release Date:** 2025-12-26  
**Type:** Critical Hotfix

---

## 🔥 Critical Bug Fix

### Missing Import: DPT2ByteFloat

**Problem:**
- `DPT2ByteFloat` was used but not imported in `knx_gateway.py` (lines 407, 416)
- Caused `NameError` when processing 2-byte float KNX telegrams

**Impact:**

1. **Wetterstation Broken:**
   - Temperature, Wind, Lux sensors showed raw bytes: `[5, 223]` instead of `22.3°C`
   - Exception caught silently, fallback to raw value

2. **Bus Monitoring Disabled:**
   - Temperature telegrams not recognized (no 🌡️ emoji in logs)
   - ION temperature discovery impossible
   - Manual conversion required (impractical)

3. **All DPT 9.xxx Sensors Affected:**
   - Temperature (DPT 9.001)
   - Brightness (DPT 9.004)
   - Wind speed (DPT 9.005)
   - Pressure (DPT 9.006)
   - Humidity (DPT 9.007)

**Fix:**
```python
from xknx.dpt.dpt_9 import DPT2ByteFloat  # Added import
```

**Before (v0.3.4):**
```
DEBUG: Received telegram: 9.0.7 → 5/1/10, value=[5, 223]
```

**After (v0.3.5):**
```
INFO: 🌡️  KNX Temperature: 9.0.7 → 5/1/10 = 22.3°C (Response)
```

---

## 🎯 Why This Matters

- **Wetterstation works again** - Correct temperature/wind/lux values
- **ION Discovery enabled** - Can now find ION temperature addresses via logs
- **Bus Monitoring functional** - 🌡️ emoji makes filtering easy

---

## 📦 Installation

### Hotfix Deployment (Recommended)

Already deployed to production HA: `100.97.159.88`

**Via SSH:**
```bash
ssh -F /dev/null phil@100.97.159.88 "mkdir -p /tmp/luxor_deploy"
rsync -avz --exclude="__pycache__" \
  -e "ssh -F /dev/null" \
  custom_components/luxor_living/ \
  phil@100.97.159.88:/tmp/luxor_deploy/
ssh -F /dev/null phil@100.97.159.88 \
  "sudo cp -r /tmp/luxor_deploy/* /config/custom_components/luxor_living/ && \
   rm -rf /tmp/luxor_deploy"
```

Then restart HA: http://100.97.159.88:8123

### Via GitHub Release
1. Download from releases
2. Extract to `/config/custom_components/`
3. Restart Home Assistant

---

## ✅ Quality

- **Tests:** 86/86 passing (2.94s)
- **Fix verified:** Import correct, no errors
- **Regression:** None - simple import addition

---

## 🔗 Links

- **Repository:** https://github.com/phismith91/luxorliving
- **Issues:** https://github.com/phismith91/luxorliving/issues

---

**This is a critical hotfix for v0.3.4 - upgrade immediately if using Wetterstation or DPT 9.xxx sensors!**
