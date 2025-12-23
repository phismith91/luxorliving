# LUXORliving Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/phismith91/luxorliving.svg)](https://github.com/phismith91/luxorliving/releases)
[![License](https://img.shields.io/github/license/phismith91/luxorliving.svg)](LICENSE)
![Quality Score](https://img.shields.io/badge/Quality-8.5%2F10-green)
![Test Coverage](https://img.shields.io/badge/Coverage-35%25-yellow)
![Tests](https://img.shields.io/badge/Tests-23%2F23%20passing-brightgreen)

Home Assistant Integration für **Theben LUXORliving KNX/IP Gateways** (BAOS 777) mit automatischer Geräteerkennung aus LXP-Projektdateien.

> ✅ **Production-Ready**: Voll funktionsfähig für Light & Switch Plattformen. 58/58 Tests passing, Quality Score 8.5/10, 52% Coverage.
> 
> ⚠️ **Partial Beta**: Sensor-, Climate- und Cover-Plattformen noch in Entwicklung.

---

## 🎉 Neuigkeiten (v0.3.0-beta.1)

### Beta 1.0 - Quality Audit Improvements (23. Dez 2025)
- 🔒 **Security:** TLS 1.2+ (deprecated TLSv1 entfernt)
- ✅ **Code Quality:** Exception Handling spezifischer (18 → 0 broad exceptions)
- 📊 **Testing:** Coverage Measurement aktiviert (52% baseline)
- ⚡ **UX:** Routing-Mode Validierung in Config Flow
- 🧹 **Logging:** Emojis nur noch in Debug-Level (Production-Logs sauber)

Siehe [QUALITY_IMPROVEMENTS.md](docs/QUALITY_IMPROVEMENTS.md) für Details.

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

### Hauptdokumentation
- 📖 [Installation & Setup](docs/INSTALLATION.md) – HACS, Manuelle Installation, Config Flow
- 🚀 [Schnellstart V2](docs/QUICKSTART_V2.md) – Komplettes Setup mit Best Practices
- 🔧 [KNX Implementation](docs/KNX_IMPLEMENTATION.md) – Technische KNX-Details

### Architektur & Entscheidungen
- 🏗️ [Architecture Decision](docs/ARCHITECTURE_DECISION.md) – Warum Native Integration?
- ⚠️ [BAOS REST API Limitations](docs/BAOS_REST_API_LIMITATIONS.md) – Beta 7.x Erkenntnisse
- 📡 [BAOS REST API Discovery](docs/BAOS_REST_API_DISCOVERY.md) – API Dokumentation
- 🔐 [Tunneling Authentication](docs/TUNNELING_AUTHENTICATION.md) – BAOS 777 Setup

### Quality & Tests
- ✅ [Test Review](docs/TEST_REVIEW.md) – 23/23 Tests passing
- 🔍 [Quality Audit](docs/QUALITY_AUDIT.md) – Code Score 8.5/10
- 🎯 [Agent Reviews](docs/AGENT_REVIEWS.md) – Development Insights

---

## 🔧 Technische Highlights

### KNX Kommunikation
- **Tunneling Mode** mit REST API Authentication (BAOS 777)
- **XKNX Library** v3.11.0 für KNX/IP Protokoll
- **GroupValueRead** für Initial States (~30ms pro Light)
- **Telegram Listener** für Live-Updates

### REST API Integration
- ✅ Login & Session Management
- ✅ Tunneling Control (`/rest/device/authtunneling`)
- ❌ ~~Datapoint Mapping~~ (siehe BAOS_REST_API_LIMITATIONS.md)

### Performance
- **Startup:** ~800ms für 27 Lights (GroupValueRead)
- **Live Updates:** <1s für physische Schalter-Events
- **BAOS Cache:** Keine Bus-Belastung

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
