# ION Temperature Sensor Discovery Guide

## Problem

ION4/ION-8 devices have built-in temperature sensors that are **not visible in Home Assistant** because:
- The LXP file marks them as `affected="0"` (hidden)
- No KNX datapoint addresses are listed in the LXP
- We need to discover the actual KNX addresses used by ION devices

## Solution: KNX Bus Monitoring

We've created a monitoring script that listens to ALL KNX telegrams and filters temperature-related messages.

## Step-by-Step Instructions

### 1. Prepare Your System

Make sure your Home Assistant integration is **NOT running** (to avoid conflicts):

```bash
# Stop Home Assistant or disable the LUXORliving integration temporarily
```

### 2. Run the KNX Monitor

```bash
cd /home/phil/gitlab_github/luxorliving

# Activate virtual environment
source venv/bin/activate

# Run monitor for 5 minutes (300 seconds)
python scripts/monitor_knx_telegrams.py \
    --host 192.168.1.3 \
    --port 3671 \
    --username admin \
    --password <YOUR_PASSWORD> \
    --duration 300
```

**Parameters:**
- `--host`: Your LUXORliving IP1 gateway IP address
- `--port`: KNX port (usually 3671)
- `--username`: REST API username (from config)
- `--password`: REST API password (from config)
- `--duration`: How long to monitor in seconds (default: 300 = 5 minutes)

### 3. Trigger Temperature Updates

While the monitor is running, trigger ION devices to send temperature:

**Option A: Touch ION Display**
- Touch the ION device screen to wake it up
- Navigate through menus to force temperature display
- The device should send temperature updates to KNX bus

**Option B: Wait for Periodic Updates**
- Some ION devices send temperature periodically
- Wait 5-10 minutes for automatic updates

**Option C: Use LUXORliving App**
- Open LUXORliving mobile app
- View ION device temperature
- This might trigger KNX telegrams

### 4. Check Results

The script saves results to `knx_monitor_output/`:

```bash
ls -la knx_monitor_output/

# View temperature telegrams found
cat knx_monitor_output/temperature_telegrams_*.txt
```

**Expected Output:**

```
================================================================================
ION TEMPERATURE SENSOR DISCOVERY RESULTS
================================================================================

Monitoring session: 20251225_205530
Total telegrams: 1247
Temperature telegrams: 8

================================================================================
TEMPERATURE TELEGRAMS (DPT 9.001)
================================================================================

Time:        2025-12-25T20:56:12
Source:      9.0.7
Destination: 5/1/10
Temperature: 22.3°C
Direction:   RESPONSE
Raw Value:   DPTArray((5, 223))
--------------------------------------------------------------------------------

Time:        2025-12-25T20:56:42
Source:      9.0.8
Destination: 5/1/11
Temperature: 21.8°C
Direction:   RESPONSE
Raw Value:   DPTArray((5, 218))
--------------------------------------------------------------------------------

================================================================================
GROUPED BY SOURCE ADDRESS (ION Devices)
================================================================================

Source: 9.0.7 (2 telegrams)
  → 5/1/10: 22.3°C at 2025-12-25T20:56:12
  → 5/1/10: 22.4°C at 2025-12-25T20:58:45

Source: 9.0.8 (2 telegrams)
  → 5/1/11: 21.8°C at 2025-12-25T20:56:42
  → 5/1/11: 21.9°C at 2025-12-25T20:59:15
```

### 5. Map ION Devices to Addresses

Cross-reference with your LXP file:

```bash
# Find ION device addresses in LXP
grep -B 2 'name="iON' docs/Familie\ Schmidt_0.9.lxp | grep address=

# Example output:
# address="9.0.7"  → iON4-3
# address="9.0.8"  → iON4-2
# address="9.0.10" → iON4-7
```

**Create mapping table:**

| Device Name | Physical Address | Temperature Group Address |
|-------------|------------------|---------------------------|
| iON4-3      | 9.0.7            | 5/1/10                    |
| iON4-2      | 9.0.8            | 5/1/11                    |
| iON4-7      | 9.0.10           | 5/1/12                    |

### 6. Configure Overrides

Add discovered addresses to `overrides.yaml`:

```yaml
sensors:
  - name: "iON4-3 Raumtemperatur"
    role: "Temperature"
    address: "5/1/10"
    device_name: "iON4-3"
    device_id: "ion4_3"
    
  - name: "iON4-2 Raumtemperatur"
    role: "Temperature"
    address: "5/1/11"
    device_name: "iON4-2"
    device_id: "ion4_2"
    
  - name: "iON4-7 Raumtemperatur"
    role: "Temperature"
    address: "5/1/12"
    device_name: "iON4-7"
    device_id: "ion4_7"
```

### 7. Restart Home Assistant

After adding overrides, restart HA to see the new temperature sensors!

## Troubleshooting

### No Temperature Telegrams Found

**Problem:** `Temperature telegrams: 0`

**Solutions:**
1. **Increase monitoring duration:**
   ```bash
   python scripts/monitor_knx_telegrams.py ... --duration 600  # 10 minutes
   ```

2. **Force ION updates:**
   - Touch ION screen multiple times
   - Change temperature setpoint via LUXORliving app
   - Physically change room temperature (open window)

3. **Check ION configuration:**
   - Verify temperature sensor is enabled in LUXORplug
   - Check if ION firmware supports temperature broadcasts

### Connection Failed

**Problem:** `Authentication failed` or `Failed to enable tunneling`

**Solutions:**
1. Check credentials match Home Assistant config
2. Ensure no other KNX connection is active (stop HA first)
3. Verify IP1 gateway is reachable: `ping 192.168.1.3`
4. Check REST API is enabled on IP1

### Wrong Temperature Values

**Problem:** Temperature values look wrong (e.g., 327.6°C)

This means the value is NOT a temperature (DPT 9.001). The script filters reasonable temps (-50°C to 100°C).

### ION Addresses Don't Match

**Problem:** Monitor shows addresses like `9.0.3` but LXP shows `9.0.7`

Check:
1. LXP file is up-to-date
2. ION device physical address hasn't changed
3. You're looking at the right device in LXP

## Advanced: Manual KNX Group Address Test

If you know/guess an address, test it directly:

```python
# In Home Assistant Developer Tools → Template
{{ state_attr('sensor.ion4_3_temperature', 'group_address') }}

# Or use KNX integration to read:
# Services → KNX: read
# Address: 5/1/10
```

## Next Steps

Once you have the addresses:
1. **Document them** in `docs/ION_ADDRESSES.md`
2. **Add to overrides.yaml**
3. **Create GitHub issue** with findings to improve auto-detection
4. Consider creating a PR to auto-discover ION temperatures

## Files

- **Monitor Script**: `scripts/monitor_knx_telegrams.py`
- **Output Directory**: `knx_monitor_output/`
- **Analysis Doc**: `docs/ION_TEMPERATURE_SENSOR_ANALYSIS.md`
- **This Guide**: `docs/ION_TEMPERATURE_DISCOVERY_GUIDE.md`
