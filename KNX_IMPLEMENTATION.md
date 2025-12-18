# KNX Communication Implementation

## Übersicht

Die XKNX-Integration wurde erfolgreich implementiert. Die Integration kommuniziert jetzt direkt mit dem **LUXORliving IP1 Gateway** über KNX/IP.

---

## Neue Komponenten

### 1. KNX Gateway Manager (`knx_gateway.py`)

Zentrale Komponente für die KNX-Kommunikation:

**Features:**
- ✅ KNX/IP Tunneling Support
- ✅ KNX/IP Routing Support  
- ✅ Automatisches Reconnect
- ✅ Telegram Senden (GroupValueWrite)
- ✅ Telegram Empfangen (Listener System)
- ✅ Simulation Mode (für Tests ohne Hardware)

**Methoden:**
```python
async_setup()                    # Verbindung aufbauen
async_disconnect()               # Verbindung trennen
async_send_telegram()            # KNX Telegram senden
async_read_group_address()       # Status lesen
register_listener()              # Status-Updates empfangen
```

### 2. Erweiterte Konstanten (`const.py`)

**Neue Konfigurationsoptionen:**
- `CONF_CONNECTION_TYPE` - Tunneling oder Routing
- `CONF_SIMULATION_MODE` - Dry-Run ohne echte Hardware
- `DATA_KNX_GATEWAY` - Schlüssel für Gateway-Instanz

---

## Config Flow Erweiterungen

Der Setup-Assistent unterstützt jetzt:

### Schritt 1: LXP-Datei (unverändert)
- Pfad zur `.lxp` Projektdatei

### Schritt 2: Gateway-Konfiguration (erweitert)
- **Host**: IP-Adresse des IP1 Gateways
- **Port**: KNX/IP Port (Standard: 3671)
- **Connection Type**: 
  - `tunneling` (Empfohlen) - Punkt-zu-Punkt Verbindung
  - `routing` - Multicast für mehrere Clients
- **Simulation Mode**: Aktiviert Dry-Run ohne echte Kommunikation

---

## Entity-Plattformen

### Lights (`light.py`)

**Features:**
- ✅ KNX Telegram senden (Ein/Aus)
- ✅ KNX Status empfangen (automatische Updates)
- ✅ Dimmen mit Prozent-Werten (DPT 5.001)
- ✅ Listener für Helligkeits-Updates

**Dimmbare Lichter:**
```python
async_turn_on(brightness=128)  # Dimmt auf 50%
```

### Switches (`switch.py`)

**Features:**
- ✅ KNX Telegram senden (Ein/Aus)
- ✅ KNX Status empfangen (automatische Updates)
- ✅ Listener für Status-Updates

---

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

---

## Simulation Mode

Für Tests ohne echte Hardware:

**Aktivierung:**
```yaml
Simulation Mode: true
```

**Verhalten:**
- ✅ Alle Entities funktionieren
- ✅ State-Changes werden geloggt
- ❌ Keine echten KNX Telegramme
- ✅ Perfekt für Entwicklung

**Log-Beispiel:**
```
🔥 SIMULATION: Would send binary=True to KNX address 1/2/3
```

---

## Datentypen (DPT)

### Unterstützte DPT-Typen:

| Typ | DPT | Beschreibung | Verwendung |
|-----|-----|--------------|------------|
| **binary** | DPT 1.001 | On/Off | Schalter, Lichter |
| **percent** | DPT 5.001 | 0-100% | Dimmer, Jalousien |
| **temperature** | DPT 9.001 | Temperatur | Sensoren |

**Erweiterbar** für weitere DPT-Typen in `knx_gateway.py`

---

## Architektur

```
┌──────────────────────────────────────────┐
│         Home Assistant                   │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  LUXORliving Integration           │  │
│  │                                    │  │
│  │  ┌──────────────┐  ┌────────────┐ │  │
│  │  │ LXP Parser   │  │ EntityMapper│ │  │
│  │  └──────────────┘  └────────────┘ │  │
│  │                                    │  │
│  │  ┌──────────────────────────────┐ │  │
│  │  │   KNX Gateway Manager        │ │  │
│  │  │   - XKNX Integration         │ │  │
│  │  │   - Tunneling/Routing        │ │  │
│  │  │   - Telegram Send/Receive    │ │  │
│  │  └──────────────────────────────┘ │  │
│  │           │                        │  │
│  │  ┌────────┴────────┬─────────┐    │  │
│  │  │                 │         │    │  │
│  │  │ Lights     Switches  Sensors   │  │
│  │  │                 │         │    │  │
│  │  └─────────────────┴─────────┘    │  │
│  └────────────────────────────────────┘  │
└──────────────────┬───────────────────────┘
                   │
                   │ KNX/IP (UDP 3671)
                   │
      ┌────────────▼────────────┐
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
