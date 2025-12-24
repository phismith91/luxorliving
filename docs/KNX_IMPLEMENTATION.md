# KNX Protocol Details

Technical reference for KNX/IP communication implementation.

## Overview

LUXORliving integration uses **XKNX library** for native KNX/IP protocol communication with BAOS 777 gateways.

**Key features:**
- Tunneling and Routing connection modes
- Real-time telegram listening
- GroupValueRead for initial states
- Automatic reconnection on network issues

## Connection Modes

### Tunneling (Recommended)

**How it works:**
- Point-to-point connection between HA and gateway
- Requires REST API authentication (username/password)
- Port 3671/UDP
- Maximum 4 simultaneous tunneling connections per gateway

**When to use:**
- Single Home Assistant instance
- Stable, authenticated connection required
- Default mode for most users

### Routing

**How it works:**
- Multicast UDP communication (224.0.23.12)
- No authentication required
- All devices on network see KNX telegrams
- Works with multiple KNX clients simultaneously

**When to use:**
- Multiple Home Assistant instances
- Testing/debugging with ETS running parallel
- Firewall issues with tunneling

**Firewall requirements:**
- Allow multicast group 224.0.23.12
- UDP port 3671

## KNX Telegram Types

### GroupValueWrite

**Purpose:** Send commands to KNX devices

**Example:** Turn on light
```
Telegram: GroupValueWrite
Destination: 1/2/3 (Light living room)
Value: 1 (On)
DPT: 1.001 (Binary)

## KNX/IP Modi

### Tunneling (Empfohlen)
- Punkt-zu-Punkt Verbindung zum IP1 Gateway
- Maximale Sicherheit
- Nur 1 Client gleichzeitig

**Verwendung:**
```yaml
Connection Type: tunneling
```

### Routing
- Multicast-Kommunikation (224.0.23.12)
- Mehrere Clients möglich
- Für größere Installationen

**Verwendung:**
```yaml
Connection Type: routing
```

**Used by:** Light on/off, switch control

### GroupValueRead

**Purpose:** Request current state from KNX device

**Example:** Read light status
```
Telegram: GroupValueRead
Destination: 1/2/3
Response: GroupValueResponse with current value
```

**Used by:** Initial state reading on integration startup (~30ms per entity)

### GroupValueResponse

**Purpose:** Automatic state updates from physical switches

**Example:** Wall switch pressed
```
Telegram: GroupValueResponse
Source: Physical switch
Destination: 1/2/3
Value: 1 (On)
```

**Used by:** Real-time entity updates in Home Assistant

## Supported Data Types (DPT)

| DPT   | Type        | Range           | Usage              |
| ----- | ----------- | --------------- | ------------------ |
| 1.001 | Binary      | On/Off          | Switches, lights   |
| 5.001 | Percent     | 0-100%          | Dimmer, brightness |
| 5.003 | Angle       | 0-360°          | Blinds position    |
| 9.001 | Temperature | -273°C - +670°C | Sensors            |

Additional DPTs can be added in `knx_gateway.py`.

## Performance

**Startup time:**
- Initial state reading: ~30ms per entity (GroupValueRead)
- Example: 27 lights = ~800ms total
- Parallel reads not used to avoid KNX bus congestion

**Real-time updates:**
- Physical switch → HA update: <1 second
- HA command → Physical device: <500ms

**Connection stability:**
- Automatic reconnection on network issues
- XKNX handles connection lifecycle
- Graceful shutdown on HA restart

## Troubleshooting

**No telegrams received:**
- Check firewall allows UDP 3671
- Verify group addresses in LXP file match ETS configuration
- Enable debug logging to see telegram traffic

**Slow entity updates:**
- GroupValueRead takes ~30ms per entity (KNX protocol limitation)
- Consider reducing number of entities if startup is too slow
- Initial states are cached after first read

**Connection drops:**
- Tunneling: Max 4 simultaneous connections (check if ETS or other clients connected)
- Routing: Verify multicast routing enabled on network switches
- Check gateway uptime (may need reboot)

**Debug logging:**
```yaml
logger:
  default: info
  logs:
    custom_components.luxor_living.knx_gateway: debug
    xknx: debug
```

Shows all KNX telegrams sent/received with full details.
      │  LUXORliving IP1        │
      │  (Weinzel Gateway)      │
      │                         │
      │  - Tunneling Server     │
      │  - Routing Multicast    │
      └─────────────────────────┘
                   │
                   │ KNX Bus
                   │
      ┌────────────▼────────────┐
      │   KNX Devices           │
      │   - Lichter             │
      │   - Schalter            │
      │   - Sensoren            │
      │   - Jalousien           │
      └─────────────────────────┘
```

---

## Status Updates

### Wie funktionieren Live-Updates?

1. **Entity registriert Listener** beim KNX Gateway
2. **IP1 Gateway** sendet Status-Telegramme
3. **KNX Gateway** empfängt Telegram
4. **Callback** wird aufgerufen
5. **Entity** aktualisiert State in Home Assistant

**Beispiel:**
```python
# In light.py
self._knx_gateway.register_listener(
    self._address_status,
    self._handle_knx_update
)

def _handle_knx_update(self, group_address: str, value: Any):
    self._attr_is_on = bool(value)
    self.schedule_update_ha_state()
```

---

## Bekannte Limitierungen

### IP1 Gateway (Weinzel)
- ❌ **Keine REST API** - nur KNX/IP Protokoll
- ✅ Tunneling und Routing werden unterstützt
- ⚠️ Tunneling erlaubt nur 1 gleichzeitige Verbindung

### Integration
- ⚠️ Binary Sensor noch im Simulation-Mode
- ⚠️ Cover (Jalousien) noch nicht implementiert
- ⚠️ Climate (Thermostate) noch nicht implementiert

---

## Nächste Schritte

### Priorität 1: Fehlende Plattformen
- [ ] Binary Sensor mit KNX verbinden
- [ ] Cover mit KNX verbinden (auf/ab/stopp)
- [ ] Climate mit KNX verbinden (Solltemperatur)

### Priorität 2: Erweiterte Features
- [ ] Szenen-Unterstützung (DPT 17)
- [ ] RGB-Lichter (DPT 232.600)
- [ ] Secure Tunneling (KNX Data Secure)

### Priorität 3: Optimierungen
- [ ] Connection Pooling
- [ ] Besseres Error Handling
- [ ] Automatische DPT-Erkennung

---

## Testing

### Test mit Simulation Mode:
1. Config Flow durchlaufen
2. Simulation Mode aktivieren
3. Entity schalten → Logs prüfen

### Test mit echter Hardware:
1. IP1 Gateway im Netzwerk verfügbar
2. Config Flow mit echter IP
3. Tunneling Mode wählen
4. Entity schalten → KNX Bus überwachen

---

## Dependencies

**XKNX Version:** ≥ 2.12.0

```json
"requirements": [
    "xknx>=2.12.0"
]
```

---

## Changelog

### Version 0.2.0 (Feature Branch)
- ✅ XKNX Integration implementiert
- ✅ KNX Gateway Manager erstellt
- ✅ Tunneling/Routing Support
- ✅ Light Platform mit KNX verbunden
- ✅ Switch Platform mit KNX verbunden
- ✅ Simulation Mode für Tests
- ✅ Automatische Status-Updates
- ✅ Config Flow erweitert

---

## Dokumentation

Weitere Infos:
- **XKNX Docs**: https://xknx.io/
- **KNX Standard**: https://www.knx.org/
- **LUXORliving**: https://www.theben.de/luxorliving
