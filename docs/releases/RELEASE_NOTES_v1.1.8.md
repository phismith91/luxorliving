# Release Notes — v1.1.8

## Added

- **Configuration parameters documented**: README now includes a dedicated
  "Configuration Parameters" section describing all config-flow and options-flow
  fields (gateway host, port, credentials, connection type, push-token, auth method).

- **Known Limitations section**: README documents the SSL certificate constraint
  (BAOS 777 uses a factory self-signed certificate, verification intentionally
  disabled), unsupported device types (scenes, RF-only), LXP reload behaviour,
  and other known limitations.

- **Removal instructions**: README documents how to remove the integration from
  Home Assistant (Settings → Devices & Services → Delete) and from HACS.

## Changed

- **Config flow test coverage expanded**: Added 6 new tests for the
  reauthentication flow (`async_step_reauth`, `async_step_reauth_confirm`) and
  the reconfigure flow (`async_step_reconfigure`), covering success paths and
  error cases. Satisfies HA quality scale Bronze rule `config-flow-test-coverage`.
  Test count: 765 → 771.

## Quality Scale

This release closes the following HA Integration Quality Scale gaps:

| Rule | Tier | Status |
| --- | --- | --- |
| `docs-removal` | Bronze | ✅ |
| `config-flow-test-coverage` | Bronze | ✅ |
| `docs-configuration-parameters` | Silver | ✅ |
| `docs-known-limitations` | Silver | ✅ |
