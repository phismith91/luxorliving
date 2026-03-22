# User Guide — LUXORliving KNX Integration

**Audience:** Home Assistant users who want to connect their Theben LUXORliving KNX system to HA. No prior KNX or programming knowledge required.

---

## What You Need Before Starting

- **Theben LUXORliving IP1 gateway** (BAOS 777) connected to your network
- **LXP project file** — exported from the Theben LUXORPlug software on your PC
- **Gateway IP address** — find it in your router's DHCP list or via the LUXORPlug software
- **Gateway credentials** — default is `admin` / `admin` (change this if you already secured your gateway)
- **Home Assistant ≥ 2025.12.0** — check Settings → About

---

## Installation

### Via HACS (recommended)

1. Open **HACS** in the HA sidebar
2. Go to **Integrations** → click the three-dot menu (⋮) → **Custom repositories**
3. Enter `https://github.com/phismith91/luxorliving` and select **Integration**
4. Click **Add**, then search for **LUXORliving** and click **Download**
5. **Restart Home Assistant**

### Manual Installation

1. Download the [latest release](https://github.com/phismith91/luxorliving/releases/latest)
2. Copy the `custom_components/luxor_living` folder into your HA config directory (same level as `configuration.yaml`)
3. **Restart Home Assistant**

---

## Initial Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **LUXORliving** and click it
3. Fill in the setup form:

   | Field | What to enter |
   | --- | --- |
   | Host | IP address of your gateway (e.g. `192.168.1.50`) |
   | Username | `admin` (or your custom username) |
   | Password | `admin` (or your custom password) |
   | Connection type | **Tunneling** (recommended for most setups) |
   | LXP file | Upload the file or enter the full path (e.g. `/config/luxor/myproject.lxp`) |

4. Click **Submit**

HA will connect to the gateway and create entities for everything in your LXP project. This takes a few seconds.

---

## What Gets Created

Entities are named and grouped based on your LXP project file:

- **Lights** — all dimmable and switching light circuits
- **Covers** — shutters, blinds (with tilt if configured in LXP)
- **Climate** — heating zones with setpoint and valve control
- **Sensors** — temperature, humidity, CO2, brightness, wind speed (if connected)
- **Binary Sensors** — motion detectors, window contacts, push buttons
- **Switches** — sockets and generic on/off outputs

Entities are grouped into **devices** by room and function, matching your LXP project structure.

---

## Basic Settings

Open **Settings → Devices & Services → LUXORliving → Configure** to adjust:

| Setting | Default | What it does |
| --- | --- | --- |
| Scan interval | 30 s | How often HA asks the gateway for current states. 30 s is a good balance. |
| Simulation mode | Off | Runs without real hardware — useful for testing. |
| Allow diagnostics | Off | When on: lets you download a full diagnostic report for bug reports. When off: only basic info is exported. |
| Log level | Info | Set to `debug` if you need detailed logs for troubleshooting. |
| Discovery timeout | 2.0 s | How long the gateway search waits. Increase only if entities are missing at startup. |

---

## Compatible Devices

The following Theben KNX devices are tested and fully supported:

| Device | Type | HA entities created |
| --- | --- | --- |
| S 4 / S 8 / S 16 | Switching actuator | Switch or Light (based on LXP config) |
| D 2 / D 4 | Dimming actuator | Light with brightness control |
| J 4 / J 8 | Blind / shutter actuator | Cover (with position and optional tilt) |
| H 6 | Heating actuator | Climate (setpoint + valve) |
| Motion detector | Binary input | Binary Sensor |
| Binary input module | Binary input | Binary Sensor |
| KNX weather station | Multi-sensor | Sensor (temperature, wind, brightness) |

Other Theben KNX devices using standard DPT types will typically work as well.

---

## Automations

The integration works with all standard HA automations. Common examples:

```yaml
# Turn on lights when motion is detected
automation:
  - alias: "Motion → Living room lights"
    trigger:
      - platform: state
        entity_id: binary_sensor.bewegungsmelder_wohnzimmer
        to: "on"
    action:
      - service: light.turn_on
        target:
          entity_id: light.deckenleuchte_wohnzimmer
```

See [Automation Recipes](AUTOMATIONS.md) for a full collection of ready-to-use examples covering lights, covers, climate, motion, and scenes.

---

## Dashboard

Add your LUXORliving entities to any Lovelace dashboard:

```yaml
type: entities
title: Living Room
entities:
  - entity: light.deckenleuchte_wohnzimmer
  - entity: cover.jalousie_wohnzimmer
  - entity: sensor.temperatur_wohnzimmer
  - entity: binary_sensor.bewegungsmelder_wohnzimmer
```

See [Dashboard Examples](DASHBOARD_EXAMPLES.md) for room dashboards, energy views, and mobile layouts including Mushroom and Button Card examples.

---

## Troubleshooting

| Problem | Solution |
| --- | --- |
| Integration not loading | Check HA logs: Settings → System → Logs, filter for `luxor_living` |
| Gateway unreachable | Verify the IP address and that port 3671 is reachable from HA |
| Entities not created | Check that the LXP file contains group addresses; try re-uploading it |
| LXP file not found | Use the absolute path: `/config/luxor/project.lxp` (not a relative path) |
| Tunneling fails | Try **Routing** mode, or check BAOS authentication credentials |
| Entities missing after restart | Increase **Discovery timeout** in Options (Settings → Configure) |
| Slow startup | Normal for large LXP files — the integration reads all group addresses on start |

**Enable debug logging** (add to `configuration.yaml`):

```yaml
logger:
  default: info
  logs:
    custom_components.luxor_living: debug
```

Then restart HA and check Settings → System → Logs.

---

## Getting Help

- [GitHub Issues](https://github.com/phismith91/luxorliving/issues) — bug reports and feature requests
- [Full Reference](REFERENCE.md) — all options and behaviors documented
- [Advanced Guide](ADVANCED_GUIDE.md) — push webhook, overrides, and performance tuning
