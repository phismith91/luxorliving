# KNX Tunneling Setup für LUXORliving

## Überblick

Die LUXORliving Integration unterstützt **zwei KNX-Verbindungsmodi**:

### 1. **KNX Routing** (Multicast)
- **Standard für größere Installationen**
- Verwendet Multicast IP: `224.0.23.12`
- Port: `3671`
- **Keine direkte 1:1 Verbindung** zum Gateway
- Alle KNX/IP Geräte im Netzwerk empfangen Telegramme

### 2. **KNX Tunneling** (Point-to-Point)
- **Empfohlen für kleinere Installationen**
- Direkte Verbindung zum LUXORliving IP1 Gateway
- Verwendet die **echte IP-Adresse** des Gateways (z.B. `192.168.1.3`)
- Port: `3671`
- **Bessere Kontrolle** über Verbindung
- **Schnellere Initial-Status-Abfrage**

---

## 🔧 Tunneling aktivieren

### Methode 1: Script verwenden (Empfohlen)

```bash
cd /home/phil/gitlab_github/luxorliving
python3 scripts/set_tunneling.py 192.168.1.3
```

**Ersetze `192.168.1.3` mit der IP deines LUXORliving IP1 Gateways!**

Das Script:
- ✅ Ändert `connection_type` auf `tunneling`
- ✅ Setzt die Gateway IP
- ✅ Aktualisiert die Config Entry in `.homeassistant/.storage/core.config_entries`

### Methode 2: Manuell via Python

```python
import json
from pathlib import Path

storage_file = Path.home() / '.homeassistant/.storage/core.config_entries'
with open(storage_file) as f:
    data = json.load(f)

for entry in data['data']['entries']:
    if entry['domain'] == 'luxor_living':
        entry['data']['connection_type'] = 'tunneling'
        entry['data']['host'] = '192.168.1.3'  # DEINE GATEWAY IP!
        entry['data']['port'] = 3671

with open(storage_file, 'w') as f:
    json.dump(data, f, indent=2)

print("✅ Auf Tunneling umgestellt!")
```

### Methode 3: Über Home Assistant UI (Neu-Konfiguration)

1. Entferne die bestehende Integration
2. Füge sie erneut hinzu
3. Bei "Connection Type" wähle **"tunneling"**
4. Gib die IP des LUXORliving IP1 Gateways ein

---

## 🔍 Aktuelle Konfiguration prüfen

```bash
python3 <<'EOF'
import json
from pathlib import Path

storage_file = Path.home() / '.homeassistant/.storage/core.config_entries'
with open(storage_file) as f:
    data = json.load(f)

for entry in data['data']['entries']:
    if entry['domain'] == 'luxor_living':
        print(f"Connection Type: {entry['data'].get('connection_type')}")
        print(f"Host: {entry['data'].get('host')}")
        print(f"Port: {entry['data'].get('port')}")
EOF
```

---

## ⚡ Verbesserungen für Initial-Status-Lesung

### Was wurde implementiert?

Die Integration sendet nun **koordinierte Batch-Reads** beim Start:

#### **Vorher:**
- Jede Entity sendet **einzeln** eine Read-Anfrage
- Bei 50 Entities → 50 unkoordinierte KNX-Telegramme
- **Slow startup**, manche Status werden nicht empfangen

#### **Jetzt:**
- Read-Requests werden **mit Tracking** gesendet (`is_initial=True`)
- Empfangene Antworten werden als **"✅ initial"** markiert
- Logging zeigt, welche Status erfolgreich gelesen wurden
- Neue Funktion: `async_batch_read_group_addresses()` für Batch-Ops

### Beispiel-Logs

```
2025-12-19 10:15:23 DEBUG [custom_components.luxor_living.knx_gateway] 📖 Sent read request to 1/2/3 (initial)
2025-12-19 10:15:23 DEBUG [custom_components.luxor_living.knx_gateway] 📥 Received KNX Response: 1/2/3=1 (type: int) ✅ initial
```

---

## 🚀 Nach der Änderung

1. **Home Assistant neu starten:**
   ```bash
   pkill -f "hass -c" && sleep 2 && ./scripts/start_homeassistant.sh
   ```

2. **Logs beobachten:**
   ```bash
   tail -f ~/.homeassistant/home-assistant.log | grep -E "luxor_living|KNX"
   ```

3. **Prüfe Connection-Modus im Log:**
   ```
   ✅ Successfully connected to KNX Gateway 192.168.1.3:3671 (TUNNELING mode)
   ```

---

## 🐛 Troubleshooting

### Problem: Keine Verbindung nach Umstellung auf Tunneling

**Lösung:**
- Prüfe Gateway-IP: Ist `192.168.1.3` erreichbar?
  ```bash
  ping 192.168.1.3
  ```
- Ist der KNX/IP Port offen?
  ```bash
  nc -zv 192.168.1.3 3671
  ```

### Problem: Nicht alle Status werden initial gelesen

**Ursachen:**
- KNX Gateway antwortet nicht auf alle Read-Requests
- Manche Geräte haben keine Status-Adressen
- Bus ist überlastet

**Lösungen:**
1. **Prüfe Logs** auf fehlgeschlagene Reads
2. **Nutze die neue Batch-Read-Funktion** (kommend in nächstem Update)
3. **Erhöhe Delay** zwischen Reads (Standard: 50ms)

### Problem: "Cannot read - not connected to KNX gateway"

**Lösung:**
- Gateway-Verbindung ist fehlgeschlagen
- Prüfe Connection Type und IP
- Stelle sicher, dass nur **1 Tunneling-Verbindung** aktiv ist (manche Gateways erlauben nur eine!)

---

## 📊 Vergleich: Routing vs. Tunneling

| Feature | Routing | Tunneling |
|---------|---------|-----------|
| **IP-Adresse** | Multicast (224.0.23.12) | Gateway IP (192.168.1.3) |
| **Verbindungsart** | Broadcast | Point-to-Point |
| **Max. Clients** | Unbegrenzt | 1-4 (je nach Gateway) |
| **Performance** | Höher bei vielen Geräten | Besser für einzelne Clients |
| **Firewall** | Multicast muss erlaubt sein | Normale TCP-Verbindung |
| **Empfohlen für** | Große Netzwerke | Kleinere Installationen |

---

## 🔗 Weiterführende Dokumentation

- [KNX/IP Spezifikation](https://www.knx.org/knx-en/for-professionals/index.php)
- [XKNX Library Docs](https://xknx.io/)
- [Home Assistant KNX Integration](https://www.home-assistant.io/integrations/knx/)

---

## ✅ Zusammenfassung

**Für die meisten Luxor-Installationen wird Tunneling empfohlen:**

1. ✅ Nutze das `set_tunneling.py` Script
2. ✅ Gib die echte IP deines LUXORliving IP1 Gateways an
3. ✅ Starte Home Assistant neu
4. ✅ Prüfe die Logs auf erfolgreiche Verbindung

**Bei Problemen:**
- Zurück zu Routing: Setze `host` auf `224.0.23.12` und `connection_type` auf `routing`
