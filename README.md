# LUXORliving Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/phismith91/luxorliving.svg)](https://github.com/phismith91/luxorliving/releases)
[![License](https://img.shields.io/github/license/phismith91/luxorliving.svg)](LICENSE)
![Quality Score](https://img.shields.io/badge/Quality-8.5%2F10-green)

Home Assistant Integration für **Theben LUXORliving KNX/IP Gateways** mit automatischer Geräteerkennung aus LXP-Projektdateien.

> ⚠️ **Beta Status**: Diese Integration ist funktionsfähig, aber noch in aktiver Entwicklung. Sensor-, Climate- und Cover-Plattformen sind noch nicht vollständig implementiert.

---

## 🌟 Highlights

- ✅ **Echte KNX/IP Kommunikation** – Unterstützt Tunneling & Routing Modi
- ✅ **Kein ETS erforderlich** – Nutzt `.lxp` Projektexporte aus Theben LUXORPlug
- ✅ **Automatisches Entity-Mapping** – Erkennt Lichter, Schalter, Sensoren automatisch
- ✅ **Live Status-Updates** – Empfängt KNX Telegramme in Echtzeit
- ✅ **Config Flow UI** – Einfache Einrichtung über Home Assistant UI
- ✅ **Simulation Mode** – Testen ohne Hardware (Dry-Run)
- ✅ **HACS-Ready** – Einfache Installation über HACS

---

## 📋 Anforderungen

- **Home Assistant** ≥ 2024.12.0
- **Theben LUXORliving IP1 Gateway** (KNX/IP Interface)
- **LXP-Projektdatei** (`.lxp`) – Export aus Theben LUXORPlug Software

---

## 🚀 Installation

### Via HACS (Empfohlen)

1. Öffne **HACS** in Home Assistant
2. Klicke auf **Integrations**
3. Klicke auf die **3 Punkte** (oben rechts) → **Custom repositories**
4. Füge hinzu:
   - **Repository:** `https://github.com/phismith91/luxorliving`
   - **Kategorie:** `Integration`
5. Klicke auf **Download** → **Neustart** von Home Assistant

### Manuelle Installation

1. Kopiere den Ordner `custom_components/luxor_living` in dein Home Assistant `config/custom_components/` Verzeichnis
2. Starte Home Assistant neu

---

## ⚙️ Einrichtung

### Schritt 1: LXP-Datei exportieren

1. Öffne **Theben LUXORPlug** Software
2. Öffne dein Projekt
3. Gehe zu **Datei** → **Exportieren** → **LXP-Datei speichern** (`.lxp`)
4. Speichere die Datei auf deinem Home Assistant Server (z.B. `/config/luxor/mein_projekt.lxp`)

### Schritt 2: Integration hinzufügen

1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Klicke auf **Integration hinzufügen**
3. Suche nach **LUXORliving**
4. Folge dem Setup-Assistenten:
   - **Schritt 1:** Pfad zur LXP-Datei eingeben (z.B. `/config/luxor/mein_projekt.lxp`)
   - **Schritt 2:** Gateway-Konfiguration:
     - **IP-Adresse**: IP des LUXORliving IP1 Gateways
     - **Port**: 3671 (KNX/IP Standard)
     - **Connection Type**: Tunneling (empfohlen) oder Routing
     - **Simulation Mode**: Für Tests ohne Hardware aktivieren

### Schritt 3: Fertig!

Die Integration erkennt automatisch alle Geräte aus deinem LXP-Projekt und erstellt entsprechende Entities:

- ✅ **Lights** (Dimmer, Schaltaktoren) - **Voll funktionsfähig**
- ✅ **Switches** (Schaltaktoren) - **Voll funktionsfähig**
- ✅ **Binary Sensors** (Bewegungsmelder, Fensterkontakte) - **Voll funktionsfähig**
- ⚠️ **Sensors** (Temperatur, Helligkeit) - **In Entwicklung**
- ⚠️ **Covers** (Jalousien, Rollläden) - **In Entwicklung**
- ⚠️ **Climate** (Thermostate) - **In Entwicklung**

---

## 🎯 Plattform-Status

| Plattform | Status | Features |
|-----------|--------|----------|
| 💡 **Light** | ✅ Production | On/Off, Dimming, Status Updates |
| 🔌 **Switch** | ✅ Production | On/Off, Status Updates |
| 📊 **Binary Sensor** | ✅ Production | Status Updates |
| 🌡️ **Sensor** | ⚠️ Beta | Basis-Implementation |
| 🪟 **Cover** | ⚠️ Planned | Noch nicht implementiert |
| 🌡️ **Climate** | ⚠️ Planned | Noch nicht implementiert |

---

## 🧪 Simulation Mode (Dry-Run)

Zum Testen ohne echte Hardware:

1. Gehe zu **Einstellungen** → **Geräte & Dienste** → **LUXORliving**
2. Klicke auf **Optionen**
3. Aktiviere **Simulation Mode**
4. Alle Entity-Befehle werden geloggt, aber nicht an das Gateway gesendet

---

## 🛠️ Troubleshooting

### Integration lädt nicht

```bash
# Logfile prüfen
tail -f /config/home-assistant.log | grep luxor_living
```

### LXP-Datei wird nicht erkannt

- Stelle sicher, dass der Pfad korrekt ist (absoluter Pfad)
- Prüfe Dateiberechtigungen (`chmod 644 mein_projekt.lxp`)
- LXP-Datei muss aus **Theben LUXORPlug** exportiert sein (XML-Format)

### Gateway nicht erreichbar

- Prüfe IP-Adresse und Port (Standard: `3671`)
- Firewall-Regeln prüfen
- Ping zum Gateway: `ping <GATEWAY_IP>`

---

## 📚 Weitere Ressourcen

- [QUICKSTART.md](QUICKSTART.md) – Entwickler-Dokumentation
- [CONTEXT.md](.github/copilot/CONTEXT.md) – Architektur-Übersicht
- [Issue Tracker](https://github.com/phismith91/luxorliving/issues) – Bugs & Feature Requests

---

## 📝 Lizenz

Dieses Projekt steht unter der [LICENSE](LICENSE).

---

## 🙏 Credits

- **Theben AG** – LUXORliving Hardware & LUXORPlug Software
- **xknx** – KNX/IP Python Library
- **Home Assistant Community** – Framework & Support

---

## 🤝 Beitragen

Pull Requests sind willkommen! Für größere Änderungen bitte zuerst ein Issue öffnen.

1. Fork das Repository
2. Erstelle einen Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

---

**Viel Erfolg mit deiner LUXORliving Integration! 🏠✨**