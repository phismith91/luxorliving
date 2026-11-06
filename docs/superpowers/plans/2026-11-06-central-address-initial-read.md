# Plan: Stop initial reads on central/panic group addresses (#217)

**Goal:** Home Assistant restart must never switch lights off.
**Branch:** `fix/217-no-initial-read-on-central-addresses` (from `main`)
**Release:** `v1.2.3-rc.1`

## Evidence (from two debug logs attached to #217)

1. At startup a binary sensor ("T5", role `OnOff`) is mapped onto the central
   group addresses `5/1/248` (Panik) and `5/1/249` (ZentralAus).
2. `LuxorLivingBinarySensor.async_added_to_hass` calls
   `async_read_group_address(addr, is_initial=True)` for every binary sensor.
3. Every actuator that participates in central-off answers the read with
   `Response = 0`.
4. Within about one second the switch and dimmer actuators report their
   status GAs as `0`. Lights that were on are now off.
5. Same sequence in both logs. No outgoing write to any light address.

Open point: whether the actuator reacts to the Response (update flag) or to
the Read itself. It does not matter for the fix, since we stop sending the read.

## Why the tests did not catch it

| # | Gap | Evidence |
|---|-----|----------|
| 1 | Binary sensor tests mock the gateway and only assert `async_read_group_address(addr, is_initial=True)` was awaited. They pin the *bug* as expected behaviour. | `tests/test_binary_sensor_extended.py` (asserts at `2330`, `5120`) |
| 2 | No test uses an LXP that maps a sensor onto a `Panik`/`ZentralAus` GA. | none of the 5 local LXPs contains such a sensor; `Panik`/`ZentralAus` appear in tests only for parser/platform-detector/log-hygiene |
| 3 | Real-LXP tests are skipped in CI because `*.lxp` is gitignored. | `skipif(not ...exists())` in `tests/test_lxp_integration.py`; `Path("a private home path")` hardcoded in `tests/test_entity_mapper.py` |
| 4 | No test looks at the *side effect* of a read on the bus. Everything below the gateway is mocked, so "reading a central GA is dangerous" cannot surface. | `mock_knx_gateway` fixture is a bare MagicMock |
| 5 | Initial-read behaviour is tested per platform (what is requested), never globally (which GAs must never be read). | no gateway-level invariant |

Root cause on the design level: reads are treated as side-effect free. On a
bus with central functions that does not hold.

## Fix design

Root cause: a **command GA** (written *to* actuators) is treated as a
**status GA** (read *from* devices). Measured in log b: of 104 distinct GAs
read at startup, 102 are status/feedback groups (`x/1`, `x/3`, `x/4`, `x/5`
middle groups). The only two command GAs are `5/1/248` and `5/1/249`, both
reached through the T5 binary sensor. So the fix is not a Panik special case.

Rule: **never read a GA that is a command-role datapoint of any actuator**
(`OnOff`, `SchaltenOnOff`, `Dimmen%`, `UpDown`, `ZentralAus`, `Panik`, ...).
Derived from the parsed LXP, not from names or group numbers.

Two layers:

1. **Gateway (the rule).** `LuxorKNXGateway` gets the set of actuator
   command GAs at setup (same place as "Registered N known LXP addresses").
   `async_read_group_address` refuses those. Covers every platform and every
   read path (initial, polling, watchdog).
2. **Binary sensor (intent).** Do not request the initial read when its GA is
   in that set. Listener stays, so button presses still update state.

Why this is not a workaround: it removes the wrong assumption ("any GA a
sensor knows can be read") instead of hiding one address. Plain contact
sensors whose `OnOff` is not an actuator command GA keep their initial read.

The set is built where `Registered N known LXP addresses` is logged today.
No new config option.

Not in scope: changing how T5 is mapped (still a binary sensor), pollers other
than the initial read (check that none exists, see task 1).

## Tasks (TDD, one commit each)

1. **Audit reads.** List every caller of `async_read_group_address` and
   `GroupValueRead` (initial reads, polling, zombie watchdog, backpressure
   re-reads). Confirm none targets a central GA by another route.
2. **Synthetic fixture.** Build `tests/fixtures/central_off_sensor.lxp`
   (small, fully anonymised): 2 switch actuators with `ZentralAus`/`Panik`
   datapoints, 1 sensor `T5` whose `OnOff` equals the Panik GA. Commit it
   (un-ignore only `tests/fixtures/*.lxp`). This also gives CI a real-LXP test
   without private data.
3. **RED: gateway test.** Real `LuxorKNXGateway`, fake xknx. Reading a GA in
   the never-read set sends no telegram. Fails today.
4. **RED: end-to-end test.** Fixture LXP, parser, mapper, setup of all
   platforms, assert no `GroupValueRead` is sent to the central GAs, while
   normal status GAs are still read.
5. **RED: change the existing binary sensor assertions** so they no longer
   pin reads for central GAs; keep them for normal GAs.
6. **GREEN:** implement gateway guard and binary sensor skip.
7. **Regression guard (invariant test).** Parametrised over all mapped
   entities from every LXP available (fixture always, local ones if present):
   no entity may request an initial read on a Panik/ZentralAus GA.
8. **Real-data check (local only).** Entity-count diff main vs branch on the
   five local LXPs. Expected: identical counts.
9. **Docs/release:** CHANGELOG, `RELEASE_NOTES_v1.2.3.md` (pre-release
   header), README test badge, `check_version_refs.sh`, `pyproject.toml`
   version = manifest version (see release runbook).
10. **Issue reply** (friendly, English) after the user approves. Ask lorenzl to
    install rc.1 and to send a fresh debug log. Do not close the issue.

Gate before PR: full gated suite, `pre-commit run --all-files`,
`pytest --collect-only -q | tail` for the badge count.

## Risks

- A deny-list by role misses a GA that is central by wiring but has no
  `ZentralAus`/`Panik` role (for example scene or custom central GAs).
  Mitigation: task 1 audit, and ask the reporter for the LXP.
- The T5 mapping in the reporter's LXP is only inferred from the log
  (`OnOff` → 10744/10745). Task 2 fixture must be checked against his real
  export before merge.
- Skipping the initial read means T5 shows "off" until the first button
  press. That is correct for a momentary button.

---

# Plan: Anonymise the repository

## Findings (tracked files in HEAD)

| Category | Where | Action |
|----------|-------|--------|
| Real Tailscale IP the Tailscale host IP | `.claude/napkin.md`, `.github/copilot/*` (3), `docs/INCIDENT_RESPONSE_RUNBOOK.md`, `docs/RELEASE_OPERATIONS.md`, `CHANGELOG.md:1112`, `docs/superpowers/plans/*` | replace by `<HA_HOST>` / `ha.example.invalid` |
| Reporter's first name, many places | `CHANGELOG.md` (13), `README.md`, `docs/releases/RELEASE_NOTES_v1.2.1/1.2.2`, `knx_gateway.py` comments (5), `entity_mapper.py`, `tests/test_knx_gateway.py` (7), `tests/test_entity_mapper_extended.py`, `docs/superpowers/plans/2026-07-11-*` | replace by "a reporter" / "field log" and keep the date |
| Customer/project names in LXP context (`large-climate`, a family-project name) | `CHANGELOG.md`, release notes v1.1.14, `docs/ARCHITECTURE_DECISION.md`, `tests/test_lxp_integration.py` (17), `tests/test_entity_mapper*.py`, `tests/test_integration.py` | rename to neutral labels (`LXP_LARGE_CLIMATE`, ...) |
| Hardcoded private path `a private home path` | `tests/test_entity_mapper.py:17` | remove, use the new fixture |
| Vendor PDFs tracked despite `.gitignore` | `docs/LUXORliving_API_Documentation_EN.pdf`, `docs/weinzierl-777-...pdf` | `git rm --cached`, check licence |
| Test IPs (`192.168.1.x`, `10.0.0.x`, `172.16.0.5`) | tests, config_flow | RFC1918 placeholders, leave, or move to `192.0.2.x` (RFC 5737) |
| Maintainer GitHub handle `phismith91` | CODEOWNERS, manifest, README | public by design, leave |

Not tracked in HEAD and never in history (checked with
`git log --all --diff-filter=A`): `*.lxp`, `*.log`, HA diagnostic zips,
`.knxprod`. They are in `.gitignore` and stay local. The local files in
`docs/` (five LXPs, ~10 logs) must never be added.

Real `.lxp` contents (device names, serials such as the weather-station
serial) are only referenced by name, not copied.

## Plan

1. Branch `chore/anonymise-repo`. Separate from the #217 fix, so the fix stays
   reviewable.
2. Script `scripts/anonymise_check.sh` (also a CI step): fails if tracked files
   match the real Tailscale IP, a deny-list of names (kept in a gitignored
   local file, not in the repo), `/home/<user>/` paths, or tracked `*.lxp`,
   `*.log`, `*.zip`.
3. Mechanical replacements per table above, one commit per category.
4. Replace all LXP references in tests by the synthetic fixtures. Real-LXP
   tests stay, but read the path from an env var (`LUXOR_TEST_LXP_DIR`) and
   skip when unset. No private filenames in the repo.
5. Remove the two PDFs from the index.
6. Update `.gitignore` for `tests/fixtures/*.lxp` exception, add
   `docs/*.log`.

## Decision needed: git history

HEAD can be cleaned with a normal PR. The **history** still contains the IP,
the names and the old PDFs. Options:

- **A. HEAD only (recommended default).** Quick, no force-push. IP is a
  Tailscale address (not reachable from the internet), names are first names
  only. Lowest risk.
- **B. Rewrite history** (`git filter-repo`, force-push main, re-tag).
  Breaks every clone, open PR, existing tags and release assets, and HACS
  users pinned to tags. Only worth it if the PDFs' licence or the names are a
  real problem.

Also check: GitHub issues and comments quote the names and attach logs with
the reporter's LAN IPs. Those live on GitHub and are not touched by either
option. Edit or delete them manually if wanted.
