# Installation Guide

Step-by-step installation and configuration for LUXORliving integration.

## Prerequisites

Before installation, ensure you have:

- **Theben LUXORliving IP1 Gateway** (BAOS 777) connected to your network
- **LXP project file** exported from Theben LUXORPlug software
- **Home Assistant** ≥ 2024.12.0
- Network access to gateway (verify with `ping <gateway-ip>`)

## Installation

### HACS (Recommended)

1. Open **HACS** → **Integrations**
2. Click **⋮** (top right) → **Custom repositories**
3. Add repository:
   - URL: `https://github.com/phismith91/luxorliving`
   - Category: **Integration**
4. Click **Download**
5. Restart Home Assistant

### Manual Installation

1. SSH to Home Assistant server
2. Navigate to config directory:
   ```bash
   cd /config/custom_components
   ```
3. Download integration:
   ```bash
   wget https://github.com/phismith91/luxorliving/releases/latest/download/luxor_living.zip
   unzip luxor_living.zip
   ```
4. Restart Home Assistant

## Configuration

### Step 1: Add Integration

**Settings** → **Devices & Services** → **Add Integration** → Search **"LUXORliving"**

### Step 2: Upload LXP File

**Option A: File Upload (recommended)**
- Click **Choose File** → Select your `.lxp` project file
- File is automatically copied to Home Assistant config

**Option B: Manual Path**
- Copy LXP file to `/config/luxor/` directory
- Enter path: `/config/luxor/project.lxp`

**Exporting LXP from LUXORPlug:**
1. Open Theben LUXORPlug software
2. **File** → **Export** → Save as `.lxp`
3. Transfer file to Home Assistant (e.g., via Samba share)

### Step 3: Gateway Configuration

| Field | Value | Notes |
|-------|-------|-------|
| Gateway IP | `192.168.1.3` | Find in LUXORPlug or router DHCP table |
| Connection Type | **Tunneling** | Recommended (authenticated, stable) |
| Username | `admin` | BAOS REST API credentials |
| Password | `admin` | Default: admin/admin |

**Connection Types:**
- **Tunneling**: Point-to-point connection, requires authentication (recommended)
- **Routing**: Multicast, no authentication, may have firewall issues

### Step 4: Verify Setup
   
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
**Check integration:**
1. **Settings** → **Devices & Services** → **LUXORliving**
2. Verify entities created (lights, switches, sensors)
3. Test first entity:
   - **Developer Tools** → **Services**
   - Service: `light.turn_on`
   - Target: Select any light entity
   - Click **Call Service**

**Expected result:** Physical light turns on, entity state updates in HA.

## Troubleshooting

### Integration Not Loading

**Check logs:**
```bash
tail -f /config/home-assistant.log | grep luxor_living
```

**Common causes:**
- Invalid LXP file path → Use absolute path `/config/luxor/project.lxp`
- File permissions → `chmod 644 /config/luxor/project.lxp`
- Integration not installed → Verify `/config/custom_components/luxor_living/` exists

### Gateway Unreachable

**Verify connectivity:**
```bash
ping <gateway-ip>
nmap -p 3671 <gateway-ip>
```

**Common causes:**
- Wrong IP address → Check router DHCP table
- Firewall blocking port 3671 → Allow UDP 3671
- Gateway offline → Check physical connection

### Authentication Failed

**Error:** "Invalid username or password"

**Solutions:**
1. Try default credentials: `admin` / `admin`
2. Check BAOS web interface: `http://<gateway-ip>`
3. Reset gateway to factory defaults (see BAOS manual)

### No Entities Created

**Causes:**
- LXP file contains no group addresses
- Wrong file format (must be `.lxp`)
- Parsing error

**Solutions:**
1. Verify LXP file in LUXORPlug software
2. Check debug logs: Set logger to debug level
3. Re-export LXP file

## Advanced

### Debug Logging

Enable detailed logs in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.luxor_living: debug
    xknx: debug
```

Restart Home Assistant, then check logs for detailed KNX telegram information.

### Simulation Mode

Test without physical gateway:

1. **Settings** → **Devices & Services** → **LUXORliving** → **Options**
2. Enable **Simulation Mode**
3. Submit

All KNX operations are logged but not sent to gateway. Useful for development and testing.

### Multiple Gateways

Configure multiple LUXORliving gateways:

1. Add first integration (gateway A)
2. **Add Integration** again → **LUXORliving**
3. Configure gateway B with different IP
4. Each gateway creates separate entities with unique IDs

## Uninstall

### Remove Integration

1. **Settings** → **Devices & Services**
2. Find **LUXORliving** → **⋮** → **Delete**
3. Confirm deletion

All entities are removed automatically.

### Remove Files

```bash
rm -rf /config/custom_components/luxor_living
```

Restart Home Assistant.

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
