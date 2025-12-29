# Release Notes v0.3.3

**Release Date:** 26. Dezember 2025

## 🔧 Infrastructure Improvements

### SSH Key Authentication Setup
- **SSH-Key Deployment** für Remote HA Testing
  - Passwortlose SSH-Verbindung zu Remote Home Assistant (via Tailscale)
  - Public Key in `/etc/ssh/authorized_keys` installiert
  - Vereinfachter Deployment-Workflow für Pre-Release Testing

### Documentation Updates
- Agent-Anweisungen aktualisiert (`.github/copilot-instructions.md`)
- Release-Prozess dokumentiert mit SSH-Key Authentication
- Deployment-Best-Practices für Remote HA Testing
- Security Guidelines für sichere Credential-Verwaltung

## 📋 Previous Features (from v0.3.2)
Alle Premium UI Features aus v0.3.2 sind enthalten:
- ✅ Device Configuration URL
- ✅ Reload Service (`luxor_living.reload`)
- ✅ Diagnostics Support (Download über UI)
- ✅ Options Flow (UI-basierte Konfiguration)

## 🐛 Bug Fixes (from v0.3.2)
- Fixed Options Flow 500 Internal Server Error
- Fixed Diagnostics AttributeError
- Added missing `services.yaml` file

## 🔧 Installation

### Via HACS (empfohlen)
1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. Repository: `https://github.com/phismith91/luxorliving`
3. Kategorie: Integration
4. Installation und HA Neustart

### Manuell
1. Download von [GitHub Releases](https://github.com/phismith91/luxorliving/releases/tag/v0.3.3)
2. Entpacken nach `custom_components/luxor_living/`
3. Home Assistant neustarten
4. Konfiguration via UI: Einstellungen → Geräte & Dienste → Integration hinzufügen → "LUXORliving"

## 📝 Testing Status
- ✅ 86 Unit Tests passing
- ✅ SSH-Key Authentication funktioniert
- ✅ Remote Deployment via Tailscale getestet

## 🔗 Links
- [Vollständige Dokumentation](https://github.com/phismith91/luxorliving/blob/main/docs/README.md)
- [Installationsanleitung](https://github.com/phismith91/luxorliving/blob/main/docs/INSTALLATION.md)
- [Issue Tracker](https://github.com/phismith91/luxorliving/issues)
