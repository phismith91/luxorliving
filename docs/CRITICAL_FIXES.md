# 🔧 Critical Fixes - Action Plan

**Priority:** P0 (BLOCKER)  
**ETA:** ~1 hour  
**Status:** Ready to implement

---

## ❌ CRITICAL ISSUE #1: Memory Leak in Entities

### Files to Fix:
- `custom_components/luxor_living/light.py`
- `custom_components/luxor_living/switch.py`
- `custom_components/luxor_living/binary_sensor.py` (if using listeners)

### Implementation:

```python
# Add to LuxorLivingLight class:
async def async_will_remove_from_hass(self) -> None:
    """Clean up listener when entity is removed."""
    if self._address_status:
        self._knx_gateway.unregister_listener(
            self._address_status, 
            self._handle_knx_update
        )
    await super().async_will_remove_from_hass()
```

```python
# Add to LuxorLivingDimmableLight class:
async def async_will_remove_from_hass(self) -> None:
    """Clean up listeners when entity is removed."""
    if self._address_dim:
        self._knx_gateway.unregister_listener(
            self._address_dim, 
            self._handle_brightness_update
        )
    await super().async_will_remove_from_hass()
```

```python
# Add to LuxorLivingSwitch class:
async def async_will_remove_from_hass(self) -> None:
    """Clean up listener when entity is removed."""
    if self._address_status:
        self._knx_gateway.unregister_listener(
            self._address_status, 
            self._handle_knx_update
        )
    await super().async_will_remove_from_hass()
```

**ETA:** 15 minutes

---

## ❌ CRITICAL ISSUE #2: DPT Percent Encoding Bug

### File: `custom_components/luxor_living/knx_gateway.py`

### Line 140 - Current Code:
```python
elif value_type == "percent":
    # DPT 5.001 (0-100%)
    payload = GroupValueWrite(DPTArray(int(value * 255 / 100)))
```

### Fix:
```python
elif value_type == "percent":
    # DPT 5.001 (0-100%) - must be list!
    byte_value = int(value * 255 / 100)
    payload = GroupValueWrite(DPTArray([byte_value]))
```

**ETA:** 2 minutes

---

## ❌ CRITICAL ISSUE #3: Incomplete DPT Decoding

### File: `custom_components/luxor_living/knx_gateway.py`

### Line 246 - Current Code:
```python
elif isinstance(telegram.payload.value, DPTArray):
    # For DPT arrays, we'll need to decode based on type
    # For now, just get the raw value
    value = telegram.payload.value.value
```

### Fix:
```python
elif isinstance(telegram.payload.value, DPTArray):
    raw_value = telegram.payload.value.value
    # Decode based on length (DPT type indicator)
    if isinstance(raw_value, (list, bytes)) and len(raw_value) == 1:
        # DPT 5.001 (percent): 0-255 → 0-100
        value = int(raw_value[0] * 100 / 255)
    else:
        # Unknown DPT - return raw value
        value = raw_value
```

**ETA:** 5 minutes

---

## ❌ CRITICAL ISSUE #4: Race Condition in Listener

### File: `custom_components/luxor_living/knx_gateway.py`

### Line 262 - Current Code:
```python
# Notify listeners
if group_address in self._listeners:
    for callback in self._listeners[group_address]:
        try:
            await self.hass.async_add_executor_job(
                callback, group_address, value
            )
```

### Fix:
```python
# Notify listeners
if group_address in self._listeners:
    # Create snapshot to avoid modification during iteration
    callbacks = list(self._listeners[group_address])
    for callback in callbacks:
        # Check if still registered (could be removed during iteration)
        if callback not in self._listeners.get(group_address, []):
            continue
        try:
            await self.hass.async_add_executor_job(
                callback, group_address, value
            )
```

**ETA:** 5 minutes

---

## ❌ CRITICAL ISSUE #5: Missing Error Handling in Setup

### File: `custom_components/luxor_living/__init__.py`

### Line 53 - Current Code:
```python
if lxp_path and lxp_path.exists():
    _LOGGER.info("Parsing LXP file: %s", lxp_path)
    parser = LXPParser(str(lxp_path))
    project = await parser.parse()
    
    # Create entity mapper
    mapper = EntityMapper(project)
```

### Fix:
```python
if lxp_path and lxp_path.exists():
    _LOGGER.info("Parsing LXP file: %s", lxp_path)
    try:
        parser = LXPParser(str(lxp_path))
        project = await parser.parse()
        
        # Create entity mapper
        mapper = EntityMapper(project)
    except ET.ParseError as err:
        _LOGGER.error("Invalid LXP XML file: %s", err)
        return False
    except Exception as err:
        _LOGGER.exception("Failed to parse LXP file: %s", err)
        return False
```

**Also add import:**
```python
import xml.etree.ElementTree as ET
```

**ETA:** 5 minutes

---

## 📋 Testing Checklist

After implementing fixes, test:

### Test 1: Memory Leak Fix
```bash
# 1. Start HA with integration
# 2. Delete an entity
# 3. Check logs for unregister calls
# 4. Restart integration → No callbacks to removed entities
```

### Test 2: Dimmer Functionality
```bash
# 1. Turn on dimmable light
# 2. Set brightness to 50%
# 3. Check KNX telegram logs → Should send [127] (50% of 255)
# 4. Verify no TypeError exceptions
```

### Test 3: Brightness Status Updates
```bash
# 1. Manually send KNX telegram with brightness value
# 2. Entity should update to correct percentage
# 3. Check: Raw value 255 → 100%, Raw value 127 → 50%
```

### Test 4: Config Entry Reload
```bash
# 1. Reload integration while entities exist
# 2. No race condition errors in logs
# 3. All listeners properly re-registered
```

### Test 5: Invalid LXP File
```bash
# 1. Create invalid XML file
# 2. Try to set up integration
# 3. Should show clear error message
# 4. No uncaught exceptions
```

---

## 🚀 Deployment Steps

1. **Implement all 5 fixes** (30 minutes)
2. **Run local tests** (15 minutes)
3. **Check logs for errors** (5 minutes)
4. **Commit changes** (5 minutes)
5. **Push to feature branch** (5 minutes)

**Total Time:** ~1 hour

---

## ✅ Success Criteria

- [ ] No memory leaks (entities clean up listeners)
- [ ] Dimmer works correctly (brightness 0-100%)
- [ ] Status updates decode correctly
- [ ] No race conditions in listener callbacks
- [ ] Invalid LXP files handled gracefully
- [ ] All tests pass
- [ ] No errors in Home Assistant logs

---

## 📝 Commit Message Template

```
fix(critical): Resolve memory leaks and KNX encoding issues

CRITICAL FIXES:
- Add async_will_remove_from_hass() to prevent listener memory leaks
- Fix DPT 5.001 encoding (percent must be byte array)
- Implement proper DPT decoding for status updates
- Prevent race condition in listener iteration
- Add error handling for LXP XML parsing

These changes fix 5 critical issues identified in quality audit.

Closes #XX (if issue exists)
```

---

## 🔍 Post-Fix Verification

Run quality audit again:
```bash
# Check for remaining issues
grep -r "TODO\|FIXME" custom_components/luxor_living/
pylint custom_components/luxor_living/
```

Expected result:
- ✅ No critical issues
- ✅ Memory leaks resolved
- ✅ All KNX communication functional
- ✅ Ready for beta testing

---

**Ready to implement?** Let me know and I'll apply all fixes! 🔧
