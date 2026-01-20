# Security Rules

- Never commit secrets (tokens, HA creds, VPN keys); keep keys in env/secret storage; rotate immediately on exposure.
- Do not log sensitive payloads or URLs with tokens; scrub personally identifiable data; redact diagnostic exports when sharing.
- Use HTTPS for remote calls; validate TLS; prefer least-privilege tokens for CI; avoid embedding credentials in tests or fixtures.
- Validate and sanitize inbound data; enforce type hints; handle KNX/REST errors defensively and avoid crash loops.
- Before release, review for hardcoded endpoints/ids, ensure diagnostics omit secrets, and confirm licenses of bundled assets.
