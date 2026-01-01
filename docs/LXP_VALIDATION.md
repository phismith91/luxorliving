# LXP Validation Tool

## 📋 Übersicht

Das `validate_lxp.py` Skript validiert LUXORliving LXP-Projektdateien auf häufige Probleme und bietet detaillierte Berichte über Konfigurationsprobleme.

## 🚀 Verwendung

```bash
# Grundlegende Verwendung
python3 scripts/validate_lxp.py <pfad_zur_lxp_datei>

# Beispiel
python3 scripts/validate_lxp.py docs/Hauptwohnung.lxp
```

## 🔍 Validierungsprüfungen

### 1. **Dateizugriff**
- Überprüft, ob die LXP-Datei existiert und lesbar ist

### 2. **Geräte ohne Datenpunkte**
- **Schweregrad:** Warnung
- **Kategorie:** Configuration
- Identifiziert Geräte ohne konfigurierte KNX-Datenpunkte
- Diese Geräte erzeugen keine Home Assistant Entities

### 3. **Duplizierte Adressen**
- **Schweregrad:** Fehler
- **Kategorie:** Addressing
- Prüft auf mehrere Geräte mit derselben KNX-Adresse
- Jedes Gerät muss eine eindeutige Adresse haben

### 4. **Gateway-Konfiguration**
- **Schweregrad:** Fehler
- **Kategorie:** Gateway
- Validiert Gateway-IP-Adresse und Port
- Standard KNX/IP Port: 3671

### 5. **Sensoren/Aktuatoren ohne Datenpunkte**
- **Schweregrad:** Info
- **Kategorie:** Configuration
- Zeigt Sensoren/Aktuatoren ohne Datenpunkte an

### 6. **Namenskonventionen**
- **Schweregrad:** Info/Warnung
- **Kategorie:** Naming
- Prüft auf zu lange oder fehlende Gerätenamen

## 📊 Ausgabe

Das Skript generiert einen detaillierten Bericht mit:

1. **Projekt-Statistiken**
   - Projektname
   - Gateway-Konfiguration
   - Anzahl Geräte, Sensoren, Aktuatoren
   - Gesamtanzahl Datenpunkte

2. **Validierungsergebnisse**
   - Gruppiert nach Schweregrad (Fehler, Warnungen, Info)
   - Detaillierte Problembeschreibungen
   - Lösungsvorschläge

3. **Zusammenfassung**
   - Anzahl Fehler, Warnungen, Infos
   - Gesamtstatus (PASSED/FAILED)

## ⚙️ Exit Codes

- **0**: Validation erfolgreich (keine Fehler)
- **1**: Validation fehlgeschlagen (Fehler gefunden)

## 🔧 Integration im Workflow

### Pre-Commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
if ls *.lxp 1> /dev/null 2>&1; then
    for file in *.lxp; do
        python3 scripts/validate_lxp.py "$file" || exit 1
    done
fi
```

### CI/CD Pipeline
```yaml
# .github/workflows/validate-lxp.yml
- name: Validate LXP Files
  run: |
    find . -name "*.lxp" -exec python3 scripts/validate_lxp.py {} \;
```

## 📝 Beispiel-Ausgabe

```
🔍 Validating LXP file: Hauptwohnung.lxp
============================================================

📊 Project Statistics:
  • Project: Hauptwohnung
  • Gateway: 192.168.8.226:3671
  • Devices: 63
  • Sensors: 122
  • Actuators: 57
  • Datapoints: 851

⚠️  9 device(s) without datapoints (14.3%)

============================================================
🔍 Validation Results:
============================================================

⚠️  Warnings (9):
  • [CONFIGURATION] Device has no datapoints configured
    Device: Taster Diele EG Ankleide 2C13
    Address: 9.0.35
    💡 Check KNX programming in LUXORplug and assign group addresses

============================================================
Summary: 0 errors, 9 warnings, 0 info
⚠️  Validation passed with warnings - Review warnings for best results
```

## 🛠️ Erweiterte Validierung

### Benutzerdefinierte Prüfungen hinzufügen

Füge neue Validierungen in der `LXPValidator` Klasse hinzu:

```python
def _check_custom_rule(self, project) -> None:
    """Custom validation rule."""
    # Implementierung hier
    pass
```

Registriere die Prüfung in der `validate()` Methode:

```python
async def validate(self) -> bool:
    # ... existing code ...
    self._check_custom_rule(project)
    # ... rest of validation ...
```

## 📚 Weitere Informationen

- **Parser-Dokumentation:** [lxp_parser.py](../custom_components/luxor_living/lxp_parser.py)
- **Audit-Bericht:** [LXP_AUDIT_HAUPTWOOHNUNG.md](LXP_AUDIT_HAUPTWOOHNUNG.md)
- **Tests:** [test_lxp_parser.py](../tests/test_lxp_parser.py)
