# Release Notes — v1.2.2

Pre-release (`v1.2.2-rc.1`). Full detail per change in [CHANGELOG.md](../../CHANGELOG.md#122---2026-08-02).

## Fixed

- **Cover tilt position inverted (#197)**: KNX `Lamelle%` follows the same
  0=open/100=closed convention as `Höhe%` (fixed for main position in
  v1.1.6), but tilt read/write and the open/close-tilt commands passed
  values straight through. A closed blind reported
  `current_tilt_position: 100` instead of `0`, and "open tilt"/"close tilt"
  sent the opposite KNX value from what they meant. All four tilt paths
  now apply the same `100 - x` inversion as position.
