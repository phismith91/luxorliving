# Release Notes — v1.1.5

## Fixed

- **Heating entities never created**: RTR thermostats (`activateRTR=1` parameter, e.g. iON touch
  panels) and heating actuators (`heizungsart` parameter, e.g. H6 valves, infrared heaters) were
  silently ignored by the entity mapper and never appeared as climate entities in Home Assistant.
  Both device types are now correctly mapped to `Platform.CLIMATE`.

- **Deduplication**: When an RTR sensor and a heating actuator share the same KNX group address
  (`Istwert`), only one climate entity is created. The RTR sensor takes precedence as it represents
  the user-facing thermostat.

- **`status@Sollwert` setpoint feedback**: `_target_dp_key` in `climate.py` now recognises
  `status@Sollwert` (RTR sensor variant) in addition to `StatusSollwert` (actuator variant),
  ensuring the correct setpoint feedback address is used for KNX listeners and initial reads.

- **Lingering asyncio task in test**: `test_memory_leak_prevention` now cancels the pending debounce
  task after the assertion, preventing "lingering task" errors in strict asyncio environments
  (Python 3.14+).
