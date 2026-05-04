# Release Notes — v1.1.4

## Fixed

- **Cover and climate entities crash on setup** (`AttributeError: 'MappedEntity' object has no attribute 'get'`).
  `MappedEntity` is a dataclass — switched from dict `.get()` calls to direct attribute access
  (`.datapoints`, `.unique_id`, `.name`, `.device_id`, `.device_name`).

- **KNX listener lifecycle**: Registration moved from `__init__` (runs in a thread executor) to
  `async_added_to_hass`, preventing thread-safety issues and premature `async_write_ha_state()` calls.
  Added `async_will_remove_from_hass` to clean up listeners on integration reload.

- **Temperature DPT encoding**: Removed incorrect ×100/÷100 integer encoding. The KNX gateway
  already decodes DPT 9.001 as Python `float` — temperature values are now passed directly.

- **`StopStep` → `StepStop`** typo in `platform_detector.py` `ROLE_TO_PLATFORM` mapping.

- **`device_info`**: Removed non-existent `device_model`/`sw_version` fields; using `model="LUXORliving"`.

- **Gateway API alignment**: Cover and climate now use `async_send_telegram` / `async_read_group_address`
  (listener-driven pattern), consistent with light and switch platforms.
