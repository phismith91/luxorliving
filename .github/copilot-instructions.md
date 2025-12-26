# GitHub Copilot Instructions - LUXORliving Integration

## 🚀 Deployment & Testing

### SSH-Verbindung für Pre-Release Tests

**WICHTIG:** Für Tests vor offiziellen Releases steht eine SSH-Verbindung zum Remote Home Assistant zur Verfügung:

- **Host:** 100.97.159.88 (via Tailscale VPN)
- **User:** phil
- **Passwort:** NIEMALS in Skripte oder Code schreiben!
- **Zielverzeichnis:** `/config/custom_components/luxor_living/` (root-owned, benötigt sudo)

### Deployment-Workflow

**ACHTUNG: Passwort-Sicherheit beachten!**

Beim Erstellen von Deployment-Skripten:
- ✅ Passwort als Umgebungsvariable oder Prompt verwenden
- ✅ Skripte mit `.gitignore` ausschließen wenn Credentials enthalten
- ❌ NIEMALS Passwörter in Git committen
- ❌ NIEMALS Credentials in GitHub pushen

**Empfohlener Deployment-Ansatz:**

```bash
# Deployment ohne Passwort im Skript
read -sp "HA Passwort: " HA_PASSWORD
sshpass -p "$HA_PASSWORD" ssh -F /dev/null \
  -o StrictHostKeyChecking=no phil@100.97.159.88 "command"
```

**SSH-Besonderheiten:**
- Lokale `~/.ssh/config` hat ungültige Einträge → immer `-F /dev/null` verwenden
- Git-Operationen: `GIT_SSH_COMMAND='ssh -F /dev/null' git push`
- HA-Dateien gehören root → `sudo` für File-Operationen verwenden
- HA Restart via SSH funktioniert nicht → manuelle Nutzung über UI notwendig

### Deployment-Ablauf

1. **Sync zu Temp-Verzeichnis** (als User phil):
   ```bash
   ssh phil@100.97.159.88 "mkdir -p /tmp/luxor_deploy"
   rsync -avz --exclude="__pycache__" custom_components/luxor_living/ \
     phil@100.97.159.88:/tmp/luxor_deploy/
   ```

2. **Copy mit sudo zu final location**:
   ```bash
   ssh phil@100.97.159.88 "sudo cp -r /tmp/luxor_deploy/* \
     /config/custom_components/luxor_living/ && \
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

## ⚠️ Security Best Practices

1. **Niemals Credentials committen:**
   - Keine Passwörter in Skripten
   - Keine API-Tokens in Code
   - Keine SSH-Keys im Repository

2. **Bei versehentlichem Commit:**
   ```bash
   # History zurücksetzen
   git reset --hard HEAD~N  # N = Anzahl Commits
   GIT_SSH_COMMAND='ssh -F /dev/null' git push -f origin main
   
   # Tags löschen
   git tag -d vX.Y.Z
   GIT_SSH_COMMAND='ssh -F /dev/null' git push origin :refs/tags/vX.Y.Z
   
   # GitHub Release löschen
   gh release delete vX.Y.Z -y
   
   # SOFORT Passwort ändern!
   ```

3. **Deployment-Skripte:**
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
