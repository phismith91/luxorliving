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
