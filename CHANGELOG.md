# Changelog

All notable changes to the LUXORliving Home Assistant integration will be
documented in this file.

## [1.2.1] - 2026-07-12

Pre-release (`v1.2.1-rc.5`).

### Added

- **H6 cooling-mode support**: H6 climate entities now support cooling in addition to heating when the `UmschaltenHeitzenKühlen` (heating/cooling mode-switch) datapoint is present. Marcus' setup with ION8 T10 mode-switch controlling H6 devices (511, 512, 513) is fully supported. Mode-switch control sends binary telegram: 1 for heating, 0 for cooling.

### Fixed

- **IP1 tunneling slot exhaustion**: Unclean HA shutdowns left stale tunneling slots on the IP1 (up to 4 slots, then lockup). `enable_tunneling()` now calls `disable_tunneling()` first to flush any orphaned sessions from previous crashed HA instances. Diagnostics added: log prints connected client count and slot saturation state on startup.
- **Mid-uptime slot exhaustion (rc.4)**: The startup flush above only ran once per HA restart. Orphaned slots from other clients (a crashed prior instance, LuxorPlay) can still accumulate during a single long uptime and freeze the bus after ~24-72h without HA ever seeing a disconnect — confirmed on Marcus' 2026-06-30 log (~30h uptime, continuous `L_DATA_CON` confirmation timeouts, no disconnect logged, required a physical KNX restart). The existing 4h proactive `_session_refresh_loop` now also calls `disable_tunneling()` before re-login, so it actually clears device-wide orphaned slots instead of only cycling its own session. Slot-saturation diagnostics now log at WARNING (visible in default HA logs) once slots are at/over capacity, instead of only at DEBUG/INFO which most bug-report logs don't include.
- **Zombie-tunnel watchdog**: The IP1 tunnel can report CONNECTED for hours while every outgoing telegram fails its L_DATA_CON confirmation, with xknx's own heartbeat never detecting a real disconnect (confirmed on a 2026-07-10 log: ~20 confirmation timeouts/min for 9h, unaffected by the existing periodic REST-session flush from #180, which only cycles the REST layer, not the xknx tunnel object). A new watchdog polls xknx's `cemi_count_outgoing_error` counter every 30s and forces a full REST+KNX reconnect if it jumps by 5+ in one window, with a 5-minute cooldown to avoid reconnect storms. Also serializes the recovery cycle against the periodic session refresh and against integration unload, so a reload during an in-flight recovery can't leak a connection or background tasks.
- **Wetterstation "Vorne" sensor mislabeled as "Mitte"**: Theben's own KNX product definition (ComObject 0 "Helligkeitswert vorne", parameter enum "Sensor vorne") has no "Mitte" position — only vorne/links/rechts. The front-facing brightness sensor's display name is now "Helligkeit Vorne" instead of "Helligkeit Mitte". Also escalated the two periodic-refresh success log lines from INFO to WARNING so they're visible in default HA log exports.

## [1.2.0] - 2026-06-18

Pre-release (`v1.2.0-rc.5`). Includes critical fixes for TLS and tunneling. rc.4

### Security

- **Push forwarder no longer downgrades TLS**: `v1.2.0-rc.3` made `PushClient`
  use `async_get_clientsession(hass, verify_ssl=False, ssl_cipher=INSECURE)` —
  but `push_ws_url` is a user-configured forwarder, **not** the IP1. That blanket
  application disabled certificate verification and lowered the cipher security
  level for an arbitrary, possibly internet-facing, token-authenticated endpoint
  (MITM / token-theft risk). `PushClient` now uses HA's standard shared session
  with full TLS verification. The IP1 legacy-TLS posture is confined to the three
  IP1-REST call sites (`knx_gateway`, `config_flow`, `repairs`). Only entries
  with `push_ws_url` configured were affected. Guarded by
  `test_push_client_does_not_downgrade_tls`.

### Fixed (rc.4)

- **Request timeouts on the injected session**: `login`/`logout`/`enable_tunneling`
  now pass an explicit per-request `timeout` (30 s). The owned session set this at
  session level; HA's shared session uses aiohttp's defaults (total 300 s), so the
  explicit timeout restores the intended 30 s ceiling on the injected path.
- **`_async_forced_refresh` error handling**: the fire-and-forget REST-refresh task
  now catches exceptions (like `_async_on_reconnect`) instead of surfacing an
  unhandled task error when a refresh login fails.

### Fixed

- **CRITICAL — IP1 legacy TLS (`@SECLEVEL=0`) restored**: `_make_ssl_context`
  again sets `set_ciphers("DEFAULT:@SECLEVEL=0")`. It had been dropped in
  `v1.1.15-rc.1` (carried into `v1.2.0-rc.2`) with an untested comment claiming
  the gateway works without it — but that posture is identical to the failing
  `v1.2.0-rc.1` shared session, so `v1.2.0-rc.2` was latently affected by the
  same `SSLV3_ALERT_HANDSHAKE_FAILURE` on real hardware. The only field-proven
  posture is `v1.1.14`'s `CERT_NONE` + `@SECLEVEL=0`.

### Added

- **Platinum quality scale — inject websession (done correctly)**: the REST
  client (`BAOSRestClient`) and `PushClient` again accept Home Assistant's shared
  session, now obtained with `async_get_clientsession(hass, verify_ssl=False,
  ssl_cipher=SSLCipherList.INSECURE)`. `SSLCipherList.INSECURE` resolves to
  `"DEFAULT:@SECLEVEL=0"`, so the shared session speaks the IP1's legacy TLS —
  the missing parameter that broke `v1.2.0-rc.1`. Wired through `knx_gateway.py`,
  `config_flow.py`, `repairs.py` and `push_client.py`. The owned-session path is
  kept as a fallback (same `@SECLEVEL=0` context).
- **Regression guards** (`test_inject_ssl_cipher.py`, gated suite): assert
  `_make_ssl_context` sets `@SECLEVEL=0` + `CERT_NONE`, that the string matches
  HA's `SSLCipherList.INSECURE`, and that every injection call site passes
  `verify_ssl=False, ssl_cipher=SSLCipherList.INSECURE`. A live legacy-cipher
  handshake cannot be reproduced in CI's modern OpenSSL, so end-to-end TLS
  remains a manual pre-release check on real hardware.

## [1.2.0] - 2026-06-18

Pre-release (`v1.2.0-rc.2`). Ships the Gold quality-scale item only. The
Platinum websession-injection from `v1.2.0-rc.1` has been **reverted** — it
broke the connection to real IP1 hardware (see below). `v1.1.15-rc.1` remains
published as a fallback.

> ⚠️ Superseded: `v1.2.0-rc.2` is itself affected by the latent `@SECLEVEL=0`
> regression described under \[Unreleased] and must not be promoted. Use
> `v1.2.0-rc.3`.

### Added

- **Gold quality scale — stale-device handling**: implemented
  `async_remove_config_entry_device`. Devices that disappeared from the LXP
  project (no longer mapped by the integration) can now be deleted manually from
  the HA UI, while the gateway hub and active devices remain protected.

### Fixed

- **Log flood / HA rate-limiter**: per-telegram logging in `knx_gateway.py`
  (incoming telegrams, DPT 9.xxx floats, external push) was emitted at INFO and
  fired for every KNX telegram — on a busy bus this produced multi-MB logs and
  tripped Home Assistant's "logging too frequently" limiter. Demoted to DEBUG.
- **Config-flow broken description text**: the `gateway` step's error-redisplay
  paths (`invalid_auth`, `cannot_connect`) did not pass the `project_name`
  description placeholder, producing `MISSING_VALUE`/`MISSING_TRANSLATION` in the
  UI on every failed connection attempt. All re-display paths now pass it.
- **Startup warning spam**: multi-channel devices (e.g. climate controllers with
  several channels under one `device_id`) collide on `unique_id` by design; the
  disambiguation guard logged one WARNING per collision on every startup.
  Per-collision detail moved to DEBUG with a single INFO summary; the
  deterministic `_chN` suffix scheme is unchanged (no entity-id churn).

### Reverted

- **Platinum quality scale — inject websession (regression fix)**: `v1.2.0-rc.1`
  routed the REST client and `PushClient` through Home Assistant's shared
  `async_get_clientsession(hass, verify_ssl=False)`. On real IP1 hardware this
  caused `SSLV3_ALERT_HANDSHAKE_FAILURE`: the shared session bypassed the
  client's custom `ssl_context`, so the `@SECLEVEL=0` cipher policy required to
  talk to the IP1's legacy TLS was never applied (`verify_ssl=False` only
  disables certificate verification, not the OpenSSL security level). The REST
  client (`BAOSRestClient`) and `PushClient` again create and own their own
  `ClientSession` with the `@SECLEVEL=0` `ssl_context`, identical to the
  known-good `v1.1.14` / `v1.1.15-rc.1` path. The injected-session constructor
  parameter and the two injection tests
  (`test_inject_session_tls_integration.py`, `test_inject_websession.py`) were
  removed — the integration self-signed-TLS test used a modern cipher and so
  never reproduced the IP1's `SECLEVEL` failure, giving false confidence.
  Platinum websession injection is incompatible with the IP1's TLS stack and is
  dropped, not deferred.

## [1.1.15] - 2026-06-13

Pre-release (`v1.1.15-rc.1`). Bundles the post-1.1.14 security, entity, and hygiene fixes plus a
fully green gated test suite. Two quality-scale items (Gold stale-device
handling via `async_remove_config_entry_device`, Platinum websession injection)
are deferred to separate branches.

### Security

- **Diagnostics token leak**: `push_token` / `push_ws_token` were emitted
  verbatim in `entry.options` in both the minimal (no-consent) and full
  diagnostics payloads. Now redacted to `**REDACTED**` via `_redact_options()`.
- **Diagnostics read stale state**: since the v1.1.12 `runtime_data` refactor,
  diagnostics still read the old (always-empty in prod) `hass.data[DOMAIN]`
  path. Fixed with a `runtime_data`-first lookup (hass.data fallback for legacy
  tests).
- **TLS `@SECLEVEL=0` removed**: `set_ciphers("DEFAULT:@SECLEVEL=0")` permitted
  null/export cipher suites. The IP1 supports standard TLS 1.2+ suites without
  it. Extracted `_make_ssl_context()` helper.
- **Timing-safe token comparison**: Token and Bearer auth in `push_view.py` used
  `!=` (timing oracle). Replaced with `hmac.compare_digest()`.

### Fixed

- **Dimmer brightness floor**: `int(brightness*100/255)` mapped brightness 1–2
  to `0%` (light off). Now `max(1, round(...))` for any non-zero brightness.
- **Dimmer turn_on guards**: dimmable `turn_on` skipped the
  `_raise_if_unavailable()` + rate-limit that the base/`turn_off` paths enforce.
  Both added.
- **Light listener timing**: both light classes registered KNX listeners in
  `__init__`, which runs in an executor thread, risking off-loop mutation of the
  gateway `_listeners` dict and `async_write_ha_state` firing before
  `async_added_to_hass`. Registration moved to `async_added_to_hass` (mirrors
  `cover.py`).
- **Climate setpoint clobber**: `set_hvac_mode(OFF)` called
  `set_temperature(min_temp)`, overwriting `_attr_target_temperature` so HEAT
  restored 5 °C. The setpoint is now saved and min_temp sent straight to the bus;
  HEAT restores the saved value.
- **Setup retry**: an unreachable gateway returned `False` (no retry). Now raises
  `ConfigEntryNotReady` outside simulation so HA retries.
- **config_flow socket leak**: the routing probe ran a blocking
  `socket.create_connection` on the event loop and never closed the socket. Now
  via `async_add_executor_job` + `sock.close()`.
- **Repair flow never triggered**: `async_create_fix_flow` matched
  `issue_id == "authentication_failed"`, but issues are created as
  `authentication_failed_<entry_id>`. Now `startswith`.
- **Health view re-registered every setup**: guard used `hasattr(dict, ...)`
  (attribute vs key → always False). Now `.get("_health_registered")`, matching
  the push guard.

### Removed

- **Dead `switch` platform**: no LXP role maps to `Platform.SWITCH`
  (`OnOff`/`SchaltenOnOff` → `LIGHT`), so the platform produced zero entities and
  `LuxorLivingSwitch` (~230 lines) was unreachable. Verified against 4 real LXP
  files + the ETS5 product DB. Dropped from `PLATFORMS`.

### Changed

- **Linters now gate CI**: removed `--exit-zero` from bandit (pre-commit +
  Makefile) and `|| true` from flake8/bandit in the Makefile. Both pass cleanly.
- **mutmut config for 3.x**: `tests_dir` kept as a list so mutmut ≥ 3.3.1
  (CI-pinned) collects the smoke selection correctly.

### Tests

- Gated suite (`-m "not enable_socket"`) is now fully green (was 2 failing):
  - `test_full_entity_creation_benchmark` used the pre-refactor
    `hass.data[DOMAIN]` layout and the removed `switch` platform → now sets
    `entry.runtime_data` and drops `switch`.
  - `test_push_client_receives_and_forwards` opened a real aiohttp websocket
    whose shutdown daemon thread trips HA's strict thread-leak guard — same leak
    the `rest_client` socket tests already gate. Added the missing
    `@pytest.mark.enable_socket` marker (reclassification, not removal).

## [1.1.14] - 2026-06-11

### Fixed

- **H6 multi-channel unique_id collision (issue #141 regression)**: All
  channels of a Theben H6 climate actuator shared the same `unique_id` when
  the `UmschaltenHeitzenKühlen` datapoint (10247) appeared first in the LXP
  file's datapoint map. Home Assistant silently dropped all but the first
  entity, leaving 5 of 6 H6 channels invisible. A new post-processing pass in
  `EntityMapper._deduplicate_unique_ids()` detects same-platform collisions and
  appends a `_ch{n}` suffix to duplicates. The first claimant retains its
  original id (existing registry entries survive upgrade).

- **KNX reconnect watchdog — proactive REST refresh after repeated disconnects**:
  When xknx fails to reconnect (5 DISCONNECTED events in 60 s without a
  CONNECTED), the integration now immediately triggers a forced REST
  logout+login+enable_tunneling cycle without waiting up to 4 h for the
  periodic session-refresh timer. This resolves the long outage Marcus reported
  where a spontaneous IP1 disconnect caused a 3.5 h bus-freeze.

- **Logout-feedback-loop guard (timestamp guard)**: `_async_on_reconnect` now
  skips re-auth if a REST refresh completed less than 30 s ago. Without this
  guard, `logout()` caused the IP1 to send a `DisconnectRequest`, xknx
  reconnected, CONNECTED fired, `_async_on_reconnect` called `logout` again —
  cycling 3× before the session lock stopped it.

- **Rate-limited "Cannot read - not connected" log**: The error is now logged
  at ERROR level at most once per 60 s; subsequent calls within the window log
  at DEBUG. During the 3.5 h outage this message appeared 44,820 times and
  flooded the HA log, masking the real reconnect failure.

### Added

- Regression test suite for Kennel LXP file: verifies 26 climate entities (H6
  and R718 channels), correct per-device counts, and no same-platform unique_id
  collisions across all 5 entity platforms.

## [1.1.13] - 2026-06-07

### Security

- **Push endpoint now requires authentication (CVE-style fix)**: The
  `/api/luxor_living/push` endpoint previously defaulted to unauthenticated
  access (`auth_method = none`), allowing any host that could reach the HA HTTP
  port to write arbitrary values to KNX group addresses (lights, covers, etc.).
  The `none` auth option is removed. All requests without valid credentials now
  return `403`. Token and Bearer auth methods additionally reject if no token is
  configured (previously silently accepted all requests).

- **Health view now requires HA authentication**: `/api/luxor_living/health`
  now sets `requires_auth = True` and requires a valid HA long-lived access
  token. Previously exposed topology information (entry IDs, KNX address counts,
  simulation mode, circuit breaker state) without authentication.

### Changed

- Push webhook config: `None` auth option removed from Options Flow. Existing
  installations with `auth_method = none` will have requests rejected until a
  token and auth method are configured under Settings → Integrations →
  LUXORliving → Configure.

## [1.1.12] - 2026-06-03

### Fixed

- **KNX bus freeze after ~47 h — race condition between session refresh and
  reconnect handler (issue #141)**: The `_session_refresh_loop` calls `logout()`
  which causes xknx to detect a disconnect and fire `_async_on_reconnect`
  *concurrently*. Without synchronization both coroutines executed
  `logout → login → enable_tunneling` in parallel, creating 2+ orphaned sessions
  per refresh cycle instead of 1. After ~7 cycles the IP1 session table overflowed
  and the KNX bus froze (L_DATA_CON timeouts on all group addresses, confirmed by
  user log from 2026-06-03).

  Fix: `asyncio.Lock` (`_session_lock`) shared by both coroutines. The reconnect
  handler skips execution immediately if the refresh loop holds the lock; otherwise
  it acquires the lock before any REST session operation. This guarantees only one
  session is active at a time.

- **Session refresh interval reduced 6 h → 4 h** for a wider safety margin against
  IP1 session table saturation.

- **Lingering `_session_refresh_task` in tests**: two gateway tests that called
  `async_setup()` without a matching `async_disconnect()` left a background task
  running, causing pytest-asyncio ≥ 1.3 to raise `Failed: Lingering task after test`.

## [1.1.11] - 2026-05-25

### Fixed

- **KNX bus freeze after 24–72 h uptime (issue #141 — complete fix)**: The
  reactive reconnect handler from v1.1.10 only recovered *after* XKNX detected
  a connection drop. This leaves the "silent freeze" case open: the IP1's
  session/channel table saturates and the bus stops routing telegrams while
  XKNX stays "connected". Two-layer protection now in place:
  - **Proactive** — `_session_refresh_loop` background task wakes every 6 h and
    cycles the REST session (logout → login → enable_tunneling) to flush stale
    table entries before saturation. The 6 h interval is well below the observed
    ~7 h freeze onset.
  - **Reactive** (unchanged from v1.1.10) — `_on_connection_state_changed`
    callback fires when XKNX detects a disconnect and immediately re-authenticates.
- **Blocking file read in event loop** (`overrides.py:55`): `load_overrides()`
  was called directly in the async setup path, triggering HA's
  "Detected blocking call to `open()`" warning. Moved to
  `hass.async_add_executor_job` so the file I/O runs in the executor thread pool.

## [1.1.10] - 2026-05-20

### Fixed

- **R718 climate entities missing when H6 present (issue #141 regression)**: v1.1.7 introduced
  a global Istwert-address set to deduplicate climate entities. Since H6 actuators are processed
  before R718 sensors, the set claimed every shared address and blocked all R718 entities.
  Replaced with per-device H6 tracking (`(device_id, istwert_addr)` key): channels within the
  *same* H6 device sharing one room sensor are still deduplicated correctly, but R718 thermostats
  on separate devices always produce their own climate entity. A setup with 3×H6 + 13×R718 now
  correctly shows 26 climate entities instead of 13.

- **KNX gateway loses bus access after reconnect / ~24 h uptime (issue #141)**: xknx's
  `auto_reconnect=True` restores the KNX/IP transport layer after a connection drop, but
  the IP1's REST tunneling authorisation was never renewed. The gateway accepted the KNX
  connection yet ignored all telegrams. A connection-state callback now fires on every
  xknx state transition:
  - `DISCONNECTED` → log warning, mark gateway unavailable (entities become unavailable in HA)
  - `CONNECTED` (after reconnect) → logout → login → `enable_tunneling` → mark available again
  Session expiry tracking corrected from 1 h to 23.5 h to match the IP1 firmware's actual limit.

---

## [1.1.8] - 2026-05-17

### Added

- **Configuration parameters documented**: README now includes a dedicated section describing all
  config-flow and options-flow parameters (gateway host, credentials, push-token, auth method).
- **Known Limitations section**: README documents SSL certificate constraints, unsupported device
  types, LXP reload behaviour, and other known limitations.
- **Removal instructions**: README documents how to remove the integration from HA and HACS.

### Changed

- **Config flow test coverage expanded**: Added tests for the reauthentication flow
  (`async_step_reauth`, `async_step_reauth_confirm`) and the reconfigure flow
  (`async_step_reconfigure`), covering success paths and error cases. Satisfies HA quality
  scale Bronze rule `config-flow-test-coverage`.

---

## [1.1.7] - 2026-05-16

### Added

- **Theben RTR 718 thermostat support**: The RTR 718 is a standalone room thermostat device
  (distinct from iON panel RTR channels). It is now automatically detected and mapped to a
  `climate` entity via its three characteristic datapoints (`Istwert`, `Sollwert`,
  `status@Sollwert`). The optional `UmschaltenHeitzenKühlen` datapoint (heating/cooling mode
  switch) is passed through to the entity for future use.

### Fixed

- **B6 binary input channels mapped as `switch` instead of `binary_sensor`**: All sensor
  channels (B6, T-series, and any other input device) now correctly map to `binary_sensor`
  regardless of whether both `OnOff` and `status@OnOff` datapoints are present.
  **Migration note:** If you had B6 entities in v1.1.6, they appeared as `switch` entities.
  After this update they become `binary_sensor` entities — update any automations or dashboards
  that referenced the old `switch.*` entity IDs.

- **Wetterstation rain sensor always showing "unknown"**: The KNX listener for the
  `Regen` datapoint was never registered because the `_address_status` lookup did not
  include the `"Regen"` key. Rain sensor state now updates in real time via KNX telegrams.

---

## [1.1.6] - 2026-05-15

### Fixed

- **Cover position inverted**: KNX `Höhe%` / `StatusHöhe%` uses 0 = fully open, 100 = fully closed.
  Home Assistant uses the opposite convention (0 = closed, 100 = open). Position values are now
  correctly inverted on both read (`_handle_position_update`) and write (`async_set_cover_position`).
  Affects all J4/J8 actuators in every LXP file.

- **BWM / BI motion sensors — status always unknown**: Motion sensors (BWM, BI180, BI360) are now
  registered as KNX listeners in `async_added_to_hass`. An initial read of the status address is
  also triggered on startup, so the entity's state is never stuck at "unknown" after the first
  gateway connection.

- **Wetterstation rain sensor missing**: The `Regen` role was explicitly skipped in
  `_map_wetterstation_sensor`. It is now mapped as a `binary_sensor` (entity type `regen`), making
  the weather station's rain detection visible in Home Assistant.

---

## [1.1.4] - 2026-05-04

### Fixed

- Cover and climate entities crash on setup with AttributeError: MappedEntity has no attribute get
  (MappedEntity is a dataclass, not a dict — use attribute access instead)
- KNX listener registration moved to async_added_to_hass (was in __init__ which runs in a
  thread executor, causing thread-safety and lifecycle issues with async_write_ha_state)
- async_will_remove_from_hass cleanup prevents stale listeners and memory leaks on reload
- Temperature DPT encoding: removed incorrect x100/÷100 integer conversion; gateway already
  decodes DPT 9.001 as Python float
- StopStep → StepStop typo in platform_detector.py ROLE_TO_PLATFORM mapping
- device_info: remove non-existent device_model/sw_version fields; use model=LUXORliving

---

## [1.1.3] - 2026-03-23

### Fixed

- Replace incorrect icon with correct custom icon (fixes HACS store display)

---

## [1.1.2] - 2026-03-23

### Fixed

- SECURITY.md: replaced stale 0.4/0.5 supported-versions table with "latest only" policy
- Contact email updated to software@withphil.de
- Automated version-reference check added to CI (scripts/check_version_refs.sh)

---

## [1.1.1] - 2026-03-23

### Fixed

- HACS default store compliance: brand assets moved to `custom_components/luxor_living/brand/icon.png`
- Validate workflow: removed `continue-on-error` bypass, added `push` trigger

---

## [1.1.0] - 2026-03-23

### Added

- Extended test suite: 725 tests covering coordinator, binary sensor, sensor, switch, light, and cover platforms
- Branch coverage raised from 73% to 80%+ (Gold Quality Scale target)

---

## [1.0.0] - 2026-03-22

### Added

- **Gold Quality Scale**: icon translations (`icons.json`), exception translations (`HomeAssistantError` with `translation_key`), zeroconf discovery (`_knxip._udp.local.`), docs use-cases and known-limitations sections
- **Options flow sections**: Standard options (scan interval, log level, simulation mode) and collapsible Push Webhook advanced section via `data_entry_flow.section()`
- **Persona documentation**: `USER_GUIDE.md`, `ADVANCED_GUIDE.md`, `DEVELOPER_GUIDE.md`, `REFERENCE.md` — replaces scattered per-audience docs
- **README hub**: short hub README with 3-step quickstart, persona router, absolute doc links

### Changed

- **Docs overhaul**: archived 15 outdated/duplicate files; all doc links use absolute `/blob/main/` URLs (avoids 404 on old release tags)
- **Translation sync**: `strings.json`, `en.json`, `de.json`, `fr.json` updated for all new options fields and zeroconf confirm step

---

## [0.8.0] - 2026-03-21

### Added

- **Reauth flow**: `async_step_reauth` + `async_step_reauth_confirm` in
  `config_flow.py` — expired credentials trigger HA's native re-authentication
  flow instead of a hard error (Silver compliance)
- **Entity availability**: All entities become unavailable when the KNX gateway
  connection is lost; write actions raise `HomeAssistantError` via
  `_raise_if_unavailable()` (Silver compliance)

### Changed

- **`entry.runtime_data`**: Removed global `_integration_states` registry;
  all platform and push files now use `entry.runtime_data` directly (Bronze
  compliance, HA 2024+ standard)
- **Unique config entry**: `async_set_unique_id(host)` +
  `_abort_if_unique_id_configured()` prevent duplicate entries for the same IP
  (Bronze compliance)
- **`PARALLEL_UPDATES`**: Set on all 6 platform files (`= 1` for write
  platforms, `= 0` for read-only) (Silver compliance)
- **Diagnostic entities**: Health binary sensor and auto-discovered sensors
  marked `EntityCategory.DIAGNOSTIC` and disabled by default (Gold compliance)
- **pre-commit**: Fixed prettier v4.0.0-alpha.8 regression (`pass_filenames:
  false` + `.` target) so commits with only prettierignored files no longer
  fail the hook

---

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.3] - 2026-03-20

### Changed

- **Dependency fix**: `xknx` requirement bumped from `>=2.12.0` to `>=3.13.0` in
  `manifest.json` — previously HACS would install an incompatible version
- **Security**: added `defusedxml>=0.7.1` to `manifest.json` requirements for safe
  XML parsing
- **Code split**: extracted `LuxorLivingHealthView` → `health_view.py` and
  `LuxorLivingPushView` → `push_view.py` out of `__init__.py` (616 → ~250 lines)
- **Asyncio**: replaced all `asyncio.get_event_loop()` calls with
  `asyncio.get_running_loop()` across `light`, `switch`, `binary_sensor`,
  `climate`, `cover`, `sensor`, `rest_client`, `health_view` (deprecation fix for
  Python 3.10+)
- **Error handling**: all 11 bare `except Exception: pass/fallback` blocks now log
  at `DEBUG` level; `push_client.py` narrowed to `json.JSONDecodeError`;
  `override_handler.py` narrowed to `(ValueError, IndexError, TypeError)`
- **Tooling**: `black` pre-commit rev synced to `26.1.0`; `flake8 --exit-zero`
  removed (failures now blocking); docstring codes `D1xx` exempted to avoid
  noise
- **CI/CD**: new `release.yml` workflow (tag-triggered, version gate, CHANGELOG
  extraction, ZIP validation, test gate before publish); new `bump-version.yml`
  workflow (version bump + CHANGELOG promotion via `workflow_dispatch`); `ci-cd.yml`
  simplified to CI-only
- **Scripts**: fixed `deploy_release.sh` manifest path bug and empty release notes;
  fixed `release_automation.sh` to pass `--notes-file` to `gh release create`;
  `benchmark.py` moved from integration source to `scripts/`

### Fixed

- `deploy_release.sh` read version from `ROOT/manifest.json` (file does not exist)
  instead of `custom_components/luxor_living/manifest.json` — would always exit
  with code 3 unless `--version` was provided explicitly
- `release_automation.sh` validated release notes file but passed `--notes "Release
  TAG"` instead — all GitHub releases had empty bodies
- `ci-cd.yml` release job used `--notes-file CHANGELOG.md`, dumping the entire
  changelog history as release notes

## [0.6.1] - 2026-01-16

### Added

- **Push webhook & WebSocket client** — optional `POST /api/luxor_living/push`
  endpoint and configurable WebSocket client (`push_ws_url`) to accept external
  pushed KNX state updates. Supports configurable authentication: `none`,
  `token`, `bearer`, and `hmac` (HMAC-SHA256).

### Changed

- Documented push options and added tests for push handling and WebSocket
  client.

### Testing

- All 287 tests passing (unit + integration-style), including push client/view,
  integration_state, platform_detector, override_handler, and coordinator auth
  suites.

## [0.6.0] - 2026-01-11

### 🚀 Major Refactoring & Audit Compliance

This release implements all critical findings from Week 2-3 external audit
reviews, significantly improving code quality, security, and maintainability.

### ✨ Added

- **🔒 Security Scanning** - Automated vulnerability detection
  - `bandit` security linter in CI workflow
  - `pip-audit` dependency vulnerability scanning
  - Security policy enforcement via GitHub Actions
  - Dependabot configuration with security labels

- **📐 Type-Safe State Management** (Issue #5)
  - New `IntegrationState` dataclass replacing global dict storage
  - Runtime validation of required fields
  - IDE autocomplete and type checking support
  - Helper methods: `get_gateway_or_raise()`, `get_coordinator_or_raise()`,
    `is_ready()`
  - Global state registry with `register/unregister/get_integration_state()`
  - Comprehensive test coverage (16 new tests)

- **📚 Comprehensive Documentation**
  - **Architecture Overview** - System design, component responsibilities, data
    flows
  - **Incident Response Runbook** - Emergency procedures (P0-P3 severity
    classification)
  - **README restructure** - Organized by audience (Users/Developers/DevOps)

### 🔧 Refactoring

- **EntityMapper Modularization** (Issue #2)
  - Split 523 LOC god object into focused modules:
    - `PlatformDetector` (160 LOC, 100% coverage, 33 tests)
    - `OverrideHandler` (180 LOC, 93.75% coverage, 17 tests)
    - `MappedEntity` dataclass (27 LOC)
  - Dependency injection for testability
  - EntityMapper reduced to 405 LOC (-23%)

- **State Management** (Issue #5)
  - Removed all `hass.data[DOMAIN][entry_id]` dict access
  - All platforms use type-safe `get_integration_state()`
  - Updated: light, switch, cover, climate, sensor, binary_sensor
  - Backward compatibility removed for cleaner codebase

### 🧪 Testing Improvements (Issue #3)

- **Coverage Increase**: 55% → 68.99% (+25%)
- **New Test Suites**:
  - `test_coordinator_auth.py` (9 tests, coordinator auth failure handling)
  - `test_circuit_breaker.py` (15 tests, 100% state machine coverage)
  - `test_integration_state.py` (16 tests, state management validation)
- **Total Tests**: 221 → 287 (+66 tests, +30%)
- **All 287 tests passing** ✅

### 📊 Quality Metrics

| Metric              | Before | After  | Change |
| ------------------- | ------ | ------ | ------ |
| Test Coverage       | 55%    | 68.99% | +25%   |
| EntityMapper LOC    | 523    | 405    | -23%   |
| Tests               | 221    | 287    | +30%   |
| Documentation Pages | 8      | 10     | +25%   |

### 🐛 Bug Fixes

- Fixed circular import in EntityMapper refactoring
- Fixed async fixture error in performance benchmarks
- Fixed integration state registry cleanup between tests

### ⚠️ Breaking Changes

- **State Management**: Custom integrations accessing `hass.data[DOMAIN]`
  directly must migrate to `get_integration_state()`
- **EntityMapper API**: Direct instantiation now requires dependency injection

### 🔐 Re-Authentication Flow (from 0.5.x)

- Automatic credential recovery after 3 consecutive authentication failures
- User-friendly credential update UI
- Automatic reconnection after successful re-authentication

### 🌍 Multi-Language Support (from 0.5.x)

- 🇩🇪 German (de) translation
- 🇫🇷 French (fr) translation
- 🇬🇧 English (en) translation

### 📊 Quality Scale Status

| Tier   | Status         | Progress |
| ------ | -------------- | -------- |
| Bronze | ✅ Complete    | 100%     |
| Silver | ✅ Complete    | 100%     |
| Gold   | ⚠️ In Progress | 45%      |

**Audit Compliance:**

- ✅ Issue #1: Security Posture (bandit + pip-audit)
- ✅ Issue #2: EntityMapper Complexity (refactored with DI)
- ✅ Issue #3: Test Coverage Gaps (55% → 69%)
- ✅ Issue #4: Documentation Discoverability (new architecture docs)
- ✅ Issue #5: Global Dict Storage (type-safe IntegrationState)

**Next Steps to Gold:**

- Automatic gateway discovery (SSDP/mDNS)
- Full reconfiguration flow (IP/credentials via UI)

---

## [0.5.4] - 2026-01-09

### 🥈 Home Assistant Silver Compliance Features

This release implements critical features to achieve **Home Assistant Silver
Quality Scale** compliance:

### ✨ Added

- **🔐 Re-Authentication Flow** - Automatic credential recovery
  - Repair flow triggers after 3 consecutive authentication failures
  - User-friendly credential update UI
  - Automatic reconnection after successful re-authentication
  - Integration reload without reconfiguration

- **🌍 Multi-Language Support** - Full internationalization
  - 🇩🇪 German (de) translation
  - 🇫🇷 French (fr) translation
  - 🇬🇧 English (en) translation
  - Localized config flow, error messages, and repair flows

- **🐛 Bug Fixes**
  - Fixed `test_integration_entity_creation_benchmark` async fixture error
  - Simplified performance test to avoid Home Assistant instance dependency

### 🔧 Technical Improvements

- Coordinator now tracks authentication failures and triggers repair flow
- Added `repairs.py` module with authentication repair flow handler
- Enhanced `strings.json` with issue and repair translations
- Updated coordinator to accept `ConfigEntry` parameter for repair flow
- All 212 tests passing ✅

### 📊 Quality Scale Status

| Tier   | Status         | Progress |
| ------ | -------------- | -------- |
| Bronze | ✅ Complete    | 100%     |
| Silver | ✅ Complete    | 100%     |
| Gold   | ⚠️ In Progress | 40%      |

**Next Steps to Gold:**

- Automatic gateway discovery (SSDP/mDNS)
- Full reconfiguration flow (IP/credentials via UI)
- Extended end-user documentation (examples, blueprints)

### ⚠️ Breaking Changes

None - fully backward compatible with v0.5.x

### 🧪 Testing

```bash
python -m pytest tests/ -v  # 212 tests passing
```

---

## [0.6.0-beta.1] - 2026-01-07

### 🥈 Home Assistant Silver Compliance Features

**Status:** BETA Release - Testing Welcome!

This release implements critical features to achieve **Home Assistant Silver
Quality Scale** compliance:

### ✨ Added

- **🔐 Re-Authentication Flow** - Automatic credential recovery
  - Repair flow triggers after 3 consecutive authentication failures
  - User-friendly credential update UI
  - Automatic reconnection after successful re-authentication
  - Integration reload without reconfiguration

- **🌍 Multi-Language Support** - Full internationalization
  - 🇩🇪 German (de) translation
  - 🇫🇷 French (fr) translation
  - 🇬🇧 English (en) translation
  - Localized config flow, error messages, and repair flows

- **🐛 Bug Fixes**
  - Fixed `test_integration_entity_creation_benchmark` async fixture error
  - Simplified performance test to avoid Home Assistant instance dependency

### 🔧 Technical Improvements

- Coordinator now tracks authentication failures and triggers repair flow
- Added `repairs.py` module with authentication repair flow handler
- Enhanced `strings.json` with issue and repair translations
- Updated coordinator to accept `ConfigEntry` parameter for repair flow
- All 212 tests passing ✅

### 📊 Quality Scale Status

| Tier   | Status         | Progress |
| ------ | -------------- | -------- |
| Bronze | ✅ Complete    | 100%     |
| Silver | ✅ Complete    | 100%     |
| Gold   | ⚠️ In Progress | 40%      |

**Next Steps to Gold:**

- Automatic gateway discovery (SSDP/mDNS)
- Full reconfiguration flow (IP/credentials via UI)
- Extended end-user documentation (examples, blueprints)

### ⚠️ Breaking Changes

None - fully backward compatible with v0.5.x

### 🧪 Testing

```bash
python -m pytest tests/ -v  # 212 tests passing
```

---

## [0.5.2] - 2026-01-02

### 🚀 Major Features

- **Climate Platform:** Full support for H6 heating actuators (FBH zones) with
  temperature control
  - Current temperature (Istwert) and setpoint (Sollwert) display
  - Temperature adjustment with 0.5°C steps (5°C - 35°C range)
  - HVAC mode switching (Heat/Off)
  - Window contact monitoring
  - Valve position tracking (Stellgrösse)
  - **9 heating zones** detected in test project (Hauptwohnung.lxp)

- **Cover Platform:** Full support for J8/J4 shutter and blind actuators
  - Open/Close/Stop controls (UpDown, StepStop)
  - Position control (Höhe%) with feedback (StatusHöhe%)
  - Tilt/Slat control (Lamelle%) with feedback (StatusLamelle%)
  - Safety features (Rain/Frost/Wind sensors, Panic mode)
  - Window contact integration
  - Device class auto-detection (Shutter vs. Blind based on tilt capability)
  - **15 covers** detected in test project (all with tilt support)

- **Parallel Entity Creation:** Async entity instantiation across all platforms
  using `asyncio.gather`
- **Configurable Discovery Timeout:** User-adjustable auto-discovery debounce
  delay (0.5-10.0s) via Options Flow
- **Performance Benchmarking:** Comprehensive benchmarking framework with
  regression detection
- **Circuit Breaker Protection:** Resilient error handling with configurable
  failure thresholds and recovery
- **Smart LXP Caching:** TTL-based caching with automatic eviction and memory
  management
- **Health Check Endpoint:** System monitoring and diagnostics at
  `/api/luxor_living/health`

### 🔧 Improvements

- **Enhanced LXP Parser:** Device-level warnings for unconfigured devices,
  detailed statistics logging
- **Validation Tools:** New `validate_climate_cover.py` script for entity
  validation
- **Async Optimizations:** CPU-intensive operations run in thread pools to
  prevent blocking
- **Enhanced Error Handling:** Comprehensive error scenario testing and graceful
  degradation
- **Memory Usage Tracking:** Built-in memory monitoring for performance analysis
- **Configuration Options:** Extended Options Flow with discovery timeout and
  log level controls
- **Developer Tools:** Benchmark framework for performance measurement and
  analysis

### 🧪 Quality Assurance

- **Climate/Cover Tests:** 30 new test cases for heating and cover platforms
- **Performance Tests:** Automated benchmarking and regression detection (11
  test cases)
- **Error Scenario Tests:** Circuit breaker and concurrent error handling
  validation
- **Test Coverage:** 178 total tests passing, comprehensive integration testing
- **Code Quality:** Enhanced type safety and error handling patterns
- **Real-World Validation:** Tested with Hauptwohnung.lxp (63 devices, 851
  datapoints)

### 📊 Performance Metrics

- **Startup Time:** Up to 70% faster entity creation through parallelization
- **Memory Usage:** Optimized caching reduces memory footprint
- **Error Recovery:** Automatic circuit breaker recovery within configurable
  timeouts
- **Reliability:** Enhanced resilience against network failures and timeouts

---

## [Unreleased]

### Added

- Placeholder

### Changed

- Placeholder

---

## [0.6.1-beta.4] - 2026-01-16

### Added

- **Push webhook & WebSocket client** — optional `POST /api/luxor_living/push`
  endpoint and configurable WebSocket client (`push_ws_url`) to accept external
  pushed KNX state updates. Supports configurable authentication: `none`,
  `token`, `bearer`, and `hmac` (HMAC-SHA256).

### Changed

- Documented push options and added tests for push handling and WebSocket
  client.

### Testing

- All 287 tests passing (unit + integration-style), including push client/view,
  integration_state, platform_detector, override_handler, and coordinator auth
  suites.

### Planned

## [0.5.4.3] - 2026-01-03

### ✅ Release Notes

- Final release attempt after resolving GitHub Actions permissions and immutable
  release issues
- Automated CI/CD pipeline with GitHub Release creation
- ZIP archive for HACS/manual installation
- All changes from v0.5.4 preserved

### 🧪 Testing

- Local: `python -m pytest tests/` → 209 passed
- CI/CD: `python -m pytest tests/ -m "not enable_socket"` → 195 passed (14
  skipped socket tests)

---

## [0.5.4-beta.1] - 2026-01-03

### 🔒 HTTPS Enforcement Pre-Release (superseded by 0.5.4)

**Goal:** Validate HTTPS authentication enforcement for outbound requests.

#### Added

- Enforce HTTPS authentication path for external requests
  (copilot/enforce-https-authentication merged into main)
- Pre-release build to test HTTPS request handling

#### Quality

- Tests: pending validation in this pre-release cycle
- Quality gates: pending (validate_readme.sh to be executed before final
  release)

---

## [0.5.3] - 2026-01-02

### 🎯 Quality Assurance Improvements

**Focus:** Enhanced release process reliability and documentation quality gates

#### Added

- **README.md Quality Gates:** Automated validation script
  (`scripts/validate_readme.sh`)
  - Version consistency checks (manifest.json ↔ README.md ↔ CHANGELOG.md)
  - Test count accuracy verification (pytest ↔ README.md)
  - Documentation link validation (no 404s)
  - CHANGELOG.md release entry validation
  - Detection of versioned [Unreleased] sections (common mistake)

- **CHANGELOG.md Quality Gates:** Mandatory pre-release validation
  - Ensures current version has proper release entry
  - Prevents accidental versioned [Unreleased] sections
  - Validates [Unreleased] section exists for future work

- **Enhanced Release Documentation:**
  - Updated `docs/RELEASE_OPERATIONS.md` with README/CHANGELOG quality gates
  - Added automated validation workflow to Step 0.4
  - Updated GitHub Release template with current metrics (207 tests)
  - Generalized version examples for future releases
  - SSH workaround documentation (`-F /dev/null` for git operations)

- **Agent Documentation:**
  - Enhanced `agent_release_manager.md` with quality gate workflows
  - Added `RELEASE_OPERATIONS_REVIEW.md` (comprehensive review report)
  - Updated critical rules to include CHANGELOG.md validation

#### Fixed

- **CHANGELOG.md:** Corrected v0.5.2 release entry (was incorrectly marked as
  [Unreleased])
- **README.md:** Removed broken link to non-existent `AGENTS.md`
- **Documentation Links:** All links validated and verified functional
- **Release Process:** Eliminated RELEASE_NOTES.md references (project uses
  CHANGELOG.md)

#### Changed

- **Quality Standards:** README.md and CHANGELOG.md now validated with same
  rigor as code tests
- **Release Workflow:** Mandatory `./scripts/validate_readme.sh` before each
  release
- **Documentation Metrics:** Updated all references to current test count (207
  tests)

### 📊 Quality Metrics

- **Validation Script:** 6-step automated quality gate
- **Test Count:** 207/207 passing (100% success rate)
- **Quality Coverage:** README + CHANGELOG + Links + Version consistency
- **Release Safety:** Prevents common documentation errors before release

### 🔧 Technical Details

**Validation Script Features:**

```bash
./scripts/validate_readme.sh
# Checks:
# 1. Version consistency (manifest ↔ README)
# 2. Test count accuracy (pytest ↔ README)
# 3. Documentation links (all files exist)
# 4. Outdated patterns detection
# 5. CHANGELOG.md release entry
# 6. [Unreleased] section validation
```

**Exit Codes:**

- `0` = All checks passed (safe to release)
- `1` = Errors found (must fix before release)

---

## [0.4.0] - 2025-12-27

### 🚀 Major Features

- **Auto-Discovery:** Automatische Erkennung von ION Temperatursensoren via
  Bus-Monitoring
- **REST API Authentication:** Automatische Tunneling-Aktivierung bei Startup
  (Hybrid-Ansatz)
- **LXP Parameter Extraction:** Vollständige Extraktion und Anzeige von
  LXP-Parametern
- **Duplicate Name Cleaning:** Automatische Bereinigung von doppelten
  Entity-Namen
- **Memory Management:** MAX_CANDIDATES Limit zur Verhinderung von Memory-Leaks
- **Sensor Type Detection:** Entity-basierte automatische Sensor-Typ-Erkennung

### 🔧 Improvements

- **Enhanced Diagnostics:** Verbesserte Diagnose mit detaillierten Entity-Listen
- **Connection Stability:** Robuste Fehlerbehandlung bei Verbindungsproblemen
- **Performance:** Optimierte LXP-Parsing und Discovery-Algorithmen
- **Logging:** Verbesserte Debug-Informationen für Troubleshooting

### 🐛 Bug Fixes

- **Syntax Error:** Behoben in sensor.py async_will_remove_from_hass
- **Import Issues:** Alle Module korrekt importiert und verfügbar
- **Configuration:** Manifest.json Version korrekt gesetzt

### 🧪 Quality Assurance

- **Test Coverage:** 74/74 Tests passing (100%)
- **Code Quality:** Syntax-Check und Type-Checking erfolgreich
- **Security:** defusedxml für sichere XML-Parsing implementiert

## [0.3.6] - 2025-12-26

### 🔥 Critical Hotfix

- **DPT 9.xxx (2-byte float) conversion completely broken** - Fixed API usage
  - Root cause: `from_knx()` expects `DPTArray` object, not raw `bytes()`
  - Impact: Wetterstation sensors showed raw bytes `(5, 20)` instead of
    temperature `13.0°C`
  - Fixed: All DPT 9.xxx sensors now convert properly (Temperature, Wind, Lux,
    Humidity, Pressure)
  - Bonus: 🌡️ emoji logging now works → enables ION temperature discovery via
    bus monitoring

## [0.3.5] - 2025-12-26

### 🔥 Hotfix

- **CRITICAL**: Fixed missing import `DPT2ByteFloat` in knx_gateway.py
  - **Impact:** Wetterstation and all DPT 9.xxx sensors (Temperature, Wind, Lux)
    showed raw bytes instead of converted values
  - **Bus Monitoring:** Temperature telegrams were not recognized (no 🌡️ emoji
    in logs)
  - **ION Discovery:** Made ION temperature address discovery impossible
  - **Fix:** Added `from xknx.dpt.dpt_9 import DPT2ByteFloat` import

---

## [0.3.4] - 2025-12-26

### 🛠️ Fixed

- **Critical**: Test fixtures - Added proper `conftest.py` with MockConfigEntry
  and HA-compatible fixtures
- **Critical**: Options Flow reload - Verified correct implementation (already
  working)
- **High**: Password redaction in diagnostics - Sensitive data now shows
  `**REDACTED**`
- **High**: Enhanced diagnostics entity handling - Detailed entity list
  (first 50) + summary by platform
- **High**: Consistent CONF_SCAN_INTERVAL usage across codebase

### 🏗️ Agent Reorganization

- **New**: Created `agent_defect_tracker.md` for systematic bug management
- **Enhanced**: Expanded `agent_architect.md` with comprehensive code quality
  standards
- **Updated**: Rewrote `CONTEXT.md` as Single Source of Truth (removed outdated
  Proxmox/Madeira references, added current SSH deployment to 100.97.159.88)
- **Created**: Comprehensive `.github/copilot/README.md` for agent documentation
- **Archived**: 6 obsolete agents (12 → 7 active): code_quality, config_flow,
  lxp_import, mapping, documentation, github_release_workflow

### ✅ Quality

- All 86 tests passing
- Enhanced test coverage with proper fixtures
- Improved diagnostics for debugging

---

## [0.3.1-beta.2] - 2025-12-24

### 🛠️ Fixed

- **Sensor Platform Registration**: `Platform.SENSOR` zur `PLATFORMS`-Liste in
  `__init__.py` hinzugefügt.
  - Behebt, dass die Sensor-Plattform nicht geladen wurde und keine
    Sensor-Entities erstellt wurden.
  - Sichtbare Logs nach Fix: "Setting up LUXORliving sensors" und "Creating N
    sensor entities".

---

## [0.3.1-beta.1] - 2025-12-24

### 🎉 New Features

- **Sensor Platform**: Full implementation of Home Assistant sensor platform for
  float/string values
  - Automatic detection of sensor types: Temperature, Humidity, Pressure, CO2,
    Brightness, WindSpeed, RainVolume, AirQuality
  - Proper unit of measurement handling (°C, %, hPa, ppm, lux, m/s, mm)
  - Device class mapping for proper Home Assistant integration (temperature,
    humidity, pressure, illuminance, precipitation)
  - Initial state reading from KNX via `async_read_group_value`
  - Real-time updates via KNX telegram listeners

### ✨ Improvements

- **EntityMapper Extension**: Added sensor role detection and unit mapping
  - `ROLE_TO_UNIT`: Maps sensor roles to HA units
  - `ROLE_TO_DEVICE_CLASS`: Maps sensor roles to HA device classes
  - Priority-based role detection (sensors first, then binary/switches)

### 🧪 Testing

- Added comprehensive sensor platform tests (11 new test cases)
- Test coverage for entity initialization, KNX state reading, telegram updates
- All 85 tests passing (74 existing + 11 new)

### 📋 Known Limitations

- Climate platform: Not yet implemented (no actuators in current projects)
- Cover platform: Not yet implemented (no actuators in current projects)

---

## [0.3.0] - 2025-12-24

This is the first stable release of the LUXORliving Home Assistant integration.
All critical issues from beta testing have been resolved.

### 🎉 Major Features

- **Full KNX Integration**: Seamless integration with KNX-based home automation
  systems
- **LXP Project Support**: Automatic entity generation from LUXORliving .lxp
  project files
- **Multi-Device Support**: Proper handling of multiple devices (S16, B6, iON4,
  etc.)
- **Real-time Updates**: Event-driven state updates via KNX telegrams
- **Multiple Platforms**: Light, Switch, and Binary Sensor entities

### ✨ Fixed (from beta.3)

- **Entity Mapper Unique ID Generation**: Use KNX addresses instead of
  actuator/sensor IDs
  - Multiple actuators/sensors with same name but different addresses now get
    unique IDs
  - Use control address (OnOff, SchaltenOnOff, Dimmen%, UpDown) for actuators
  - Resolves "Platform luxor_living does not generate unique IDs" errors

- **Per-Device Entity Grouping**: Entities properly organized by their source
  device
  - S16, B6, iON4 devices appear as separate devices in Home Assistant
  - Each device has its own entity list in the UI
  - Proper device identification for automation and scenes

- **Entity Type Handling**: Fixed MappedEntity attribute access
  - Proper dataclass usage throughout the codebase
  - Fixed 'MappedEntity' object has no attribute 'get' errors

- **Coordinator Architecture**: Event-driven passive state model
  - Removed invalid XKNX device polling logic
  - State updates from KNX telegram listeners (push-based)
  - Proper alignment with KNX event-driven architecture

- **Platform Defensive Checks**: Robust error handling
  - Light, Switch, and Binary Sensor platforms validate integration data
  - Graceful degradation with meaningful error messages

### 📊 Testing & Quality

- **All 74 tests passing** with zero regressions
- HACS compliant: unique IDs, device info, proper structure
- Home Assistant Core compliant: Coordinator pattern, entity standards
- Production ready: Tested with real LUXORliving hardware

### 🔧 Technical Details

- **Minimum Home Assistant**: 2025.12.0
- **Python Version**: 3.11+
- **Dependencies**: xknx≥3.11.0, defusedxml≥0.7.1, aiohttp≥3.9.0

### ⚠️ Breaking Changes from v0.2.x

- Entity unique_ids have changed (no longer backwards compatible)
- Entities will re-register in Home Assistant with new unique_ids
- Automations/scripts may need updating if they reference old entity IDs
- Previous beta versions (0.3.0-beta.\*) will have their entities migrated

### 🚀 Upgrade Instructions

1. Backup your Home Assistant configuration
2. Update to v0.3.0 through HACS
3. Re-import the .lxp file (or restart integration)
4. Entities will re-register with proper unique IDs
5. Update any automations/scripts that reference entity IDs

---

## [0.3.0-beta.3] - 2025-12-23

### Fixed

- **Entity Mapper Unique ID Generation**: Use KNX addresses instead of
  actuator/sensor IDs
  - Multiple actuators/sensors with same name but different addresses now get
    unique IDs
  - Use control address (OnOff, SchaltenOnOff, Dimmen%, UpDown) for actuators
  - Use first datapoint address for sensors
  - **Critical Fix**: Resolves "Platform luxor_living does not generate unique
    IDs" errors
  - Example: Two "Reserve Deckenlampe" at addresses 2074 and 2075 now generate
    different IDs

- **Per-Device Entity Grouping**: Entities properly organized by source device
  - Each LXP device (S16-1, S16-2, B6-1, etc.) gets separate Home Assistant
    device
  - Fixes: Only "Luxor Living Gateway" was shown before

- **Entity Base Class Type Handling**: Fixed MappedEntity attribute access
  - Changed mapped_entity parameter from dict to MappedEntity dataclass
  - Updated name property to use getattr() for attributes
  - Fixed 'MappedEntity' object has no attribute 'get' errors in all platforms

- **Entity Unique ID Usage**: Use MappedEntity's address-based unique_id
  directly
  - Platform implementations now use unique_id from MappedEntity
  - Guarantees unique entity registration in Home Assistant
  - Prevents "already exists" errors when registering multiple entities

- **Coordinator Architecture Simplified**: Changed from broken polling model to
  event-driven passive state model
  - Removed invalid XKNX device polling logic (`.devices.items()` and
    `resolve_state()` calls)
  - Coordinator now acts as passive cache holder instead of active poller
  - State updates come from KNX telegram listeners (push-based)
  - Properly aligns with KNX event-driven architecture
  - Code simplified: -16 lines (20 removed, 4 added)

- **Platform Defensive Checks**: Added robust error handling for integration
  data access
  - Light, Switch, and Binary Sensor platforms now validate integration data
  - Type checking with `isinstance(integration_data, dict)`
  - Try/except blocks around data access
  - Graceful degradation with meaningful error messages

### Testing

- All 74 tests passing with zero regressions
- Entity unique IDs properly derived from KNX addresses (guaranteed unique)
- Multiple actuators/sensors with same name now work correctly
- Entities properly grouped by their source device
- Entity base class properly handles MappedEntity objects
- Coordinator architecture corrected to match actual KNX event-driven model
- All platforms properly handle missing or invalid integration data

---

## [0.3.0-beta.2] - 2025-12-23

### Fixed

- **Coordinator Data Update**: Fixed 'Devices' object iteration error
  - XKNX devices collection is not dict-like, requires direct iteration
  - Properly extracts `group_address_state` from each device
  - Added fallback to `group_address` if state address unavailable
  - Improved error logging with device names instead of addresses

### Testing

- All 74 tests passing after fix
- No regressions introduced
- Coordinator properly handles XKNX Devices collection

---

## [0.3.0] - 2025-12-23

### Highlights

**Production-Ready HACS Release** with complete DataUpdateCoordinator pattern,
device registry integration, and comprehensive type hints.

### Added

- **DataUpdateCoordinator Pattern**: Centralized state management for all
  entities
  - Async polling every 30 seconds
  - State cache for all KNX group addresses
  - Proper coordinator lifecycle management
  - `async_config_entry_first_refresh()` support

- **Entity Base Class (LuxorLivingEntity)**:
  - Common functionality for all entity types
  - Device registry integration via `device_info` property
  - Coordinator listener management
  - Unique ID generation from entity attributes
  - `async_added_to_hass()` with automatic listener registration

- **Type Hints**: 100% coverage on critical platforms
  - All function parameters typed
  - All return types annotated
  - Enables IDE autocompletion and type checking

- **Code Quality Tools**:
  - Black formatter configuration (line-length=100, py313)
  - isort import organization (black profile)
  - mypy type checking (strict mode)
  - flake8 linting configuration
  - bandit security scanning
  - pre-commit hooks for automated checks
  - py.typed marker for PEP 561 support

- **Test Coverage Baseline**: 55% (1408 statements, 640 missed)
  - 74 comprehensive tests (100% passing)
  - Test suite includes platform imports, constants, coordinator structure
  - Coverage metrics per module documented

### Changed

- **Light Platform**: Complete refactoring
  - Now extends `LuxorLivingEntity` + `LightEntity`
  - Full type hints on all parameters
  - DataUpdateCoordinator integration
  - ConfigEntry support
  - Improved docstrings

- **Switch Platform**: Complete refactoring
  - Now extends `LuxorLivingEntity` + `SwitchEntity`
  - Full type hints coverage
  - DataUpdateCoordinator integration
  - Binary sensor dual-listener support

- **Binary Sensor Platform**: Enhanced with auto-detection
  - Now extends `LuxorLivingEntity` + `BinarySensorEntity`
  - Automatic device class detection
  - Full type hints implementation
  - Improved entity naming

- **Import Organization**: All files reformatted with isort
  - Stdlib → third-party → first-party ordering
  - Black-compatible formatting
  - Consistent throughout codebase

- **Documentation**: All docstrings and comments enhanced
  - Detailed parameter documentation
  - Return value descriptions
  - Usage examples on complex functions

### Fixed

- Device registry integration now properly implemented on all entities
- Inconsistent entity implementations across platforms
- Missing type hints causing IDE issues
- Import organization inconsistencies

### Quality Assurance

- ✅ **74/74 Tests Passing** (100% success rate)
- ✅ **Black Format**: 100% compliant (26 files)
- ✅ **Type Hints**: 100% on critical modules
- ✅ **Coverage Baseline**: 55% established
- ✅ **Code Style**: isort organized imports
- ✅ **Documentation**: CHANGELOG fully English

### Technical Details

**Coordinator Implementation:**

```python
class LuxorLivingCoordinator(DataUpdateCoordinator):
    """Manages state updates for all KNX entities."""

    def __init__(self, hass, host):
        super().__init__(hass, _LOGGER, name="Luxor Living",
                         update_interval=timedelta(seconds=30))
        self.gateway = LuxorKNXGateway(host)

    async def _async_update_data(self):
        """Fetch data from KNX gateway."""
        try:
            return await self.gateway.get_all_states()
        except Exception as err:
            raise UpdateFailed(f"Error: {err}") from err
```

**Entity Base Class Benefits:**

- Automatic device info generation
- Listener registration/unregistration
- Unique ID handling
- Coordinator integration
- Common lifecycle management

**Type Hints Example:**

```python
def __init__(
    self,
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
    knx_gateway: LuxorKNXGateway,
) -> None:
    """Initialize light entity."""
```

### Known Issues

- Test coverage: 55% (ongoing improvement in 0.3.x)
- Climate, Cover, Sensor platforms: Development in progress
- Some REST client error paths: Need additional coverage

### Installation

**Via HACS:**

1. Open HACS → Integrations
2. Search for "LUXORliving"
3. Click Install
4. Restart Home Assistant
5. Settings → Devices & Services → Create Integration

**Manual:**

1. Download v0.3.0 release
2. Extract to `~/.homeassistant/custom_components/luxor_living/`
3. Restart Home Assistant

## [Unreleased]

### Added

- DataUpdateCoordinator pattern for centralized state management
- LuxorLivingEntity base class for common entity functionality
- Device registry integration for all platforms
- Type hints on all functions and parameters
- Code formatting with Black and isort
- Comprehensive test coverage (55% baseline established)
- py.typed marker for type checking support

### Changed

- Light platform refactored to use DataUpdateCoordinator
- Switch platform refactored to use DataUpdateCoordinator
- Binary Sensor platform refactored with auto-detection of device classes
- All platforms now extend LuxorLivingEntity base class
- Improved docstrings on all methods
- Import organization with isort

### Fixed

- Device registry integration missing in entities
- Inconsistent entity implementations across platforms
- Missing type hints causing IDE issues

## [0.2.12] - 2025-12-23

### Highlights

- **Log Enrichment**: GroupAddress→Entity and IndividualAddress→Device labels in
  log output for improved traceability
- **Dimmable Light Brightness**: Status% (2/3/0) read initially and monitored
  continuously
- **Event Loop Safety**: Robust callback scheduling with test-time fallback for
  HA-loop absence

### Added

- `knx_gateway.py`:
  - `set_group_address_labels()` - Sets GA→Entity label map for log enrichment
  - `set_individual_address_labels()` - Sets IA→Device label map for log
    enrichment
  - GA and IA labels in log output (📥 Received KNX telegram with Source IA Name
    and Destination GA Entity Name)
  - Fallback to direct callback invocation when HA Event Loop unavailable (test
    safety)

- `entity_mapper.py`:
  - `get_group_address_label_map()` - Creates GA→["Entity Name (ID)"] map
  - `get_individual_address_label_map()` - Creates IA→["Device Name (DeviceID)"]
    map

- `light.py`:
  - `LuxorLivingDimmableLight._address_dim_status` - Additional Status% address
    (2/3/0) listener
  - Initial read on Status% address for brightness initialization
  - `knx_address_dim_status` as extra attribute for dimmable lights

- Test Updates:
  - Dual listener tests for Light and Switch
  - KNX initial read tests (no REST-based initialization anymore)
  - Gateway callback scheduling tests with HA-loop fallback

### Changed

- Log output now contains human-readable names instead of only
  GroupAddress/IndividualAddress numbers
- Dimmable lights now listen to 2 addresses: `Dimmen%` (2/2/0) and `Status%`
  (2/3/0)
- Tests: Expectations adjusted for dual-listener architecture and KNX-only
  initial reads

### Fixed

- Brightness updates on dimmable lights now support both Dimmen% and Status%
  addresses
- HA Event Loop absence no longer causes callback scheduling failures (test
  compatibility)
- Log tracing now bidirectionally visible (who sends to whom)

### Removed

- REST-based initial reads (fully migrated to KNX reads)

### Quality

- ✅ **58/58 Tests Passing** (100%)
- ✅ **Code Quality Score:** 8.5/10
- ⚠️ **TLSv1 Deprecation Warnings** in rest_client.py (Minor)

### Technical Details

**Brightness Handling for Dimmable Lights:**

- Initial read sends telegrams to both addresses
- Listener registered on Dimmen% (2/2/0) and Status% (2/3/0)
- `_handle_brightness_update()` combines updates from both sources
- Percent-to-brightness conversion: `brightness = int((percent / 100) * 255)`

**Log Enrichment:**

- Gateway receives GA→Entity map on setup (`set_group_address_labels()`)
- Gateway receives IA→Device map on setup (`set_individual_address_labels()`)
- On telegram reception, labels are looked up from map and displayed
- Format: "📥 Received KNX telegram: Source IA: 9.0.12 (Device "Name"),
  Destination GA: 5/0/1 (Entity "light.badlicht")"

---

## [0.2.11] - 2025-12-20

### Added

- Dual KNX Listener Architecture for Light and Switch Entities
- Listeners on STATUS and CONTROL Group Addresses
- Initial reads on KNX addresses for state initialization
- `rest_client.py` for BAOS REST authentication and tunneling management
- Integration of XKNX v3.11.0 for KNX/IP communication

### Features

- ✅ Light platform with on/off and dimming
- ✅ Switch platform with on/off control
- ✅ Binary Sensor platform for motion detectors and contacts
- ✅ LXP parser for Theben LUXORliving projects
- ✅ Entity mapper for automatic entity creation from LXP

### Testing

- 46 tests for core functionality
- Simulation mode for tests without hardware
- Config flow tests

---

## [0.2.10] and earlier

See git history for details on older versions.

---

## Roadmap

### Q1 2026

- 📅 **Cover Platform** (blinds, roller shutters)
- 📅 **Climate Platform** (thermostats)
- 📅 **Sensor Platform** improvements

### Q2 2026

- 🔮 Multi-device support (multiple gateways)
- 🔮 Automation templates
- 🔮 Dashboard widgets

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards-compatible)
- **PATCH**: Bugfixes and improvements

---

For more information see [QUICKSTART.md](docs/QUICKSTART.md) and [docs/](docs/).
