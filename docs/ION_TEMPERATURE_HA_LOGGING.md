# ION Temperature Discovery - Home Assistant Method

## ✅ Einfachste Lösung: Direkt in Home Assistant

Die Integration loggt **automatisch alle Temperatur-Telegramme** mit 🌡️ Emoji im Home Assistant Log!

## Schritt-für-Schritt

### 1. Logging Level anpassen

Öffne `configuration.yaml` in Home Assistant:

```yaml
logger:
  default: warning
  logs:
    # Enable INFO level for LUXORliving KNX gateway
    custom_components.luxor_living.knx_gateway: info
```

### 2. Home Assistant neu starten

```bash
# In Home Assistant UI:
# Einstellungen → System → Neu starten
```

### 3. ION-Geräte triggern

Berühre die ION-Displays oder öffne die LUXORliving App, um Temperatur-Updates zu erzwingen.

### 4. Log überwachen

**Option A: Home Assistant UI**

```
Einstellungen → System → Protokolle

# Suche nach: 🌡️
# Oder filtere: custom_components.luxor_living
```

**Option B: Live-Log via Terminal**

```bash
# SSH in Home Assistant Container/Server
tail -f /config/home-assistant.log | grep "🌡️"
```

**Option C: Developer Tools**

```
Entwicklerwerkzeuge → Protokolle → Filter: "Temperature"
```

### 5. Ergebnis

Du siehst Log-Einträge wie:

```
2025-12-25 20:45:32 INFO (MainThread) [custom_components.luxor_living.knx_gateway] 
🌡️  KNX Temperature: 9.0.7 → 5/1/10 = 22.3°C (Response)

2025-12-25 20:46:15 INFO (MainThread) [custom_components.luxor_living.knx_gateway] 
🌡️  KNX Temperature: 9.0.8 → 5/1/11 = 21.8°C (Response)

2025-12-25 20:47:02 INFO (MainThread) [custom_components.luxor_living.knx_gateway] 
🌡️  KNX Temperature: 9.0.10 → 5/1/12 = 23.1°C (Response)
```

**Bedeutung:**
- `9.0.7` = **ION-Geräte-Adresse** (Physical Address)
- `5/1/10` = **KNX Group Address** für Temperatur
- `22.3°C` = Temperaturwert
- `Response` = Telegram-Typ

### 6. Mapping erstellen

Vergleiche mit deinem LXP:

```bash
# In docs/Familie Schmidt_0.9.lxp
grep 'address="9.0.7"' -B 1 | grep name=
# → name="iON4-3"

grep 'address="9.0.8"' -B 1 | grep name=
# → name="iON4-2"
```

**Mapping-Tabelle:**

| Log Source | LXP Device | Temperature GA |
|------------|------------|----------------|
| 9.0.7      | iON4-3     | 5/1/10         |
| 9.0.8      | iON4-2     | 5/1/11         |
| 9.0.10     | iON4-7     | 5/1/12         |

### 7. Overrides konfigurieren

Erstelle/editiere `overrides.yaml`:

```yaml
sensors:
  - name: "iON4-3 Raumtemperatur"
    role: "Temperature"
    address: "5/1/10"
    device_name: "iON4-3"
    device_id: "ion4_3"
    
  - name: "iON4-2 Raumtemperatur"
    role: "Temperature"
    address: "5/1/11"
    device_name: "iON4-2"
    device_id: "ion4_2"
    
  - name: "iON4-7 Raumtemperatur"
    role: "Temperature"
    address: "5/1/12"
    device_name: "iON4-7"
    device_id: "ion4_7"
```

### 8. Integration neu laden

```
Einstellungen → Geräte & Dienste → LUXORliving → ⋮ → Integration neu laden
```

Die Temperatursensoren sollten jetzt als Entities erscheinen! 🎉

## Debug: Alle KNX-Telegramme sehen

Falls du ALLE Telegramme sehen willst (nicht nur Temperaturen):

```yaml
logger:
  default: warning
  logs:
    custom_components.luxor_living.knx_gateway: debug
```

Dann siehst du auch Licht-Schalter, Dimmer, etc.

## Vorteile dieser Methode

✅ Keine zusätzlichen Scripts nötig  
✅ Läuft während normaler HA-Nutzung  
✅ Kein Tunneling-Konflikt  
✅ Echtzeit-Anzeige im HA-Log  
✅ Emoji 🌡️ für leichtes Filtern  

## Alternative: Event Listener

Du kannst auch ein Automation erstellen, die auf KNX-Events reagiert:

```yaml
automation:
  - alias: "Log ION Temperatures"
    trigger:
      - platform: event
        event_type: luxor_living_knx_telegram
        event_data:
          is_temperature: true
    action:
      - service: system_log.write
        data:
          message: >
            ION Temp: {{ trigger.event.data.source }} → 
            {{ trigger.event.data.destination }} = 
            {{ trigger.event.data.value }}°C
          level: info
```

(Erfordert Event-Firing im Code - kann ich hinzufügen falls gewünscht)

## Troubleshooting

### Keine 🌡️ Logs

1. **Logger-Level prüfen:**
   ```yaml
   logger:
     logs:
       custom_components.luxor_living.knx_gateway: info
   ```

2. **HA neu starten** nach `configuration.yaml` Änderung

3. **ION-Display berühren** um Updates zu triggern

4. **Warte 1-2 Minuten** für periodische Updates

### Zu viele Logs

Falls zu viel geloggt wird, zurück auf `warning`:

```yaml
logger:
  logs:
    custom_components.luxor_living.knx_gateway: warning
```

Dann nur noch Warnungen, keine Info-Logs.

---

**Viel einfacher als separates Script, oder?** 😊
