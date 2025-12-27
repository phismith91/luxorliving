# GitHub Copilot Instructions - LUXORliving Integration

## 🚀 Deployment & Testing

### SSH-Verbindung für Pre-Release Tests

**WICHTIG:** Für Tests vor offiziellen Releases steht eine SSH-Verbindung zum Remote Home Assistant zur Verfügung:

- **Host:** 100.97.159.88 (via Tailscale VPN)
- **User:** phil
- **Authentifizierung:** SSH-Key (passwortlos)
- **SSH-Key:** `~/.ssh/id_rsa` (Public Key in `/etc/ssh/authorized_keys` auf HA-Server)
- **Zielverzeichnis:** `/config/custom_components/luxor_living/` (root-owned, benötigt sudo)
- **System:** Home Assistant OS mit s6-overlay Init-System

### System-Architektur

**Home Assistant OS Details:**
- **Init-System:** s6-overlay (nicht systemd)
- **SSH-Service:** Verwaltet über s6 (`/etc/s6-overlay/s6-rc.d/sshd/`)
- **HA Config:** `/config/` (gemountetes Volume)
- **SSH Auth:** Public Keys in `/etc/ssh/authorized_keys` (nicht `~/.ssh/authorized_keys`)

**SSH-Konfiguration:**
- SSH läuft standardmäßig nach Installation
- Key Authentication über `/etc/ssh/authorized_keys`
- Keine Passwort-Authentication für Sicherheit

### SSH-Service Verwaltung (s6):
```bash
# SSH-Status überprüfen
ssh phil@100.97.159.88 "ps aux | grep sshd"

# SSH-Service neu starten (falls nötig)
ssh phil@100.97.159.88 "sudo s6-svc -r /run/s6/services/sshd"
```

### SSH-Key Authentifizierung:
   - SSH-Key in `~/.ssh/id_rsa` (lokal)
   - Public Key in `/etc/ssh/authorized_keys` auf HA-Server
   - Keine Passwörter in Skripten oder Code nötig

2. **Bei versehentlichem Commit von Credentials:**
   ```bash
   # History zurücksetzen
   git reset --hard HEAD~N  # N = Anzahl Commits
   GIT_SSH_COMMAND='ssh -F /dev/null' git push -f origin main
   
   # Tags löschen
   git tag -d vX.Y.Z
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin :refs/tags/vX.Y.Z
   
   # GitHub Release löschen
   gh release delete vX.Y.Z -y
   
   # SOFORT Passwort/Key ändern!
   ```

3. **Deployment-Skripte:**
   - Können jetzt sicher mit SSH-Key committet werden
   - Keine Credentials im Code erforderlich
   - In `.gitignore` aufnehmen wenn sie Credentials enthalten
   - Oder: Template-Skript ohne Credentials committen

### Deployment-Workflow

**SSH-Besonderheiten:**
- Lokale `~/.ssh/config` hat ungültige Einträge → **immer `-F /dev/null` verwenden**
- Git-Operationen: `GIT_SSH_COMMAND='ssh -F /dev/null' git push`
- HA-Dateien gehören root → `sudo` für File-Operationen verwenden
- HA Restart via SSH funktioniert nicht → manuelle Nutzung über UI notwendig

**Empfohlener Deployment-Ansatz (mit SSH-Key):**

```bash
# Deployment mit SSH-Key (passwortlos - bereits konfiguriert)
ssh -F /dev/null -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no phil@100.97.159.88 "command"

# Oder rsync für Datei-Transfers:
rsync -avz --exclude="__pycache__" \
  -e "ssh -F /dev/null -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no" \
  custom_components/luxor_living/ \
  phil@100.97.159.88:/tmp/luxor_deploy/
```

### Deployment-Ablauf

1. **Sync zu Temp-Verzeichnis** (als User phil):
   ```bash
   ssh -F /dev/null phil@100.97.159.88 "mkdir -p /tmp/luxor_deploy"
   rsync -avz --exclude="__pycache__" \
     -e "ssh -F /dev/null" \
     custom_components/luxor_living/ \
     phil@100.97.159.88:/tmp/luxor_deploy/
   ```

2. **Copy mit sudo zu final location**:
   ```bash
   ssh -F /dev/null phil@100.97.159.88 \
     "sudo cp -r /tmp/luxor_deploy/* /config/custom_components/luxor_living/ && \
      rm -rf /tmp/luxor_deploy"
   ```

3. **HA Restart**: Manuell über UI (http://100.97.159.88:8123)
   - Einstellungen → System → Neustart

### Testing vor Release

1. Deploy zu Remote HA
2. HA neustarten
3. Features testen:
   - Integration konfigurieren
   - Options Flow testen
   - Diagnostik herunterladen
   - Services aufrufen
4. HA Logs prüfen
5. Bei Erfolg → Release erstellen

---

## 📦 Release-Prozess

### Vor jedem Release

1. **Tests laufen lassen:**
   ```bash
   python -m pytest tests/ -v
   # ERWARTUNG: Alle Tests passing
   ```

2. **Optional: Deployment zu Remote HA für Pre-Release Testing**

3. **Version bumpen:**
   - `custom_components/luxor_living/manifest.json` → "version" field
   - `CHANGELOG.md` aktualisieren

4. **Git Operations:**
   ```bash
   git add -A
   git commit -m "Release vX.Y.Z"
   git tag -a vX.Y.Z -m "Release notes..."
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin main
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin vX.Y.Z
   ```

5. **GitHub Release erstellen:**
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z - Title" \
     --notes-file RELEASE_NOTES.md --latest
   ```

### Nach Release

- Release Notes committen
- Alte Release Notes ins Archiv verschieben (falls gewünscht)
- CHANGELOG.md für nächste Version vorbereiten

---

## ⚠️SSH-Key Authentifizierung:**
   - SSH-Key in `~/.ssh/id_rsa` (lokal)
   - Public Key in `/etc/ssh/authorized_keys` auf HA-Server
   - Keine Passwörter in Skripten oder Code nötig

2. **Bei versehentlichem Commit von Credentials:**
   ```bash
   # History zurücksetzen
   git reset --hard HEAD~N  # N = Anzahl Commits
   GIT_SSH_COMMAND='ssh -F /dev/null' git push -f origin main
   
   # Tags löschen
   git tag -d vX.Y.Z
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin :refs/tags/vX.Y.Z
   
   # GitHub Release löschen
   gh release delete vX.Y.Z -y
   
   # SOFORT Passwort/Key ändern!
   ```

3. **Deployment-Skripte:**
   - Können jetzt sicher mit SSH-Key committet werden
   - Keine Credentials im Code erforderlich
   - In `.gitignore` aufnehmen wenn sie Credentials enthalten
   - Oder: Template-Skript ohne Credentials committen

---

## 🏗️ Projekt-Struktur

- `custom_components/luxor_living/` - Integration Code
- `tests/` - Unit Tests (pytest)
- `docs/` - Dokumentation
- `scripts/` - Utility-Skripte (OHNE Credentials!)

## 📊 Quality Gates

- ✅ Alle Tests passing (pytest)
- ✅ Code formatiert (black, isort)
- ✅ Type checking (mypy)
- ✅ Optional: Pre-Release Testing via SSH auf Remote HA
- ✅ Dokumentation aktuell

## 🔗 Wichtige Links

- Repository: https://github.com/phismith91/luxorliving
- Issues: https://github.com/phismith91/luxorliving/issues
- HA Forum: [Link wenn vorhanden]
