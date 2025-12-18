# LUXORliving Home Assistant Integration - Status

## ✅ Was funktioniert bereits

### Entity Mapping (66 Entities)
Die Integration kann bereits LXP-Projektdateien parsen und folgende Entities erstellen:

- **23 Lichter** - mit Ein/Aus und Dimmen-Support
- **40 Schalter** - iON Taster und andere Schaltaktoren  
- **3 Binary Sensors** - Bewegungsmelder

Alle Entities laufen im **Simulation Mode** (keine echte KNX-Kommunikation).

## 🚀 So startest du die Integration in Home Assistant

### Schnellstart (empfohlen)

```bash
cd /home/phil/gitlab_github/luxorliving
./scripts/start_homeassistant.sh
```

Das Script:
- ✅ Aktiviert automatisch das venv
- ✅ Erstellt `~/.homeassistant` falls nicht vorhanden
- ✅ Verlinkt die Integration automatisch
- ✅ Startet Home Assistant

**Erste Nutzung:**
1. Browser öffnen: http://localhost:8123
2. Benutzer erstellen
3. Onboarding abschließen
4. Integration hinzufügen (siehe Schritt 4 unten)

**Logs in separatem Terminal:**
```bash
tail -f ~/.homeassistant/home-assistant.log | grep luxor
```

---

### Manuelle Schritte (alternativ)

### 1. LXP-Datei bereitstellen
Die Integration sucht aktuell nach:
```
/home/phil/gitlab_github/luxorliving/Familie Schmidt_0.9.lxp
```

Alternativ kannst du in `__init__.py` (Zeile 35) den Pfad ändern zu deiner LXP-Datei.

### 2. Integration zu Home Assistant kopieren

**Option A: Symbolischer Link (empfohlen für Entwicklung)**
```bash
cd ~/.homeassistant/custom_components
ln -s /home/phil/gitlab_github/luxorliving/custom_components/luxor_living luxor_living
```

**Option B: Kopieren**
```bash
cp -r /home/phil/gitlab_github/luxorliving/custom_components/luxor_living \
      ~/.homeassistant/custom_components/
```

### 3. Home Assistant starten

**Du hast Home Assistant im venv - starte es manuell:**

```bash
# Terminal 1: Home Assistant starten
cd /home/phil/gitlab_github/luxorliving
source venv/bin/activate
hass -c ~/.homeassistant

# Terminal 2 (optional): Logs verfolgen
tail -f ~/.homeassistant/home-assistant.log
```

**Erstmaliges Setup:**
- Browser öffnen: http://localhost:8123
- Benutzer erstellen (falls noch nicht vorhanden)
- Onboarding abschließen

### 4. Integration hinzufügen
1. **Einstellungen** → **Geräte & Dienste**
2. **Integration hinzufügen** klicken
3. Nach **"LUXORliving"** suchen
4. Integration konfigurieren:
   - **Host**: Beliebig eingeben (z.B. `192.168.1.100` oder `localhost`)
     - ⚠️ Wird aktuell nicht verwendet - Integration läuft im Simulation Mode
   - **Port**: `3671` (Standard KNX/IP)
     - ⚠️ Wird aktuell ebenfalls nicht verwendet

### 5. Entities überprüfen
Nach dem Hinzufügen solltest du sehen:
- 23 `light.*` Entities
- 40 `switch.*` Entities
- 3 `binary_sensor.*` Entities

**Beispiel-Entities:**
```
light.badlicht
light.leselicht_fenster
switch.ion4_3_t1
binary_sensor.bewegungsmelder
```

## 🧪 Simulation Mode testen

Alle Entities funktionieren lokal ohne KNX-Hardware:

```yaml
# In Home Assistant
service: light.turn_on
target:
  entity_id: light.badlicht
```

**Was passiert:**
- ✅ Entity schaltet in UI auf "on"
- ✅ Log-Eintrag: `SIMULATION: Would send ON to KNX address 1/2/3`
- ❌ Keine echte KNX-Kommunikation

## 📊 Logs ansehen

```bash
# Home Assistant Logs
tail -f ~/.homeassistant/home-assistant.log | grep luxor

# Nur Simulation-Nachrichten
tail -f ~/.homeassistant/home-assistant.log | grep SIMULATION
```

**Erwartete Log-Ausgaben:**
```
2024-01-15 10:00:00 INFO (MainThread) [custom_components.luxor_living] Setting up LUXORliving integration
2024-01-15 10:00:00 INFO (MainThread) [custom_components.luxor_living] Parsing LXP file: ...
2024-01-15 10:00:00 INFO (MainThread) [custom_components.luxor_living.entity_mapper] Mapping 17 devices to entities
2024-01-15 10:00:00 INFO (MainThread) [custom_components.luxor_living.entity_mapper] Mapped 66 entities total
2024-01-15 10:00:01 INFO (MainThread) [custom_components.luxor_living.light] Creating 23 light entities
2024-01-15 10:00:01 INFO (MainThread) [custom_components.luxor_living.switch] Creating 40 switch entities
2024-01-15 10:00:01 INFO (MainThread) [custom_components.luxor_living.binary_sensor] Creating 3 binary sensor entities
```

## 🔧 Troubleshooting

### Integration erscheint nicht in der Liste
- Prüfe ob `custom_components/luxor_living/` existiert
- Prüfe `manifest.json` auf Syntaxfehler
- HA Logs prüfen: `grep -i error ~/.homeassistant/home-assistant.log | grep luxor`

### Keine Entities erstellt
- Prüfe ob LXP-Datei existiert (siehe `__init__.py` Zeile 35)
- Logs prüfen: `grep "Mapped.*entities" ~/.homeassistant/home-assistant.log`

### Fehler beim Laden
```bash
# Vollständige Fehlerausgabe
tail -100 ~/.homeassistant/home-assistant.log | grep -A 10 "luxor\|LUXOR"
```

## 📝 Nächste Entwicklungsschritte

### 1. Simulation Coordinator
- Zentrales State Management
- Event Simulation (Bewegungsmelder triggern)
- Szenen testen ohne Hardware

### 2. Config Flow verbessern
- LXP-Upload in der UI
- Simulation Mode Toggle
- KNX/IP Gateway optional

### 3. Echte KNX-Kommunikation
- XKNX Integration
- Telegram-Monitoring
- Status-Rückmeldungen

## 🎯 Entwicklungs-Workflow

### Code ändern
```bash
cd /home/phil/gitlab_github/luxorliving
# Änderungen vornehmen...
```

### Änderungen testen
```bash
# Terminal in dem HA läuft: Strg+C drücken, dann neu starten
cd /home/phil/gitlab_github/luxorliving
source venv/bin/activate
hass -c ~/.homeassistant

# Oder Integration neu laden (wenn unterstützt)
# Einstellungen → Geräte & Dienste → LUXORliving → Neu laden
```

### Tests ausführen
```bash
source venv/bin/activate
python tests/test_integration.py
```

## 📚 Dokumentation

- [LXP Parser](custom_components/luxor_living/lxp_parser.py) - XML Parsing
- [Entity Mapper](custom_components/luxor_living/entity_mapper.py) - Device Mapping
- [Agent Context](.github/copilot/CONTEXT.md) - Architektur-Entscheidungen
- [Mapping Rules](.github/copilot/agent_mapping.md) - Entity-Mapping-Regeln

## 🤝 Fragen?

Bei Problemen:
1. Logs prüfen (siehe oben)
2. `test_integration.py` ausführen
3. GitHub Issues erstellen
