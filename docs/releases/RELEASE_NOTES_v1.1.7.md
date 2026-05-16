# Release Notes — v1.1.7

## Added

- **Theben RTR 718 thermostat support**: The RTR 718 is a standalone room thermostat device
  (distinct from iON panel RTR channels with `activateRTR=1`). It is now automatically detected
  and mapped to a `climate` entity via its three characteristic datapoints (`Istwert`, `Sollwert`,
  `status@Sollwert`). The optional `UmschaltenHeitzenKühlen` datapoint (heating/cooling mode
  switch) is passed through to the entity for future use. Duplicate prevention applies: if an
  H6 actuator shares the same `Istwert` address, the R718 takes precedence.

## Fixed

- **B6 binary input channels mapped as `switch` instead of `binary_sensor`**: All sensor
  channels (B6, T-series, and any other input device) now correctly map to `binary_sensor`
  regardless of whether both `OnOff` and `status@OnOff` datapoints are present. Previously,
  a channel reporting both roles was incorrectly treated as a controllable switch.

  **Migration note:** If you had B6 entities appearing as `switch.*` in v1.1.6, they will
  be recreated as `binary_sensor.*` entities after updating. Please update any automations,
  scripts, or dashboards that referenced the old entity IDs.
