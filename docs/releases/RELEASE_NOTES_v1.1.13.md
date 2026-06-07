# Release Notes — v1.1.13

## Security

- **Push endpoint now requires authentication**: The `/api/luxor_living/push`
  endpoint previously defaulted to unauthenticated access (`auth_method = none`),
  allowing any host that could reach the HA HTTP port to write arbitrary values to
  KNX group addresses (lights, covers, actuators). The `none` auth option is
  removed entirely. All requests without valid credentials now return `403`.
  Token and Bearer auth methods additionally reject if no token is configured
  (previously silently accepted all requests in that case).

- **Health view now requires HA authentication**: `/api/luxor_living/health`
  now sets `requires_auth = True` and requires a valid HA long-lived access token.
  Previously exposed topology information (entry IDs, KNX address counts,
  simulation mode, circuit breaker state) without authentication.

## Changed

- Push webhook Options Flow: `None` auth option removed. Existing installations
  with `auth_method = none` will have push requests rejected until a token and
  auth method are configured under Settings → Integrations → LUXORliving →
  Configure.

## Tests

3 new security regression tests covering the previously-open attack surface.
Test count: 990 → 992 (excluding socket-dependent tests).
