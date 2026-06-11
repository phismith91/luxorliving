# Release Notes — v1.1.14

## Fixed

- **H6 multi-channel unique_id collision (issue #141)**: All channels of a
  Theben H6 climate actuator shared the same `unique_id` when the
  `UmschaltenHeitzenKühlen` datapoint (10247) appeared first in the LXP file's
  datapoint map — the mapper used `list(datapoints.values())[0]` as the fallback
  id, so every channel resolved to the same address. Home Assistant silently
  dropped all but the first entity. A new post-processing pass
  (`EntityMapper._deduplicate_unique_ids()`) detects same-platform collisions and
  appends a `_ch{n}` suffix to duplicates. The first claimant retains its original
  id so existing HA registry entries survive the upgrade.

- **KNX reconnect watchdog — proactive REST refresh after repeated disconnects**:
  When xknx cannot re-establish the KNX/IP tunnel (5 `DISCONNECTED` events in
  60 s without a successful `CONNECTED`), the integration now immediately triggers
  a forced REST logout+login+enable_tunneling cycle. Previously, the gateway could
  stay offline for up to 4 h until the periodic session-refresh timer fired. Root
  cause: after an IP1 restart the KNX/IP tunneling slot stays occupied; a REST
  cycle clears it and lets xknx reconnect.

- **Logout-feedback-loop guard**: `_async_on_reconnect` now skips re-auth if a
  REST refresh completed less than 30 s ago (`RECONNECT_COOLDOWN_SECS`). Without
  this guard, `logout()` triggered a `DisconnectRequest` from the IP1, xknx
  reconnected, `CONNECTED` fired `_async_on_reconnect` which called `logout`
  again — cycling ~3× before the session lock stopped it. The guard breaks the
  loop on the first iteration.

- **Rate-limited "Cannot read - not connected" log**: This error message is now
  logged at `ERROR` level at most once per 60 s; subsequent calls within the
  window use `DEBUG`. During a 3.5 h outage the message appeared 44,820 times
  and flooded the HA log, masking the real reconnect failure.

## Added

- Regression test suite for Kennel LXP project file: verifies 26 climate
  entities (H6 and R718 channels), correct per-device counts, and no
  same-platform `unique_id` collisions across all 5 entity platforms.
- 10 new unit tests for the three KNX hardening fixes (watchdog, timestamp
  guard, rate-limited log).

## Tests

16 new tests covering the H6 uid collision fix and the three KNX hardening
fixes. Test count: 992 → 1008.
