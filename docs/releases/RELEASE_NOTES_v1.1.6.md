# Release Notes — v1.1.6

## Fixed

- **Cover position inverted**: KNX `Höhe%` / `StatusHöhe%` uses 0 = fully open, 100 = fully
  closed. Home Assistant uses the opposite convention (0 = closed, 100 = open). Position values are
  now correctly inverted on both read and write. Affects all J4/J8 actuators (Einliegerwohnung,
  Hauptwohnung, and any other LXP file with covers).

- **BWM / BI motion sensors — status always unknown**: Motion sensors (BWM, BI180, BI360) now
  register a KNX listener in `async_added_to_hass` and trigger an initial read of the status
  address on startup. State is no longer stuck at "unknown" after the first gateway connection.

- **Wetterstation rain sensor missing**: The `Regen` role is now mapped as a `binary_sensor`
  (entity type `regen`), making the weather station's rain detection visible in Home Assistant.

- **H6 heating actuator and RTR thermostat not detected as climate entities**: A regression caused
  H6 actuators (`heizungsart` parameter) and RTR thermostats (`activateRTR=1`) to be silently
  skipped during entity mapping. Both are now correctly mapped to `climate` entities with current
  temperature, setpoint control, and live KNX state updates. Duplicate climate entities (when RTR
  and H6 share an Istwert address) are also prevented.
