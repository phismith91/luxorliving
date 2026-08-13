# Release Notes — v1.2.2

Pre-release (`v1.2.2-rc.2`). Full detail per change in [CHANGELOG.md](../../CHANGELOG.md#122---2026-08-02).

## Fixed

- **Cover tilt position inverted (#197)**: KNX `Lamelle%` follows the same
  0=open/100=closed convention as `Höhe%` (fixed for main position in
  v1.1.6), but tilt read/write and the open/close-tilt commands passed
  values straight through. A closed blind reported
  `current_tilt_position: 100` instead of `0`, and "open tilt"/"close tilt"
  sent the opposite KNX value from what they meant. All four tilt paths
  now apply the same `100 - x` inversion as position.
- **Zombie-tunnel recovery could permanently kill all self-healing (#201,
  rc.2)**: confirmed on two independent field logs (2026-08-10,
  2026-08-12) — several successful zombie recoveries every ~5min, then one
  reconnect attempt hit `E_NO_MORE_CONNECTIONS` (the just-abandoned
  tunnel's IP1 slot not freed in time), after which the integration went
  completely silent — no further zombie/refresh log lines, just
  "not connected" errors until a physical bus restart. Root cause: the
  watchdog and session-refresh loops are only restarted inside a
  *successful* reconnect, so one failed attempt left nothing running to
  ever retry. A failed recovery now schedules a retry every 60s until it
  reconnects.
