# Release Notes — v1.2.3

Pre-release (rc.1), 2026-11-06. Full detail per change in
[CHANGELOG.md](../../CHANGELOG.md#123---2026-11-06).

## Fixed

- **Home Assistant restart switched lights off (#217)**: a push-button sensor
  mapped onto the central-off / panic group addresses got an initial read at
  startup. Every actuator answered with `0` and then reported all lights as
  off. The integration now never reads central-function addresses or command
  addresses shared by several actuators. Status addresses are unaffected.
- **Dimmers came back at 100 % after being switched off and on (#237)**: the
  last non-zero brightness is now restored. With no known level the dimmer is
  switched via `OnOff`, so the actuator applies its own switch-on value.
  Contributed by @Kohbach.

## Please test

- After a Home Assistant restart, lights that were on must stay on.
- A dimmer switched off and on again returns to its previous level.
- If lights still switch off at restart, please send a debug log covering the
  restart (`custom_components.luxor_living: debug`).
