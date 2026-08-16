# Release Notes — v1.2.2

Pre-release (`v1.2.2-rc.4`). Full detail per change in [CHANGELOG.md](../../CHANGELOG.md#122---2026-08-02).

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
- **Teardown leaked live xknx instances occupying every IP1 tunnel slot
  (#201, rc.4)**: on rc.3, Marcus' 2026-08-14 logs showed the retry loop
  running (42 attempts) but every attempt dying with
  `E_NO_MORE_CONNECTIONS`, while 8 tunnel source addresses flooded the bus
  for hours — even LuxorPlay couldn't steer. Root cause: the 15s
  stop-timeout path "abandoned" xknx instances alive (heartbeat,
  auto-reconnect, transport all still running), each holding an IP1 tunnel
  slot forever; and the stop-timeout itself was caused by the teardown
  drain missing xknx's *internal* outgoing queue, where the ~1600-telegram
  poll backlog had migrated. Fixed: both queues drained at teardown, and a
  stop-timeout now force-closes the tunnel interface (releasing the IP1
  slot) instead of abandoning it.
- **Backpressure for entity polling (#201, rc.4)**: reads are skipped while
  50+ telegrams are already queued outgoing, so a zombie window can no
  longer build the doomed backlog in the first place.
- **Better field-log diagnostics (#201, rc.4)**: outgoing-queue depth in the
  zombie-detection WARNING, retry attempt numbers, dropped-telegram counts
  at teardown, and repeated identical connect failures log their traceback
  only once.
