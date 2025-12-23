# Changelog

Alle wichtigen Änderungen für das LUXORliving Home Assistant Integration werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/).

---

## [0.2.12] - 2025-12-23

### ✨ Highlights

- **Log Enrichment**: GroupAddress→Entity und IndividualAddress→Device Labels in Log-Ausgaben für bessere Traceability
- **Dimmable Light Brightness**: Status% (2/3/0) wird initial gelesen und kontinuierlich überwacht
- **Event Loop Safety**: Robuste Callback-Scheduling mit Test-Time Fallback für HA-Loop Absence

### Added

- `knx_gateway.py`:
  - `set_group_address_labels()` - Setzt GA→Entity Label-Map für Log-Enrichment
  - `set_individual_address_labels()` - Setzt IA→Device Label-Map für Log-Enrichment
  - GA und IA Labels in Log-Ausgaben (📥 Received KNX telegram mit Source IA Name und Destination GA Entity Name)
  - Fallback auf direkte Callback-Invokation wenn HA Event Loop nicht verfügbar (Test-Sicherheit)

- `entity_mapper.py`:
  - `get_group_address_label_map()` - Erzeugt GA→["Entity Name (ID)"] Map
  - `get_individual_address_label_map()` - Erzeugt IA→["Device Name (DeviceID)"] Map

- `light.py`:
  - `LuxorLivingDimmableLight._address_dim_status` - Zusätzliche Status%-Adresse (2/3/0) Listener
  - Initial Read auf Status%-Adresse für Brightness-Initialisierung
  - `knx_address_dim_status` als Extra-Attribut für Dimmbare Lichter

- Test Updates:
  - Dual Listener Tests für Light und Switch
  - KNX Initial Read Tests (keine REST-basierte Initialisation mehr)
  - Gateway Callback Scheduling Tests mit HA-Loop Fallback

### Changed

- Log-Ausgaben enthalten nun Human-readable Namen statt nur GroupAddress/IndividualAddress Nummern
- Dimmbare Lichter hören auf 2 Adressen: `Dimmen%` (2/2/0) und `Status%` (2/3/0)
- Tests: Erwartungen angepasst an Dual-Listener Architektur und KNX-Only Initial Reads

### Fixed

- Brightness-Updates auf Dimmable Lights unterstützen nun beide Dimmen% und Status% Adressen
- HA Event Loop-Absence führt nicht mehr zu Callback-Scheduling-Fehlern (Test-Compatibility)
- Log-Tracing ist nun bidirektional erkennbar (wer sendet zu wem)

### Removed

- REST-basierte Initial Reads (vollständig auf KNX-Reads migriert)

### Quality

- ✅ **58/58 Tests Passing** (100%)
- ✅ **Code Quality Score:** 8.5/10
- ⚠️ **TLSv1 Deprecation Warnings** in rest_client.py (Minor)

### Technical Details

**Brightness Handling für Dimmbare Lichter:**
- Initial Read sendet Telegramme zu beiden Adressen
- Listener registriert auf Dimmen% (2/2/0) und Status% (2/3/0)
- `_handle_brightness_update()` kombiniert Updates von beiden Quellen
- Percent-zu-Brightness Konvertierung: `brightness = int((percent / 100) * 255)`

**Log Enrichment:**
- Gateway empfängt GA→Entity Map bei Setup (`set_group_address_labels()`)
- Gateway empfängt IA→Device Map bei Setup (`set_individual_address_labels()`)
- Beim Telegram-Empfang werden Labels vom Map nachgeschlagen und angezeigt
- Format: "📥 Received KNX telegram: Source IA: 9.0.12 (Device "Name"), Destination GA: 5/0/1 (Entity "light.badlicht")"

---

## [0.2.11] - 2025-12-20

### Added

- Dual KNX Listener Architecture für Light und Switch Entities
- Listeners auf STATUS und CONTROL Group Addresses
- Initial Reads auf KNX Addresses für State-Initialisierung
- `rest_client.py` für BAOS REST Authentication und Tunneling Management
- Integration der XKNX v3.11.0 für KNX/IP Kommunikation

### Features

- ✅ Light Platform mit Ein/Aus und Dimmen
- ✅ Switch Platform mit Ein/Aus Steuerung
- ✅ Binary Sensor Platform für Bewegungsmelder/Kontakte
- ✅ LXP-Parser für Theben LUXORliving Projekte
- ✅ Entity Mapper für automatische Entities aus LXP

### Testing

- 46 Tests für Core-Funktionen
- Simulation Mode für Tests ohne Hardware
- Config Flow Tests

---

## [0.2.10] und älter

Siehe Git-Historie für Details zu älteren Versionen.

---

## Roadmap

### Q1 2026

- 📅 **Cover Platform** (Jalousien, Rollläden)
- 📅 **Climate Platform** (Thermostate)
- 📅 **Sensor Platform** Verbesserungen

### Q2 2026

- 🔮 Multi-Device Support (mehrere Gateways)
- 🔮 Automations-Templates
- 🔮 Dashboard-Widgets

---

## Versionierung

Dieses Projekt folgt [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking Changes
- **MINOR**: Neue Features (Backwards-Compatible)
- **PATCH**: Bugfixes und Verbesserungen

---

**Für mehr Infos siehe [QUICKSTART.md](docs/QUICKSTART.md) und [docs/](docs/).**
