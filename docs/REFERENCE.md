# LUXORliving — Full Reference

This document is the **single source of truth** for all options, platforms, endpoints, and behaviors of the LUXORliving integration. The persona guides ([User](USER_GUIDE.md), [Advanced](ADVANCED_GUIDE.md), [Developer](DEVELOPER_GUIDE.md)) are derived from this document.

---

## System Requirements

| Requirement | Value |
| --- | --- |
| Home Assistant | ≥ 2025.12.0 |
| Python | ≥ 3.12 |
| Gateway hardware | Theben LUXORliving IP1 (BAOS 777) |
| Project file | LXP file exported from Theben LUXORPlug software |
| Network | Gateway reachable on port 3671 (KNX/IP) and port 443 (HTTPS REST) |

---

## Configuration Options

### Initial Setup (Config Flow)

Configured once during integration setup. Accessible via **Reconfigure** afterwards.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `host` | string | — | IP address of the LUXORliving IP1 gateway |
| `username` | string | `admin` | BAOS REST API username |
| `password` | string | `admin` | BAOS REST API password |
| `connection_type` | select | `tunneling` | KNX/IP connection mode: `tunneling` (recommended) or `routing` |
| `lxp_file` | file / path | — | LXP project file (upload or absolute path e.g. `/config/luxor/project.lxp`) |

### Options (Reconfigurable at Any Time)

Accessible via Settings → Devices & Services → LUXORliving → **Configure**.

#### Standard Settings

| Option | Type | Default | Range | Description |
| --- | --- | --- | --- | --- |
| `scan_interval` | integer | `30` | 5–300 s | How often HA polls the gateway for entity state updates. Lower = more responsive, higher = less network load. With Push Webhook active, 60–120 s is sufficient. |
| `simulation_mode` | boolean | `false` | — | Runs the integration without a real gateway. Useful for testing automations and dashboards on hardware-free setups. |
| `allow_diagnostics` | boolean | `false` | — | Controls what the HA diagnostics export includes. See [Diagnostics](#diagnostics-export). |
| `log_level` | select | `info` | debug / info / warning / error | Verbosity of integration logs in the HA log file. Use `debug` for troubleshooting. |
| `discovery_timeout` | float | `2.0` | 0.5–10.0 s | Timeout for KNX group address auto-discovery during startup. Increase if entities are missing on slow networks. |

#### Advanced: Push Webhook (collapsed by default)

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `push_ws_url` | URL | — | WebSocket URL of an external KNX forwarder. HA opens a client connection and receives push updates from this URL. Leave empty to disable. |
| `push_auth_method` | select | `none` | Authentication method for incoming push requests: `none`, `token`, `bearer`, `hmac`. |
| `push_token` | password | — | Shared secret used for `token` and `hmac` authentication. |
| `push_ws_token` | password | — | Bearer token sent in the `Authorization` header when connecting to `push_ws_url`. |

---

## Supported Platforms

| Platform | HA Entity Type | KNX DPT | Notes |
| --- | --- | --- | --- |
| Light (switching) | `light` | DPT 1.001 | On/off only |
| Light (dimming) | `light` | DPT 1.001 + 5.001 | On/off + brightness 0–100% |
| Switch | `switch` | DPT 1.001 | Generic on/off |
| Cover (shutter) | `cover` | DPT 1.008 + 5.001 | Open/close/stop + position |
| Cover (blind with tilt) | `cover` | DPT 1.008 + 5.001 × 2 | Position + tilt |
| Climate | `climate` | DPT 9.001 + 1.001 | Setpoint + heating valve |
| Binary Sensor | `binary_sensor` | DPT 1.x | Motion, window contacts, buttons |
| Sensor | `sensor` | DPT 9.x | Temperature, humidity, CO2, brightness, wind |

Entity names, room assignments, and device grouping are derived directly from the LXP project file — no manual YAML configuration is needed.

---

## Compatible Devices

### Tested Theben KNX Hardware

**Switching Actuators**

| Model | Channels | HA Platform |
| --- | --- | --- |
| S 4 | 4 | switch / light |
| S 8 | 8 | switch / light |
| S 16 | 16 | switch / light |

**Dimming Actuators**

| Model | Channels | HA Platform |
| --- | --- | --- |
| D 2 | 2 | light (dimmable) |
| D 4 | 4 | light (dimmable) |

**Blind / Shutter Actuators**

| Model | Channels | HA Platform |
| --- | --- | --- |
| J 4 | 4 | cover |
| J 8 | 8 | cover |

**Heating Actuators**

| Model | Channels | HA Platform |
| --- | --- | --- |
| H 6 | 6 | climate |

**Sensors & Inputs**

| Model | Type | HA Platform |
| --- | --- | --- |
| KNX weather station | Multi-sensor | sensor (temperature, wind, brightness) |
| Motion detector | Binary | binary_sensor |
| Binary input module | Multi-channel | binary_sensor |

> Other Theben KNX devices using standard DPT types will typically work. If a device is not listed, [open an issue](https://github.com/phismith91/luxorliving/issues) with your LXP file details.

---

## Push Webhook

The integration exposes an HTTP webhook and optionally opens a WebSocket client for receiving external KNX state updates in real time — reducing dependency on polling.

### Incoming Webhook

```
POST /api/luxor_living/push
Content-Type: application/json

{
  "entry_id": "<config_entry_id>",
  "address": "1/2/3",
  "value": true,
  "value_type": "binary"
}
```

**Supported `value_type` values:** `binary`, `percent`, `temperature`, `float`

**Authentication (configured per integration options):**

| Method | Header | Description |
| --- | --- | --- |
| `none` | — | No authentication |
| `token` | `X-LUXOR-PUSH-TOKEN: <secret>` | Static shared secret |
| `bearer` | `Authorization: Bearer <token>` | Bearer token |
| `hmac` | `X-LUXOR-PUSH-SIGNATURE: <hex>` | HMAC-SHA256 of JSON body using configured secret |

### WebSocket Client

When `push_ws_url` is configured, HA opens a persistent WebSocket connection to the external URL on startup. Messages received are processed identically to incoming webhook payloads. The `push_ws_token` is sent as `Authorization: Bearer <token>` during the handshake.

---

## REST Endpoints

Internal endpoints exposed by the integration on the HA HTTP server:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/luxor_living/health` | Health check: gateway status, coordinator state |
| `POST` | `/api/luxor_living/push` | Receive external KNX state update |
| `POST` | `/api/luxor_living/benchmark` | Run internal performance benchmark suite |

---

## Diagnostics Export

Controlled by the `allow_diagnostics` option.

**Disabled (default):** The HA diagnostics download (Settings → Integrations → Download Diagnostics) returns only: entry ID, title, version, domain, state, options. No runtime data.

**Enabled:** Full export including:

- KNX gateway connection state, simulation mode, host, datapoint count
- All discovered entities (up to 50): name, platform, type, datapoints, parameters
- Entity summary by platform
- Device list from LXP project: name, serial, actuators/sensors with parameters
- Coordinator status: last update success, last exception, update interval

Passwords and LXP file paths are always `**REDACTED**` regardless of this setting.

---

## Rate Limiting

The integration enforces rate limiting to prevent unintended "light shows" from runaway automations or UI double-clicks:

- **Threshold:** 5 or more on/off commands within 1 second to the same entity triggers the rate limit
- **Effect:** Further commands are blocked until the rate resets
- **Recovery:** Automatic after the rate window expires

---

## Circuit Breaker

The KNX gateway connection is protected by a circuit breaker:

- **Opens** after repeated consecutive connection failures
- **Effect:** Entity commands are rejected immediately (no timeout wait)
- **Recovery:** Automatic retry after a cooldown period; circuit closes on successful connection

---

## Overrides

Custom entity configuration is possible via a YAML overrides file. This allows renaming entities, changing device classes, or adjusting DPT mappings without modifying the LXP file.

See [`docs/luxor_living_overrides.example.yaml`](luxor_living_overrides.example.yaml) for the full format reference.

---

## Use Cases

| Use Case | How |
| --- | --- |
| **Whole-home KNX automation** | All KNX lights, covers, climate, and sensors from your LXP project become HA entities. Automate them with standard HA automations, scenes, and scripts. |
| **KNX + non-KNX devices in one system** | Control KNX lights alongside Zigbee, Z-Wave, or cloud devices in a single HA dashboard and automation engine. |
| **Wake-up / sleep scenes** | Combine dimmer brightness ramp-ups, cover positions, and thermostat setpoints in a single HA scene triggered by an alarm or button. |
| **Presence-based automation** | Use KNX motion detectors (binary_sensor) to trigger lights, covers, or notifications — optionally combined with other presence sensors. |
| **Weather-reactive covers** | Drive KNX blind actuators based on KNX weather station data (wind, rain) or external HA weather integrations. |
| **Energy monitoring** | Expose KNX sensor values (temperature, CO2, brightness) as HA sensors and use the HA Energy Dashboard or long-term statistics. |
| **Simulation & testing** | Enable Simulation Mode to test automations and dashboards without a real gateway — useful during HA setup or when the gateway is offline. |
| **Mobile and remote control** | All KNX entities are available in HA's mobile apps and via the HA Cloud (Nabu Casa) without exposing the KNX gateway directly to the internet. |

---

## Known Limitations

See the [Advanced Guide — Known Limitations](ADVANCED_GUIDE.md#known-limitations) for a full list.

---

## Dependencies

| Library | Version | Purpose |
| --- | --- | --- |
| `xknx` | ≥ 3.13.0 | KNX/IP communication (tunneling, routing, telegram handling) |
| `defusedxml` | ≥ 0.7.1 | Safe XML parsing of LXP project files |
