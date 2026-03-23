# LUXORliving v1.1.1 — HACS Default Store Compliance

## Highlights

Fixes all blockers for HACS default store submission. All HACS validation
checks now pass without bypasses.

## Fixed

- **Brand assets**: icon moved to `custom_components/luxor_living/brand/icon.png`
  (HACS requires this exact path for the brands check)
- **Validate workflow**: removed `continue-on-error` bypass from HACS action,
  added `push` trigger per HACS submission requirements
- **Repository description**: removed surrounding literal quote characters

## Upgrade Notes

- No breaking changes — drop-in replacement for v1.1.0
- Install via HACS and restart Home Assistant
