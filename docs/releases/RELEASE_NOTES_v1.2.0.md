# Release Notes — v1.2.0

> Pre-release: `v1.2.0-rc.1`. Adds the two quality-scale items that were
> deferred from the 1.1.15-rc cycle. The `v1.1.15-rc.1` pre-release remains
> published as a fallback. **Not yet validated against real IP1 hardware** —
> promote to stable only after a live check (the connection path changed).

## Added

- **Gold quality scale — stale-device handling**: implemented
  `async_remove_config_entry_device`. Devices that disappeared from the LXP
  project (no longer mapped by the integration) can now be deleted manually from
  the Home Assistant UI, while the gateway hub and active devices stay protected.

## Changed

- **Platinum quality scale — inject websession**: the REST client
  (`BAOSRestClient`) and the WebSocket `PushClient` now obtain their aiohttp
  session from Home Assistant's shared
  `async_get_clientsession(hass, verify_ssl=False)` instead of creating and
  owning their own `ClientSession`. The REST client accepts an injected session
  and only closes sessions it owns; the push client no longer closes the shared
  session. The per-request 30 s timeout is preserved explicitly, since the
  shared session carries no default total timeout.
  - Wired through `config_flow.py`, `repairs.py` and `knx_gateway.py`, which now
    pass the shared session into `BAOSRestClient`.

## Tests

- **TLS injection integration test** (`test_inject_session_tls_integration.py`):
  exercises the new injected-session constructor path over a *real*
  self-signed-TLS socket — full `login` → `async_get_datapoints` flow — proving
  the handshake, auth headers and per-request timeout all work on the shared
  `verify_ssl=False` session. This closes the gap that no prior `enable_socket`
  test covered (the old REST integration tests use plain HTTP and assign the
  session directly, bypassing the ownership logic). No hardware required.
- Gated unit tests for the owned-session default branch of `BAOSRestClient`
  (`_owns_session` defaults to `True`; `__aexit__` is safe when no session was
  opened).

## Risk / validation status

The Gold change is pure, hardware-independent boolean logic (≈no runtime risk).
The Platinum change touches the actual IP1 connection path: in production the
client now relies entirely on `verify_ssl=False` (the previous custom
`ssl_context` path is no longer reached). This is logically equivalent and is
now covered by an end-to-end self-signed-TLS test, but has **not** been run
against a physical IP1 gateway. Validate on real hardware before promoting
`v1.2.0-rc.1` to a stable `v1.2.0`.
