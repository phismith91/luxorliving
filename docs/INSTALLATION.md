# LUXORliving v0.2.0 - Installation & Setup Guide

## 🎯 Was ist neu in v0.2.0?

**Wichtige Änderung:** KNX Tunneling funktioniert jetzt mit REST API Authentifizierung!

### Neue Features

- ✅ **REST API Integration**: Login erforderlich für KNX Tunneling
- ✅ **LXP File Upload**: Direkt in der UI hochladen
- ✅ **Username/Password**: Konfiguration über die UI
- ✅ **Automatische Tunneling-Aktivierung**: Via `/rest/device/authtunneling`
- ✅ **Graceful Shutdown**: Logout deaktiviert Tunneling automatisch

---

## 📋 Voraussetzungen

### Hardware

- **Theben LUXORliving IP1 Gateway** (BAOS 777)
- KNX-Installation mit LUXORliving-System
- Netzwerkzugriff auf das Gateway

### Software

- Home Assistant 2024.12.0 oder neuer
- LXP-Projektdatei (aus Theben LUXORPlug)

---

## 🚀 Installation

### Methode 1: HACS (Empfohlen)

1. **HACS installieren** (falls noch nicht vorhanden)
   ```
   https://hacs.xyz/docs/setup/download
   ```

2. **Custom Repository hinzufügen**
   - HACS → Integrationen → ⋮ (oben rechts) → Custom repositories
   - Repository: `https://github.com/phismith91/luxorliving`
   - Category: Integration
   - Klick: "Add"

3. **Integration installieren**
   - HACS → Integrationen → Suche "LUXORliving"
   - Klick: "Download"
   - Home Assistant neu starten

### Methode 2: Manuell

```bash
# Via SSH auf dem HA Server
cd /config/custom_components
git clone https://github.com/phismith91/luxorliving.git luxor_living

# Oder: ZIP herunterladen und entpacken
# Struktur: /config/custom_components/luxor_living/

# Home Assistant neu starten
ha core restart
```

---

## ⚙️ Einrichtung

### Schritt 1: Integration hinzufügen

1. **Home Assistant UI öffnen**
   - Einstellungen → Geräte & Dienste → Integration hinzufügen
   - Suche: "LUXORliving"

2. **LXP-Datei hochladen**
   
   ![Step 1: LXP Upload](docs/screenshots/step1_lxp_upload.png)
   
   - Klick: "Choose File"
   - Datei auswählen: z.B. `familie_schmidt.lxp`
   - Die Datei bekommst du aus Theben LUXORPlug:
     ```
     LUXORPlug → Projekt speichern → Downloads/projekt.lxp
     ```

3. **Gateway konfigurieren**
   
   ![Step 2: Gateway Config](docs/screenshots/step2_gateway_config.png)
   
   | Feld | Wert | Beschreibung |
   |------|------|-------------|
   | **Gateway IP Address** | `192.168.1.3` | IP deines BAOS 777 |
   | **Gateway Port** | `3671` | Standard KNX/IP Port |
   | **Username** | `admin` | REST API Username |
   | **Password** | `admin` | REST API Password |
   | **Connection Type** | `tunneling` | Empfohlen (mit Auth) |
   | **Simulation Mode** | `☐` | Nur zum Testen |

4. **Validierung**
   
   Die Integration testet automatisch:
   - ✅ REST API Login
   - ✅ Credentials korrekt
   - ✅ Tunneling Aktivierung möglich
   
   Bei Fehler:
   - ❌ **Invalid username or password**: Credentials prüfen
   - ❌ **Cannot connect**: IP-Adresse/Netzwerk prüfen

---

## 🔑 Credentials herausfinden

### Standard-Credentials

**Default:** `admin` / `admin`

### Credentials wurden geändert?

Wenn die Standard-Credentials nicht funktionieren:

1. **Via ETS konfiguriert**
   - In ETS nachschauen (Application → Settings)
   - Oder: ETS-Projekt-Datei durchsuchen

2. **Via Web-Interface**
   ```
   http://192.168.1.3
   # Versuche Login mit verschiedenen Credentials
   # Browser DevTools → Network Tab → Request Headers
   ```

3. **Reset auf Werkseinstellungen**
   - Siehe BAOS 777 Handbuch
   - ⚠️ Achtung: Alle Konfigurationen gehen verloren!

---

## 📁 LXP-Datei bekommen

### Option 1: Aus LUXORPlug exportieren

1. **LUXORPlug öffnen** (Windows VM)
2. **Projekt laden**
3. **Datei → Projekt speichern**
4. Datei: `C:\Users\...\Downloads\projekt.lxp`

### Option 2: Vom Projektleiter

- LXP-Datei vom Elektriker/Installateur anfragen
- Dateiname: z.B. `familie_schmidt.lxp` oder `wohnung_madeira.lxp`

### Option 3: Von bestehendem System

Falls LuxorPlug läuft:
```bash
# Auf dem LuxorPlug Windows System
# Projektdatei liegt meist in:
%APPDATA%\Theben\LUXORPlug\projects\
```

---

## 🧪 Testen der Installation

### 1. Entities prüfen

Nach erfolgreichem Setup:

```
Einstellungen → Geräte & Dienste → LUXORliving
```

Du solltest sehen:
- ✅ **Geräte**: 1 (LUXORliving Gateway)
- ✅ **Entities**: z.B. 36 (27 Lights, 9 Switches)

### 2. Erstes Licht schalten

```
Entwicklerwerkzeuge → Dienste

Dienst: light.turn_on
Ziel: light.badlicht
```

**Erwartetes Verhalten:**
- ✅ Licht geht an
- ✅ Status wird aktualisiert
- ✅ Logs zeigen KNX-Telegramme

### 3. Logs checken

```bash
# Via SSH
tail -f /config/home-assistant.log | grep luxor_living

# Oder in UI:
Einstellungen → System → Protokolle → Suche "luxor_living"
```

**Erfolgreiche Verbindung:**
```
2025-12-21 INFO custom_components.luxor_living 🔐 Step 1/3: REST API Login...
2025-12-21 INFO custom_components.luxor_living ✅ REST API login successful
2025-12-21 INFO custom_components.luxor_living 🔧 Step 2/3: Enabling KNX Tunneling...
2025-12-21 INFO custom_components.luxor_living ✅ KNX Tunneling enabled
2025-12-21 INFO custom_components.luxor_living 🔌 Step 3/3: Connecting KNX...
2025-12-21 INFO custom_components.luxor_living ✅ Successfully connected to KNX Gateway 192.168.1.3:3671
```

---

## 🐛 Troubleshooting

### Problem: "Invalid username or password"

**Ursache:** Falsche REST API Credentials

**Lösung:**
1. Prüfe Standard: `admin` / `admin`
2. Falls geändert: ETS-Projekt prüfen
3. Web-Interface testen: `http://192.168.1.3`

### Problem: "Cannot connect"

**Ursache:** Netzwerkverbindung zum Gateway

**Lösung:**
```bash
# Ping testen
ping 192.168.1.3

# Port testen
nc -zv 192.168.1.3 80    # REST API
nc -zv 192.168.1.3 3671  # KNX Tunneling

# Firewall prüfen
# - Port 80 (HTTP) muss offen sein
# - Port 3671 (KNX) muss offen sein
```

### Problem: "Entities unavailable"

**Ursache:** KNX-Verbindung nicht aktiv

**Lösung:**
```
1. Logs prüfen:
   - "✅ Successfully connected" → OK
   - "❌ Failed to connect" → Problem!

2. LuxorPlug VM prüfen:
   - Wenn LuxorPlug läuft: STOPPEN
   - Nur 1 Tunneling-Session gleichzeitig möglich

3. Home Assistant neu starten:
   Einstellungen → System → Neu starten
```

### Problem: LXP-Datei wird nicht akzeptiert

**Ursache:** Korrupte oder falsche Datei

**Lösung:**
1. Datei mit Editor öffnen
2. Prüfe: Beginnt mit `<?xml version="1.0"?>`
3. Enthält: `<Project>`-Tags
4. Neu exportieren aus LUXORPlug

### Problem: Tunneling funktioniert nicht

**Debug-Schritte:**

1. **REST API manuell testen**
   ```bash
   # Login
   curl -X POST http://192.168.1.3/rest/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin"}'
   
   # Response sollte Session Token enthalten
   ```

2. **Tunneling manuell aktivieren**
   ```bash
   # Mit Token aus Login
   curl -X PUT http://192.168.1.3/rest/device/authtunneling \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"enabled":true}'
   ```

3. **DevTools nutzen**
   ```
   Browser: http://192.168.1.3
   F12 → Network Tab → XHR
   # Beobachte Login-Request beim Anmelden
   # Dokumentiere echte API-Endpunkte
   ```

---

## 📊 Diagnostics

Diagnostics abrufen für Support-Anfragen:

```
Einstellungen → Geräte & Dienste → LUXORliving
→ Gerät auswählen → ⋮ → Download diagnostics
```

Enthält:
- Gateway-Status
- REST API Session
- Tunneling Status
- Entity-Liste
- Verbindungsinformationen

---

## 🔄 Updates

### Via HACS

```
HACS → Integrationen → LUXORliving → Update
Home Assistant neu starten
```

### Via Git

```bash
cd /config/custom_components/luxor_living
git pull
ha core restart
```

---

## 🎓 Weiterführende Dokumentation

- [Architecture Decision](docs/ARCHITECTURE_DECISION.md) - Warum REST API + Tunneling?
- [Tunneling Authentication](docs/TUNNELING_AUTHENTICATION.md) - Technische Details
- [BAOS REST API](docs/BAOS_REST_API.md) - API-Referenz
- [Testing Guide](docs/TESTS.md) - Für Entwickler

---

## 💡 Best Practices

### LuxorPlug und HA parallel?

**Nicht empfohlen**, aber möglich:

```
Problem: BAOS 777 hat nur 1 Tunnel-Slot
Lösung: Nur 1 System gleichzeitig aktiv

Option 1: Automation
  - LuxorPlug VM automatisch stoppen wenn HA startet
  - HA automatisch Tunneling deaktivieren wenn LuxorPlug startet

Option 2: Manuelle Kontrolle
  - LuxorPlug nur bei Bedarf starten (Konfiguration)
  - HA 24/7 laufen lassen (Produktiv-Betrieb)
```

### Credentials sicher speichern

Home Assistant verschlüsselt Config Entries automatisch:
```
.storage/core.config_entries
# Password ist verschlüsselt
# Nur mit HA Master Key lesbar
```

### Backup

Wichtige Dateien regelmäßig sichern:
```
/config/custom_components/luxor_living/  # Integration
.storage/luxor_living.*.lxp               # LXP-Datei
.storage/core.config_entries              # Konfiguration
```

---

## 🤝 Support

- **GitHub Issues**: [https://github.com/phismith91/luxorliving/issues](https://github.com/phismith91/luxorliving/issues)
- **Discussions**: [https://github.com/phismith91/luxorliving/discussions](https://github.com/phismith91/luxorliving/discussions)
- **Email**: [Issues bevorzugt für Tracking]

---

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei

---

**Version:** 0.2.0  
**Datum:** 21. Dezember 2025  
**Author:** @phismith91
