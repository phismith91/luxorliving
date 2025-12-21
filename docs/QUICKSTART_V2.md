# 🚀 Quick Start - LUXORliving v0.2.0

## Was ist neu?

**REST API Authentication für KNX Tunneling!**

```
✅ REST API Client (Login/Logout)
✅ Tunneling Activation via /rest/device/authtunneling
✅ Config Flow mit Username/Password
✅ 3-stufiges Gateway Setup
✅ LXP File Upload in UI
```

---

## 📝 5-Minuten Test

### 1. REST API testen

```bash
cd /home/phil/gitlab_github/luxorliving
python3 scripts/test_rest_api.py 192.168.1.3
```

**Erwartetes Ergebnis:**
```
✅ Login successful!
✅ Tunneling enabled!
✅ All tests passed!
```

### 2. Integration installieren

```bash
# Custom Component kopieren
cp -r custom_components/luxor_living ~/.homeassistant/custom_components/

# HA neu starten
pkill -f "hass -c" && sleep 3 && ./scripts/start_homeassistant.sh &
```

### 3. In UI konfigurieren

```
Home Assistant → Einstellungen → Integrationen
→ Integration hinzufügen → "LUXORliving"
→ LXP hochladen
→ Gateway: 192.168.1.3, admin/admin
→ Submit
```

### 4. Logs prüfen

```bash
tail -f ~/.homeassistant/home-assistant.log | grep luxor_living
```

**Erfolg:**
```
✅ REST API login successful
✅ KNX Tunneling enabled
✅ Successfully connected to KNX Gateway
```

---

## 🐛 Quick-Fixes

**"Login failed"** → Credentials prüfen (Standard: admin/admin)  
**"Cannot connect"** → `ping 192.168.1.3` und Port 80/3671 prüfen  
**"Entities unavailable"** → LuxorPlug VM stoppen!

---

## 📚 Vollständige Doku

- **Installation**: [INSTALLATION.md](INSTALLATION.md)
- **Tunneling**: [TUNNELING_AUTHENTICATION.md](TUNNELING_AUTHENTICATION.md)
- **Tests**: [TESTS.md](TESTS.md)

---

**Version:** 0.2.0 | **Datum:** 21. Dez 2025
