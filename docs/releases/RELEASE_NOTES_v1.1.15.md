# Release Notes — v1.1.15

> Pre-release: `v1.1.15-rc.1`. Bundles the verified post-1.1.14 security,
> entity, and hygiene fixes plus a fully green gated test suite. Two
> quality-scale items (Gold stale-device handling, Platinum websession
> injection) are deferred to separate branches.

## Security

- **Diagnostics token leak**: `push_token` / `push_ws_token` were emitted
  verbatim in `entry.options` in both the minimal (no-consent) and full
  diagnostics payloads. Now redacted to `**REDACTED**` via `_redact_options()`.
- **Diagnostics read stale state**: since the v1.1.12 `runtime_data` refactor,
  diagnostics still read the old (always-empty in prod) `hass.data[DOMAIN]`
  path. Fixed with a `runtime_data`-first lookup (hass.data fallback for legacy
  tests).
- **TLS `@SECLEVEL=0` removed**: `set_ciphers("DEFAULT:@SECLEVEL=0")` permitted
  null/export cipher suites. The IP1 supports standard TLS 1.2+ suites without
  it. Extracted a `_make_ssl_context()` helper.
- **Timing-safe token comparison**: Token and Bearer auth in `push_view.py` used
  `!=` (timing oracle). Replaced with `hmac.compare_digest()`.

## Fixed

- **Dimmer brightness floor**: `int(brightness*100/255)` mapped brightness 1–2
  to `0%` (light off). Now `max(1, round(...))` for any non-zero brightness.
- **Dimmer turn_on guards**: dimmable `turn_on` skipped the
  `_raise_if_unavailable()` + rate-limit that the base/`turn_off` paths enforce.
  Both added.
- **Light listener timing**: both light classes registered KNX listeners in
  `__init__`, which runs in an executor thread — risking off-loop mutation of the
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

## Removed

- **Dead `switch` platform**: no LXP role maps to `Platform.SWITCH`
  (`OnOff`/`SchaltenOnOff` → `LIGHT`), so the platform produced zero entities and
  `LuxorLivingSwitch` (~230 lines) was unreachable. Verified against 4 real LXP
  files + the ETS5 product DB. Dropped from `PLATFORMS`.

## Changed

- **Linters now gate CI**: removed `--exit-zero` from bandit (pre-commit +
  Makefile) and `|| true` from flake8/bandit in the Makefile. Both pass cleanly.
- **mutmut config for 3.x**: `tests_dir` kept as a list so mutmut ≥ 3.3.1
  (CI-pinned) collects the smoke selection correctly.

## Tests

The gated suite (`-m "not enable_socket"`) is now fully green (was 2 failing):

- `test_full_entity_creation_benchmark` used the pre-refactor `hass.data[DOMAIN]`
  layout and the removed `switch` platform → now sets `entry.runtime_data` and
  drops `switch`.
- `test_push_client_receives_and_forwards` opened a real aiohttp websocket whose
  shutdown daemon thread trips HA's strict thread-leak guard — the same leak the
  `rest_client` socket tests already gate. Added the missing
  `@pytest.mark.enable_socket` marker (reclassification, not removal).

## Deferred to separate branches

- **Gold** — stale/dynamic device handling via `async_remove_config_entry_device`.
- **Platinum** — inject `homeassistant.helpers.aiohttp_client.async_get_clientsession(hass)`
  into `rest_client.py` and `push_client.py` instead of each creating its own
  `ClientSession`.
