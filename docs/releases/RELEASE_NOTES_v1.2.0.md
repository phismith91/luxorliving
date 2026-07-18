# Release Notes — v1.2.0

> Pre-release: `v1.2.0-rc.2`. Ships the **Gold** quality-scale item only. The
> **Platinum** websession-injection shipped in `v1.2.0-rc.1` is **reverted** —
> it broke the connection to real IP1 hardware. The `v1.1.15-rc.1` pre-release
> remains published as a fallback.

## Added

- **Gold quality scale — stale-device handling**: implemented
  `async_remove_config_entry_device`. Devices that disappeared from the LXP
  project (no longer mapped by the integration) can now be deleted manually from
  the Home Assistant UI, while the gateway hub and active devices stay protected.

## Reverted — IP1 TLS regression fix

`v1.2.0-rc.1` routed the REST client (`BAOSRestClient`) and the WebSocket
`PushClient` through Home Assistant's shared
`async_get_clientsession(hass, verify_ssl=False)` instead of letting them create
and own their own `ClientSession`.

On real IP1 hardware this produced:

```
AuthenticationError: Network error during login: Cannot connect to host
<ip>:443 ssl:default [[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] ssl/tls alert
handshake failure (_ssl.c:1081)]
```

**Root cause:** the shared session bypassed the client's custom `ssl_context`.
The IP1 (BAOS) presents a legacy TLS cipher that modern OpenSSL 3.x rejects at
its default security level (SECLEVEL 2). The client's `ssl_context` lowers this
with `@SECLEVEL=0`, but that context is never used once an external session is
injected. `verify_ssl=False` only disables **certificate verification** — it
does **not** relax the OpenSSL security level, so the handshake still fails.

**Fix:** the REST client and `PushClient` again create and own their own
`ClientSession` built on the `@SECLEVEL=0` `ssl_context`, identical to the
known-good `v1.1.14` / `v1.1.15-rc.1` connection path. The injected-session
constructor parameter and its call sites (`config_flow.py`, `repairs.py`,
`knx_gateway.py`) are reverted.

**Removed tests:** `test_inject_session_tls_integration.py` and
`test_inject_websession.py`. The integration test exercised a self-signed-TLS
socket using a **modern** cipher, so it never reproduced the IP1's `SECLEVEL`
handshake failure and gave false confidence in the Platinum path.

**Status:** Platinum websession injection is incompatible with the IP1's TLS
stack — HA's shared session offers no per-request way to apply the required
`@SECLEVEL=0` policy. It is dropped, not deferred.

## Validation

- Gated test suite green (`pytest -m "not enable_socket"`): 924 passed.
- TLS connection path is byte-for-byte the `v1.1.14` / `v1.1.15-rc.1` logic that
  is confirmed working against live IP1 hardware in the field.
