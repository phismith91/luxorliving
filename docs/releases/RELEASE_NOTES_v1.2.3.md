# Release Notes — v1.2.3

Stable release, 2026-11-25. Promoted from v1.2.3-rc.2 without code changes; the rc.1/rc.2 pre-releases are superseded. Full detail per change in
[CHANGELOG.md](../../CHANGELOG.md#123---2026-11-25).

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

- **Entities stayed unavailable for hours after a proactive session refresh
  (#247)**: if the gateway reported a second disconnect right after the
  4-hourly session refresh, the reconnect was recognised but the integration
  never marked itself connected again. All entities stayed `unavailable` until
  the next refresh, which could hit the same race. Reported by @Kohbach.

## Please test

- After a Home Assistant restart, lights that were on must stay on.
- A dimmer switched off and on again returns to its previous level.
- If lights still switch off at restart, please send a debug log covering the
  restart (`custom_components.luxor_living: debug`).
- Entities must not stay `unavailable` after the 4-hourly
  `Proactive session refresh` log line. If they do, please send a debug log
  covering one refresh.
