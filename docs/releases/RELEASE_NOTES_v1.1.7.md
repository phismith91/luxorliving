# Release Notes — v1.1.7

## Added

- **Theben RTR 718 thermostat support**: The RTR 718 is a standalone room thermostat device
  (distinct from iON panel RTR channels with `activateRTR=1`). It is now automatically detected
  and mapped to a `climate` entity via its three characteristic datapoints (`Istwert`, `Sollwert`,
  `status@Sollwert`). The optional `UmschaltenHeitzenKühlen` datapoint (heating/cooling mode
  switch) is passed through to the entity for future use. Duplicate prevention applies: if an
  H6 actuator shares the same `Istwert` address, the R718 takes precedence.
