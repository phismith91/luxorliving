# Release Notes — v1.2.1

> Pre-release: `v1.2.1-rc.4`.

## Added

- **H6 cooling-mode support**: H6 climate entities now support cooling in
  addition to heating when the `UmschaltenHeitzenKühlen` (heating/cooling
  mode-switch) datapoint is present. Marcus' setup with ION8 T10 mode-switch
  controlling H6 devices (511, 512, 513) is fully supported. Mode-switch
  control sends a binary telegram: 1 for heating, 0 for cooling.

## Fixed — IP1 tunneling slot exhaustion

Unclean HA shutdowns (or any other client crashing mid-session, e.g.
LuxorPlay) leave a stale tunneling slot occupied on the IP1. The IP1 only
has a handful of slots (observed max 4); once they fill up the whole KNX
bus freezes and stops confirming telegrams, without HA ever seeing a clean
disconnect. Recovery previously required a physical restart of the KNX
system — reported as issue #141 and reproduced again in a 2026-06-30 log
from Marcus (~30h into one HA uptime, continuous `L_DATA_CON` confirmation
timeouts, no disconnect ever logged).

Three changes close this:

- **rc.1 — startup flush**: `connect()` now calls `disable_tunneling()`
  (a global, device-level operation) before `enable_tunneling()`, clearing
  any slot orphaned by a previous crashed instance every time HA starts up.
- **rc.4 — periodic flush**: the existing 4h proactive
  `_session_refresh_loop` — whose whole purpose is to catch slot
  saturation "even when XKNX never detects a disconnect" — only cycled its
  own REST session. It now also calls `disable_tunneling()`, so slots
  orphaned by *other* clients get cleared during a single long uptime too,
  not just at the next HA restart.
- **rc.4 — visible diagnostics**: the slot-status check (`IP1 tunneling
  slots before flush: X/Y connected`) used to log at INFO, which HA
  doesn't show by default — it was invisible in every real-world bug
  report, including Marcus' log (0 INFO lines total). It now logs at
  WARNING once slots are at or over capacity, so the precursor to a freeze
  shows up in a standard log export.

## Validation

- Gated test suite green (`pytest -m "not enable_socket"`): 939 passed.
- Awaiting Marcus' re-validation on real IP1 hardware after upgrading.
