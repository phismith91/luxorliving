# Release Notes — v1.2.1

Stable release, 2026-07-26. Supersedes `v1.2.1-rc.4` through `rc.9` and all
pre-1.2.1 pre-releases. Full detail per change in [CHANGELOG.md](../../CHANGELOG.md#121---2026-07-26).

## Added

- **H6 cooling-mode support**: H6 climate entities now support cooling in
  addition to heating when the `UmschaltenHeitzenKühlen` (heating/cooling
  mode-switch) datapoint is present. Marcus' setup with ION8 T10 mode-switch
  controlling H6 devices (511, 512, 513) is fully supported.

## Fixed

- **IP1 tunneling slot exhaustion** (startup + mid-uptime): orphaned tunnel
  slots from unclean shutdowns or other clients (LuxorPlay, a crashed prior
  instance) no longer accumulate and freeze the bus. Flushed both at
  startup and by the existing 4h periodic session refresh; slot-saturation
  diagnostics escalated to WARNING so they show up in default HA logs.
- **Zombie-tunnel watchdog**: detects a tunnel that reports CONNECTED but
  silently stops confirming telegrams (xknx's own heartbeat misses this),
  and forces a reconnect. Confirmed stable by Marcus since rc.9 — first
  clean run since tracking began 2026-06-17. Three follow-up bugs in the
  recovery path itself (a `_session_lock` deadlock, an `xknx.stop()` hang,
  and a cooldown sentinel that could skip the first detection after a
  restart) are all fixed.
- **H6 heat/cool sync across the shared mode-switch GA**: commanding one H6
  device from HA now updates every sibling device on the same physical
  switch. Went through two attempts — rc.9 registered a bus listener but it
  never fired for our own HA-triggered commands (xknx doesn't redeliver
  outgoing telegrams as incoming); the final fix explicitly fans the value
  out to siblings right after sending.
- **Wetterstation Helligkeit sensor labels (Vorne/Links/Rechts)**: went
  through three attempts based on Marcus' live comparisons against
  LuxorPlay — a naming-only rename (rc.5), a full 3-way rotation (rc.9)
  that turned out to overshoot by one step, and the final correction
  (only `HelligkeitMitte` maps to a different physical position; `Links`
  and `Rechts` were already correct).
- **Diagnostics export capped at 50 entities**: raised to 200 — installs
  with ~160 entities (Marcus') were silently losing most of the export.

## Validation

- Gated test suite green (`pytest -m "not enable_socket"`): 1033 collected.
- H6 sync and Wetterstation fixes verified against Marcus' real LXP export
  and his simulated sensor readings, not just synthetic test fixtures.
- Zombie-tunnel watchdog confirmed stable in the field since rc.9
  (2026-07-21 → 2026-07-26, no recurrence).
