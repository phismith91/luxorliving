# Release Notes — v1.1.10

## Fixed

- **R718 climate entities missing (regression since v1.1.7)**: The v1.1.7
  global dedup set `_claimed_climate_istwert_addresses` caused H6 actuator
  channels to claim all Istwert addresses first, preventing standalone RTR 718
  thermostats from creating their climate entities. Fixed by replacing the
  global set with per-device tracking `_h6_claimed_zones: set[tuple[str, int]]`
  so within-H6 deduplication is preserved while R718 sensors are no longer
  blocked. Users with R718 thermostats will see the correct number of climate
  entities after updating (e.g. 13 R718 devices → 13 climate entities restored).

- **KNX gateway loses bus access after ~24 h**: Added an xknx connection-state
  callback (`_on_connection_state_changed`) that fires on transport disconnects
  and schedules `_async_on_reconnect()` to re-authenticate against the IP1 REST
  API and re-enable KNX tunneling after xknx restores the transport layer
  automatically. Also extended the REST session timeout from 3600 s (1 h) to
  84600 s (23.5 h) so the session does not expire before the IP1's hard 24 h
  firmware limit. Entities now report unavailable while disconnected and recover
  automatically on reconnect.

## Changed

- **Test coverage for reconnect handler**: 9 new tests cover all branches of
  `_on_connection_state_changed` and `_async_on_reconnect` (DISCONNECTED,
  CONNECTING, CONNECTED states; success and failure reconnect paths; simulation
  mode and missing REST client guards). Test count: 771 → 783.
