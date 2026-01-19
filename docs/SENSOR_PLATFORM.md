# Sensor Platform Documentation

## Overview

The Sensor platform in LUXORliving provides automatic detection and integration
of float/string-based sensor values from KNX devices.

**Supported sensor types:**

- Temperature (°C)
- Humidity (%)
- Pressure (hPa)
- CO2 (ppm)
- Brightness/Illuminance (lux)
- Wind Speed (m/s)
- Rain Volume (mm)
- Air Quality (ppm)

## Automatic Entity Generation

Sensors are automatically detected from your LXP project file based on their
configured **role** in LUXORliving.

### Supported Roles

| Role          | Unit | Device Class  | Example                    |
| ------------- | ---- | ------------- | -------------------------- |
| `Temperature` | °C   | temperature   | iON4 Sensor, Wetterstation |
| `Humidity`    | %    | humidity      | Wetterstation              |
| `Pressure`    | hPa  | pressure      | Wetterstation              |
| `CO2`         | ppm  | None          | CO2 Sensor                 |
| `Brightness`  | lux  | illuminance   | Light Sensor               |
| `WindSpeed`   | m/s  | None          | Wetterstation              |
| `RainVolume`  | mm   | precipitation | Wetterstation              |
| `AirQuality`  | ppm  | None          | Air Quality Sensor         |

### Detection Logic

The EntityMapper uses the following priority:

1. **Sensor Types First**: Check if any datapoint has a sensor role
   (Temperature, Humidity, etc.)
   - If found → Create Sensor platform entity with proper unit and device class

2. **Binary Control**: Check for binary control signals (OnOff, MasterSlave)
   - If found → Create Binary Sensor or Switch entity

3. **Skip**: No mappable roles found

```python
# Example: How EntityMapper detects sensor types
datapoints = {
    "Temperature": "1/2/3",  # This role triggers Platform.SENSOR
}
# Result: LuxorLivingSensor created with °C unit
```

## Entity Attributes

Each sensor entity includes:

- **native_unit_of_measurement**: Automatically set based on role (°C, %, etc.)
- **device_class**: Set according to Home Assistant standards (temperature,
  humidity, etc.)
- **unique_id**: Based on KNX address (guaranteed unique)
- **device_info**: Organized under source device (Wetterstation, iON4-1, etc.)

## State Updates

### Initial State Reading

When a sensor entity is added to Home Assistant:

```python
await self._async_read_state()
# Calls: await knx_gateway.async_read_group_value(datapoint_address)
# Updates: self._attr_native_value
```

### Real-time Updates

KNX telegram listeners are registered for each sensor:

```python
self._knx_gateway.register_telegram_listener(
    datapoint_address,
    self._on_telegram  # Callback when value changes
)
```

**Performance:**

- Initial state read: ~30ms per sensor (BAOS cache)
- Live updates: <1 second (KNX telegram → Home Assistant)

## Example: Wetterstation Integration

If your LXP file contains a Wetterstation device with these sensors:

```xml
<Sensor Name="Außentemperatur" ...>
  <Datapoint Role="Temperature" Address="5/1/0" />
</Sensor>
<Sensor Name="Luftfeuchte" ...>
  <Datapoint Role="Humidity" Address="5/1/1" />
</Sensor>
<Sensor Name="Luftdruck" ...>
  <Datapoint Role="Pressure" Address="5/1/2" />
</Sensor>
```

LUXORliving automatically creates:

1. **Sensor: Außentemperatur**
   - Platform: sensor
   - Unit: °C
   - Device class: temperature
   - Value: Updated from KNX address 5/1/0

2. **Sensor: Luftfeuchte**
   - Platform: sensor
   - Unit: %
   - Device class: humidity
   - Value: Updated from KNX address 5/1/1

3. **Sensor: Luftdruck**
   - Platform: sensor
   - Unit: hPa
   - Device class: pressure
   - Value: Updated from KNX address 5/1/2

All organized under **Device: Wetterstation 1**

## Example: iON4/iON8 Temperature Sensors

iON4 and iON8 modules often include temperature sensors:

```xml
<Sensor Name="Temperatur Wohnzimmer" Role="Temperature" ...>
  <Datapoint Role="Temperature" Address="2/1/0" />
</Sensor>
```

Creates:

- **Sensor: Temperatur Wohnzimmer**
  - Under device: iON4-1 or iON8-3
  - Unit: °C
  - Value: Real-time from KNX

## Home Assistant Integration

### Automations

Use sensor values in automations:

```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.aussentemperatur
    above: 25
action:
  - service: light.turn_off
    entity_id: light.living_room
```

### Templates

Reference in template sensors:

```yaml
template:
  - sensor:
      - name: "Temperatur Celsius"
        unique_id: temp_celsius
        unit_of_measurement: "°C"
        state: "{{ (states('sensor.aussentemperatur') | float(0)) }}"
```

### Climate Integration

Combine with climate entities for thermostat control (v0.4.0+):

```python
# Current: Sensor platform (v0.3.1+)
sensor.aussentemperatur  # Outside temperature

# Future: Climate platform (v0.4.0)
climate.wohnzimmer  # Thermostat with setpoint control
```

## Troubleshooting

### Sensor Not Created

**Possible causes:**

1. **Role not recognized**: Check LXP file for correct role name
   (case-sensitive)
   - ✅ Correct: `Role="Temperature"`
   - ❌ Wrong: `Role="temperature"` or `Role="Temp"`

2. **Datapoint missing**: Ensure sensor has at least one datapoint

   ```xml
   <Sensor Name="...">
     <Datapoint Role="Temperature" Address="..." />  <!-- Required -->
   </Sensor>
   ```

3. **Address format**: Validate group address format (M/L/G or decimal)
   - ✅ Correct: `1/2/3` or `2563`
   - ❌ Wrong: `1.2.3`

### Overrides (Fallback, wenn LuxorPlug keine Rollen/Wirksamkeit setzt)

Wenn LuxorPlug die Sensor-Rollen nicht exportiert (oder `affected="0"` bleibt),
kannst du die Sensor-Erzeugung über eine Override-Datei erzwingen:

Hinweis zu `include_unaffected`:

- Bedeutung: Der Parser nimmt auch Elemente mit `affected="0"` auf
  (normalerweise werden diese ausgelassen).
- Wetterstation: Geräte mit Namen wie „Wetterstation“ werden jetzt automatisch
  berücksichtigt – auch wenn `affected="0"` ist. Du brauchst
  `include_unaffected` hierfür nicht.
- Nutzung: Für andere Spezialfälle weiterhin hilfreich (z. B. wenn ein Sensor
  bewusst auf „nicht wirksam“ steht, aber dennoch aus KNX gelesen werden soll).

- Datei im Home Assistant Config-Verzeichnis anlegen:
  `luxor_living_overrides.yaml` (oder `.json`)
- Beispiel YAML:

```yaml
include_unaffected: true  # optional: Parser nimmt auch affected=0 auf
map_onoff_to_binary: true # optional: OnOff-Kontakte als binary_sensor

sensors:
   - name: "Außentemperatur"
      device_name: "Wetterstation 1"
      device_id: "wetterstation_1"
      role: Temperature
      address: "5/1/0"    # M/L/G oder dezimal
   - name: "Luftfeuchte"
      device_name: "Wetterstation 1"
      device_id: "wetterstation_1"
      role: Humidity
      address: "5/1/1"
```

Die Integration lädt die Datei automatisch und legt entsprechende
Sensor-Entities an – auch wenn die LXP-Datei diese nicht als „wirksam“
exportiert.

### State Not Updating

1. **KNX connection**: Verify tunneling/routing is active

   ```bash
   # Check Home Assistant logs
   tail -f ~/.homeassistant/home-assistant.log | grep luxor_living
   ```

2. **Telegram listener**: Confirm address matches in logs

   ```
   Registered telegram listener for address: 1/2/3
   Received telegram for sensor: 22.5
   ```

3. **Device address**: Ensure device is responding on KNX network

## Performance Notes

- **Sensor creation**: ~50ms per sensor entity
- **Initial state read**: ~30ms per sensor (BAOS cache aggregated)
- **Live update latency**: <1 second (KNX telegram delivery)
- **Memory per sensor**: ~5KB per entity

**Scale test results:**

- 10 sensors: <500ms startup
- 30 sensors: <1.5s startup
- 100 sensors: <5s startup

## Future Enhancements

**Planned for v0.4.0+:**

- Climate platform for temperature setpoint control
- Historical sensor data (if enabled in Home Assistant)
- Custom unit overrides in integration UI
- CO2/Air Quality threshold alerts

## Testing

All sensor platform functionality is covered by unit tests:

```bash
pytest tests/test_sensor.py -v

# Results: 11/11 tests passing
# - Entity initialization
# - KNX state reading
# - Telegram updates
# - Error handling
```

## Code Examples

### Reading Sensor State

```python
from homeassistant.components.sensor import SensorEntity

class LuxorLivingSensor(LuxorLivingEntity, SensorEntity):
    """Sensor entity with KNX integration."""

    async def async_added_to_hass(self) -> None:
        # Read initial value from KNX
        value = await self._knx_gateway.async_read_group_value("1/2/3")
        self._attr_native_value = value
        self.async_write_ha_state()
```

### Registering Telegram Listener

```python
def _on_telegram(self, value: Any) -> None:
    """Handle incoming KNX telegram."""
    self._attr_native_value = value
    self.async_write_ha_state()

# Register on init
self._knx_gateway.register_telegram_listener(
    address="1/2/3",
    callback=self._on_telegram
)
```

## Related Documentation

- [KNX Implementation](KNX_IMPLEMENTATION.md) - Protocol details
- [Installation](INSTALLATION.md) - Setup guide
- [Entity Mapper](../custom_components/luxor_living/entity_mapper.py) - Entity
  detection logic
