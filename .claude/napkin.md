# Napkin Runbook — LUXORliving

## Curation Rules

- Re-prioritize on every read. Keep recurring, high-value notes only.
- Max 10 items per category. Each item includes date + "Do instead".

---

## Execution & Validation (Highest Priority)

1. **[2026-05-16] Check open PRs before creating a new branch** Regression risk:
   if a related PR is open but unmerged, the new branch won't contain its
   changes (H6 climate regression in v1.1.6 was caused by PR #127 never merging
   before PR #128 branched off `main`). Do instead: `gh pr list --state open`
   before every `git checkout -b`. For any PR touching the same files, merge it
   first or explicitly cherry-pick its commits.

2. **[2026-05-16] README test badge must match actual CI test count** Release
   Checks gate validates it — any mismatch fails CI. Do instead: after adding
   tests, run `python -m pytest tests/ -q --co -m "not enable_socket" | tail -3`
   locally to get the count, then update the badge in `README.md` before
   pushing.

3. **[2026-05-16] Tag must point to latest HEAD for release workflow to use
   updated CI config** When a tag push triggers the release workflow, GitHub
   uses the workflow file from the tagged commit — not from `main` or the branch
   tip. Do instead: if the workflow was fixed after the tag was pushed, delete
   the old tag (`gh release delete --cleanup-tag`, then
   `git push origin :refs/tags/vX`) and retag at the new HEAD. Repository rules
   may block reusing the same tag name — bump to the next rc number (rc.2 →
   rc.3).

4. **[2026-05-16] `gh run rerun` replays the old workflow snapshot** Re-running
   a failed workflow run does not pick up new workflow file changes pushed after
   the original tag. Do instead: delete tag + release, retag at new HEAD, push
   tag — this triggers a fresh run using the updated workflow.

---

## Shell & Command Reliability

1. **[2026-05-15] SSH config has invalid entries — always use `-F /dev/null`**
   Do instead: `ssh -F /dev/null phil@100.97.159.88 "cmd"` and
   `GIT_SSH_COMMAND='ssh -F /dev/null' git push`.

2. **[2026-05-16] Local venv is Python 3.12; CI uses Python 3.14** Some tests
   fail locally (MockConfigEntry.runtime_data, thread cleanup) that pass on CI.
   These are environment differences, not real bugs. Do instead: trust CI as
   authoritative test runner; run local suite only for fast iteration. For a new
   venv: `python3.14 -m venv .venv`.

3. **[2026-05-16] `pre-commit run --all-files` before every commit** CI runs the
   exact same checks (black, isort, flake8, bandit, prettier). Do instead: never
   skip pre-commit — CI will fail identically.

---

## Release Process

1. **[2026-05-16] PR-only workflow — never push directly to `main`** Do instead:
   always open a PR; Release Manager merges to main.

2. **[2026-05-16] Open PRs to review before each release (as of 2026-05-16)**
   - PR #128 `fix/cover-inversion-regen-bwm` — OPEN, RC phase, merge when CI
     green
   - PR #127 `fix/climate-entity-detection` — OPEN, superseded by #128 (climate
     fix cherry-picked in), close after #128 merges
   - PR #125 `types-requests bump` — safe to merge independently
   - PR #126 `mypy 2.0.0` — NOT recommended this cycle (breaking changes)
   - PRs #68–71 — old Copilot drafts, safe to ignore Do instead: update this
     list at the start of every release session.

3. **[2026-05-16] Release workflow uses Python 3.14 (updated from 3.13)**
   `homeassistant>=2026.4.4` requires Python >=3.14.2. Do instead: if
   requirements bump HA version, verify release workflow python-version matches.

---

## Domain Behavior Guardrails

1. **[2026-05-16] KNX Höhe% convention is inverted vs HA** KNX: 0 = fully open,
   100 = fully closed. HA: 0 = closed, 100 = open. Do instead: always apply
   `100 - value` on both read (`_handle_position_update`) and write
   (`async_set_cover_position`).

2. **[2026-05-16] Climate entity detection requires two conditions** H6 heating
   actuator: `heizungsart` param + `Istwert` + `Sollwert` datapoints. RTR
   thermostat: `activateRTR=1` param + `Istwert` + (`Sollwert` or
   `status@Sollwert`). R718 standalone thermostat: `Istwert` + `Sollwert` +
   `status@Sollwert` (no `activateRTR`). Do instead: when climate stops working,
   check `entity_mapper._map_sensor` and `_map_actuator` first.

3. **[2026-05-16] KNX listeners must be registered in `async_added_to_hass`, not
   `__init__`** `__init__` may run in an executor (thread-unsafe for
   `async_write_ha_state`). Do instead: always put
   `knx_gateway.register_listener(...)` + initial read in `async_added_to_hass`;
   unregister in `async_will_remove_from_hass`.

4. **[2026-05-16] knxprod DB ist die autoritative Gerätedatenbank** Alle 57
   LUXORliving-Geräte + vollständige Datapoint/DPT-Definitionen in
   `docs/LUXORliving_ETS5_KNX_DB_V2_23_2510.knxprod_FILES/`. Issue #131 trackt
   den Plan, `appId` aus LXP gegen Catalog.xml abzugleichen statt Parameter-
   Heuristiken. Do instead: bevor neue Geräteerkennung per Heuristik
   implementiert wird — erst in `M-0048/M-0048_A-<appId>.xml` nachschauen.

5. **[2026-05-16] Debounce tasks must be cancelled on `async_disconnect`**
   Lingering `asyncio.Task` from `_execute_debounced_callbacks` causes HA test
   framework failures. Do instead: `async_disconnect` cancels `_debounce_task` —
   don't remove that line.
