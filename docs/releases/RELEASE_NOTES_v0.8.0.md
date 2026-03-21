# LUXORliving v0.8.0 — HA Quality Scale Bronze/Silver/Gold

## Highlights

Dieses Release implementiert alle Bronze-, Silber- und Gold-Anforderungen der
[HA Integration Quality Scale](https://www.home-assistant.io/docs/quality_scale/).

## Neu

- **Reauth-Flow**: `async_step_reauth` — abgelaufene Credentials lösen HA's
  native Re-Authentifizierung aus statt eines harten Fehlers
- **Entity Availability**: Entities werden unavailable wenn die KNX-Gateway-
  Verbindung verloren geht; Write-Aktionen werfen `HomeAssistantError`
- **`async_step_reconfigure`**: LXP-Projektdatei über 3-Punkte-Menü aktualisieren
  ohne Gateway-Daten neu eingeben zu müssen
- **Integration Icon**: Eigenes `icon.png` (512×512)

## Geändert

- **`entry.runtime_data`**: Globale `_integration_states`-Registry entfernt;
  alle Plattform- und Push-Dateien nutzen jetzt `entry.runtime_data` direkt
  (Bronze, HA 2024+ Standard)
- **Unique config entry**: Doppelte Einträge mit gleicher Gateway-IP werden
  verhindert (Bronze)
- **`PARALLEL_UPDATES`**: Auf allen 6 Plattform-Dateien gesetzt
  (`= 1` für Write-Plattformen, `= 0` für Read-only) (Silber)
- **Diagnostic entities**: Health-Sensor und Auto-Discovery-Sensoren als
  `EntityCategory.DIAGNOSTIC` markiert und standardmäßig deaktiviert (Gold)
- **Setup-Wizard vereinfacht**: Push-Webhook-Einstellungen nur noch in Options
- **Verbindungstyp-Auswahl**: Lesbare Labels statt Rohwerte

## Fehlerbehebungen

- pre-commit: prettier v4.0.0-alpha.8 Regression behoben
- QA Matrix: PlantUML Docker-Pfade korrigiert
