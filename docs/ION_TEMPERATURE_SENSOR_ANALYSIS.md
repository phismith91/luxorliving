# ION4/ION-8 Temperature Sensor Analysis

## Summary

ION4 and ION-8 devices have **built-in temperature sensors** on channel 0 that measure room temperature. These sensors are **currently NOT shown** in Home Assistant because they are marked with `affected="0"` in the LXP file.

## LXP Structure Analysis

### ION4 Device Example (iON4-3)

```xml
<device serialNumber="$00481a006e57" name="iON4-3" appId="1044" address="9.0.7" maskVersion="1968">
    <!-- Temperature sensor on channel 0 - HIDDEN because affected="0" -->
    <sensor name="iON4-3 (°C) " channel="0" affected="0">
        <parameter value="0" name="abgleichwert" type="int"/>
        <parameter value="8" name="longPressTime" type="int"/>
        <!-- NO datapoints defined - temperature is read-only from device -->
    </sensor>
    
    <!-- Touch buttons on channels 1-4 with affected="1" -->
    <sensor name="AP1_SZ/Bett Fenster/iON4-3 T1" channel="1" affected="1">
        <datapoint address="2312" role="status@OnOff"/>
        <datapoint address="2056" role="OnOff"/>
    </sensor>
    <!-- ... T2, T3, T4 ... -->
</device>
```

### ION8 Device Example (iON8-4)

```xml
<device serialNumber="$00482100391b" name="iON8-4" appId="1048" address="9.0.3" maskVersion="1968">
    <!-- Temperature sensor on channel 0 - HIDDEN because affected="0" -->
    <sensor name="iON8-4 (°C) " channel="0" affected="0">
        <parameter value="0" name="istValueSource" type="int"/>
        <parameter value="8" name="functionNumber" type="int"/>
        <parameter value="1" name="heatingCoolingFormat" type="int"/>
        <parameter value="0" name="activateRTR" type="int"/>
        <parameter value="1" name="favoriteA" type="int"/>
        <parameter value="1" name="favoriteB" type="int"/>
        <parameter value="0" name="displaySwitchOffTime" type="int"/>
        <parameter value="1" name="regelFunktion" type="int"/>
        <parameter value="0" name="abgleichwert" type="int"/>
        <!-- NO datapoints defined - temperature is read-only from device -->
    </sensor>
    
    <!-- Touch buttons on channels 1-8 -->
    <sensor name="iON8-4 T1" channel="1" affected="1">
        <datapoint address="2319" role="status@OnOff"/>
        <datapoint address="2063" role="OnOff"/>
    </sensor>
    <!-- ... T2-T8, some affected="0", some affected="1" ... -->
</device>
```

## Key Findings

### 1. Temperature Sensor Characteristics

- **Location**: Always on **channel 0**
- **Naming pattern**: `"<device-name> (°C) "` (note trailing space!)
- **Affected status**: Always `affected="0"` 
- **No datapoints**: Temperature sensor has NO KNX datapoint addresses in LXP
- **Read-only**: Temperature is measured directly by the ION device
- **Device types**:
  - ION4: `appId="1044"` (4 touch buttons + temperature)
  - ION8: `appId="1048"` (8 touch buttons + temperature)

### 2. Why They're Hidden

The current code skips these sensors for two reasons:

1. **Parser skip**: `lxp_parser.py` lines 217-219:
   ```python
   if not affected and not (self.include_unaffected or force_include_unaffected):
       return None
   ```
   
2. **No datapoints**: Even if parsed, the sensor has no KNX datapoint addresses to read from

### 3. How Temperature is Accessed

ION devices expose their temperature via **KNX object** that is NOT listed in the LXP datapoints. The temperature must be read using:

- **KNX Read Request** to the device's internal temperature object
- Likely uses a specific DPT (probably DPT 9.001 for temperature in °C)
- The exact KNX group address is **not documented in LXP** and must be discovered

## Solution Strategy

To enable ION temperature sensors, we need to:

### Option 1: Discover KNX Temperature Object (Recommended)

1. Use KNX bus monitoring to discover temperature telegrams
2. Map the discovered address to ION device serial numbers
3. Create sensor entities with the discovered addresses

### Option 2: Use Device Registry Lookup

1. Query ION device directly via KNX for temperature
2. Use device address + specific object index (needs ION documentation)

### Option 3: Manual Override Configuration

Allow users to manually specify ION temperature addresses in `overrides.yaml`:

```yaml
sensors:
  - name: "iON4-3 Raumtemperatur"
    role: "Temperature"
    address: "9/0/7"  # Example - needs discovery
    device_name: "iON4-3"
    device_id: "ion4_3_temp"
```

## Implementation Tasks

1. **Discovery Tool**: Create script to monitor KNX bus and identify ION temperature telegrams
2. **Parser Enhancement**: Force-include ION channel-0 sensors similar to Wetterstation
3. **Address Mapping**: Build mapping from ION device address to temperature object address
4. **Entity Creation**: Create temperature sensor entities for ION devices
5. **Documentation**: Document how to find ION temperature addresses

## Test Cases Needed

1. Parse ION4 device with channel-0 temperature sensor
2. Parse ION8 device with channel-0 temperature sensor  
3. Create temperature sensor entity for ION device
4. Read temperature value via KNX
5. Update HA sensor state when temperature changes

## Related Files

- `custom_components/luxor_living/lxp_parser.py` - Parser logic
- `custom_components/luxor_living/entity_mapper.py` - Entity creation
- `docs/Familie Schmidt_0.9.lxp` - Reference LXP with ION devices

## Notes

- ION temperature sensor name always ends with `" (°C) "` (with spaces)
- Temperature calibration offset stored in `abgleichwert` parameter
- ION8 has additional RTR (room temperature regulator) parameters
- Some ION button channels also have `affected="0"` (unused buttons)

---

**Last Updated**: 2025-12-25  
**Analyzed By**: agent_architect  
**Source**: Familie Schmidt_0.9.lxp
