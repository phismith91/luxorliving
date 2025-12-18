# LUXORliving Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/phismith91/luxorliving.svg)](https://github.com/phismith91/luxorliving/releases)
[![License](https://img.shields.io/github/license/phismith91/luxorliving.svg)](LICENSE)
![Quality Score](https://img.shields.io/badge/Quality-8.5%2F10-green)
![Test Coverage](https://img.shields.io/badge/Coverage-35%25-yellow)
![Tests](https://img.shields.io/badge/Tests-23%2F23%20passing-brightgreen)

Home Assistant Integration für **Theben LUXORliving KNX/IP Gateways** mit automatischer Geräteerkennung aus LXP-Projektdateien.

> ⚠️ **Beta Status**: Diese Integration ist funktionsfähig, aber noch in aktiver Entwicklung. Sensor-, Climate- und Cover-Plattformen sind noch nicht vollständig implementiert.
> 
> ✅ **Getestet**: 23/23 Tests passing, Quality Score 8.5/10, Production-ready für Light & Switch Plattformen

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

**Theben LUXORPlug** → **Datei** → **Exportieren** → **LXP-Datei speichern** → Auf HA Server (z.B. `/config/luxor/projekt.lxp`)

### Schritt 2: Integration hinzufügen

**Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen** → **LUXORliving**

**Setup:**
1. LXP-Datei Pfad (z.B. `/config/luxor/mein_projekt.lxp`)
2. Gateway IP & Port (Standard: 3671)
3. Connection Type: Tunneling (empfohlen)
4. Optional: Simulation Mode aktivieren

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

| Plattform           | Status       | Features                        |
| ------------------- | ------------ | ------------------------------- |
| 💡 **Light**         | ✅ Production | On/Off, Dimming, Status Updates |
| 🔌 **Switch**        | ✅ Production | On/Off, Status Updates          |
| 📊 **Binary Sensor** | ✅ Production | Status Updates                  |
| 🌡️ **Sensor**        | ⚠️ Beta       | Basis-Implementation            |
| 🪟 **Cover**         | ⚠️ Planned    | Noch nicht implementiert        |
| 🌡️ **Climate**       | ⚠️ Planned    | Noch nicht implementiert        |

---

## 🧪 Simulation Mode (Dry-Run)

Testen ohne echte Hardware: **Einstellungen** → **Geräte & Dienste** → **LUXORliving** → **Optionen** → **Simulation Mode aktivieren**

---

## 🛠️ Troubleshooting

Siehe [QUICKSTART.md](docs/QUICKSTART.md) für detaillierte Fehlerbehebung.

**Häufige Probleme:**
- **Integration lädt nicht** → Logfile prüfen: `tail -f /config/home-assistant.log | grep luxor_living`
- **LXP-Datei nicht erkannt** → Absoluten Pfad verwenden, Dateiberechtigungen prüfen
- **Gateway nicht erreichbar** → IP/Port prüfen (Standard: 3671), Firewall checken

---

## 📚 Dokumentation

- 📖 [Schnellstart-Anleitung](docs/QUICKSTART.md) – Komplettes Setup & Troubleshooting
- 🔧 [KNX Implementation](docs/KNX_IMPLEMENTATION.md) – Technische Details
- 📊 [Test Report](docs/TEST_REPORT.md) – Test-Status & Coverage
- 🔍 [Quality Audit](docs/QUALITY_AUDIT.md) – Code-Qualitätsanalyse
- 🐞 [Issue Tracker](https://github.com/phismith91/luxorliving/issues) – Bugs & Feature Requests

---


## 📝 Lizenz

Dieses Projekt steht unter der [LICENSE](LICENSE).

---

## 📊 Qualität

- ✅ **23/23 Tests passing** – [Test Report](docs/TEST_REPORT.md)
- ✅ **Quality Score: 8.5/10** – [Quality Audit](docs/QUALITY_AUDIT.md)
- ✅ **35% Coverage** (config_flow 88%, knx_gateway 77%)

---

## 🤝 Beitragen

Pull Requests sind willkommen! Siehe [QUICKSTART.md](docs/QUICKSTART.md) für Development Setup.

---

## 🙏 Credits

- **[Theben AG](https://www.theben.de/)** – LUXORliving System
- **[xknx Library](https://github.com/XKNX/xknx)** – KNX/IP Kommunikation
- **Home Assistant Community** – Framework & Support

---

**Viel Erfolg mit deiner LUXORliving Integration! 🏠✨**
