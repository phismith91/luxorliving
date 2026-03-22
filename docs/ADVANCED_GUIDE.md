# Advanced Guide — LUXORliving KNX Integration

**Audience:** Power users who want to tune performance, set up push updates, customize entity behavior, or troubleshoot at a deeper level. Assumes the integration is already installed and working.

---

## Full Options Reference

All options are accessible via **Settings → Devices & Services → LUXORliving → Configure**.

The options form has two sections: **Standard** (visible by default) and **Push Webhook** (collapsed, expand to configure).

### Standard Options

| Option | Default | Range | Notes |
| --- | --- | --- | --- |
| `scan_interval` | `30` s | 5–300 | Polling interval. With push active, 60–120 s is a good value. Below 10 s puts noticeable load on the gateway REST API. |
| `simulation_mode` | `false` | — | Full dry-run: no real KNX telegrams sent. State changes are accepted and stored in memory only. |
| `allow_diagnostics` | `false` | — | See [Diagnostics Export](#diagnostics-export) below. |
| `log_level` | `info` | debug / info / warning / error | Applied at runtime without restart via the integration's log handler. |
| `discovery_timeout` | `2.0` s | 0.5–10.0 | KNX GroupValueRead timeout during startup. On slow or congested KNX buses, increase to 4–5 s. |

### Push Webhook Options

| Option | Default | Notes |
| --- | --- | --- |
| `push_ws_url` | — | WebSocket URL to an external KNX forwarder (e.g. `ws://192.168.1.100:8765`). HA connects as client on startup. |
| `push_auth_method` | `none` | Auth method for incoming HTTP push requests. Does not apply to the WS client. |
| `push_token` | — | Used as the shared secret for `token` and `hmac` auth. |
| `push_ws_token` | — | Sent as `Authorization: Bearer <token>` when connecting to `push_ws_url`. |

---

## Push Webhook Setup

The push webhook allows external systems (KNX gateways, cloud services, forwarders) to push KNX state updates directly into HA instead of waiting for the polling interval.

### When to Use

- You have a KNX forwarder or event bridge that can POST or stream KNX values
- You want near-instant entity updates (< 1 s latency vs 30 s polling)
- You want to reduce load on the gateway REST API

### Incoming HTTP Webhook

The integration registers an HTTP endpoint at `/api/luxor_living/push`:

```bash
curl -X POST http://your-ha:8123/api/luxor_living/push \
  -H "Content-Type: application/json" \
  -d '{
    "entry_id": "<your_config_entry_id>",
    "address": "1/2/3",
    "value": true,
    "value_type": "binary"
  }'
```

**`value_type` options:** `binary`, `percent`, `temperature`, `float`

**Find your `entry_id`:** Settings → Devices & Services → LUXORliving → click the integration → the URL contains the entry ID.

### Authentication

Configure `push_auth_method` in the options:

| Method | How it works |
| --- | --- |
| `none` | No check — only use on a trusted internal network |
| `token` | Sender must include `X-LUXOR-PUSH-TOKEN: <your_token>` header |
| `bearer` | Sender must include `Authorization: Bearer <your_token>` header |
| `hmac` | Sender must include `X-LUXOR-PUSH-SIGNATURE: <hmac-sha256-hex>` — signature over the JSON body using `push_token` as the key |

### WebSocket Client

Set `push_ws_url` to have HA maintain a persistent connection to an external WebSocket server. The server sends JSON messages in the same format as the HTTP webhook (without `entry_id` — the integration uses the one from config).

The WS client reconnects automatically on disconnect.

---

## Performance Tuning

### Polling vs Push

| Mode | Latency | Gateway Load | Setup complexity |
| --- | --- | --- | --- |
| Polling only (default) | Up to `scan_interval` | Moderate | None |
| Push + polling (hybrid) | < 1 s for pushed states | Low | Requires forwarder |

### Recommendations

- **Default setup (no forwarder):** `scan_interval = 30` is fine for most homes.
- **Large LXP project (50+ entities):** Consider `scan_interval = 60`. Startup reads all states in parallel (~30 ms per entity), so 50 entities ≈ 1.5 s startup time.
- **With push webhook:** Set `scan_interval = 120`. Push handles real-time updates; polling is just a safety net for missed telegrams.
- **Circuit breaker:** If your gateway goes offline repeatedly, the circuit breaker opens and commands are rejected immediately. It auto-recovers. No configuration needed.

---

## Rate Limiting

The integration prevents runaway automations or UI double-clicks from flooding the KNX bus:

- **Limit:** 5 or more on/off commands to the same entity within 1 second
- **Result:** Further commands blocked until the rate window resets
- **No configuration required** — always active

---

## Overrides

Override entity configuration without modifying the LXP file. Useful for renaming entities, changing device classes, or adjusting DPT mappings.

Create a YAML file at the path you specify in integration options, using the format from the example:

```bash
cp docs/luxor_living_overrides.example.yaml /config/luxor_living_overrides.yaml
```

See [`luxor_living_overrides.example.yaml`](luxor_living_overrides.example.yaml) for all supported keys.

---

## Sensor Platform

Sensors are auto-detected from the LXP project. Supported types:

| LXP role | HA sensor device class | Unit |
| --- | --- | --- |
| Temperature | `temperature` | °C |
| Humidity | `humidity` | % |
| CO2 | `carbon_dioxide` | ppm |
| Brightness | `illuminance` | lx |
| Wind speed | `wind_speed` | m/s |
| Presence / motion | (binary_sensor) | — |

See [Sensor Platform](SENSOR_PLATFORM.md) for detailed role detection logic, override options, and attribute reference.

---

## Diagnostics Export

Enable `allow_diagnostics` in options, then download via **Settings → Devices & Services → LUXORliving → ⋮ → Download diagnostics**.

The export includes:

- **Gateway:** connected state, host, simulation mode, datapoint count
- **Entities:** all discovered entities (up to 50) with name, platform, type, KNX datapoints, and LXP parameters
- **Devices:** full device list from LXP with actuator/sensor parameters
- **Coordinator:** last update success/failure, update interval
- **Entry:** config entry metadata, options (passwords always `**REDACTED**`)

Attach the downloaded JSON when opening a GitHub issue for faster debugging.

---

## Multiple Gateways

Each LUXORliving IP1 gateway is a separate integration entry:

1. Settings → Devices & Services → Add Integration → **LUXORliving** → configure gateway 1
2. Repeat for gateway 2

Each entry has its own options, entities, and push webhook configuration. Entry IDs are independent.

---

## Advanced Troubleshooting

**Check the health endpoint:**

```bash
curl http://your-ha:8123/api/luxor_living/health
```

Returns gateway connection state, coordinator status, and entity count.

**Run the benchmark:**

```bash
curl -X POST http://your-ha:8123/api/luxor_living/benchmark
```

Measures entity creation time, GroupValueRead latency, and coordinator cycle time.

**Enable debug logging:**

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.luxor_living: debug
```

**Common advanced issues:**

| Symptom | Cause | Fix |
| --- | --- | --- |
| Entities missing after restart | Discovery timeout too short | Increase `discovery_timeout` to 4–5 s |
| Push webhook returns 401 | Wrong auth header or token | Verify `push_auth_method` and header name match |
| WS client disconnects repeatedly | Forwarder not ready at HA start | Normal — WS client reconnects automatically |
| Circuit breaker stays open | Gateway unreachable for extended period | Check gateway IP, port 3671 reachable, BAOS service running |
| Performance very slow | Large LXP + low `scan_interval` | Increase `scan_interval` or enable push |

---

## Known Limitations

| Limitation | Details |
| --- | --- |
| **LXP file required** | The integration cannot discover entities without a valid `.lxp` project file exported from Theben LUXORPlug. There is no way to auto-generate entity mapping without this file. |
| **KNX/IP only** | Only KNX/IP (tunneling or routing) is supported. USB or RS232 KNX interfaces are not supported. |
| **BAOS 777 gateway** | Tested exclusively with the Theben LUXORliving IP1 (Weinzierl BAOS 777). Other KNX/IP gateways may work but are untested. |
| **State latency (polling)** | Without push webhook, state updates arrive at most every `scan_interval` seconds. Physical KNX switch presses are not reflected until the next poll unless push is configured. |
| **Entity names are fixed** | Entity names come from the LXP file and cannot be changed in the integration — rename them in HA's entity registry instead. |
| **Cover tilt precision** | Tilt position is rounded to 1% steps due to KNX DPT 5.001 resolution. |
| **No ETS project support** | Only LXP files (Theben LUXORPlug export) are supported. ETS `.knxproj` files are not parsed. |
| **Multiple gateways** | Multiple LUXORliving entries are supported, but each gateway needs its own LXP file and config entry. Cross-gateway automations work normally via HA. |

---

## Further Reading

- [Full Options Reference](REFERENCE.md)
- [Sensor Platform Details](SENSOR_PLATFORM.md)
- [Dashboard Examples](DASHBOARD_EXAMPLES.md) — including push webhook automation examples
- [Developer Guide](DEVELOPER_GUIDE.md) — if you want to extend or contribute
