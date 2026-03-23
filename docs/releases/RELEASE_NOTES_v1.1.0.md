# LUXORliving v1.1.0 — Test Coverage 80%

## Highlights

Raises automated test coverage from 73% to **80%+**, meeting the Gold Quality
Scale target for v1.1.0. 725 tests now cover all major platforms end-to-end.

## Added

- **Extended test suite**: 6 new test files covering coordinator, binary sensor,
  sensor, switch, light, and cover platforms (725 tests total, up from 296)
- **Branch coverage ≥ 80%**: coordinator error paths, auth-failure counter,
  repair-issue trigger, health-entity diagnostics, DPT decode error handling,
  rate-limit guard, failed-telegram state guard, tilt/position cover commands

## Changed

- **Test count badge**: README updated to reflect 725 passing tests

## Upgrade Notes

- No breaking changes — pure test infrastructure improvement
- Install v1.1.0 via HACS and restart Home Assistant
