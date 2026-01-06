# GitHub Copilot Instructions - LUXORliving Integration

> **Note:** Allgemeine Projekt-Infos, Setup-Commands und Testing-Guidelines sind in [AGENTS.md](/AGENTS.md) dokumentiert.  
> **Projekt-Context und Architektur:** Siehe [.github/copilot/CONTEXT.md](/.github/copilot/CONTEXT.md)  
> **Context Engineering Skills:** Siehe [.github/copilot/skills/](/.github/copilot/skills/)

---

## 🚀 Remote Deployment Workflow

### SSH-Verbindung zu Production HA

**WICHTIG:** Development und Testing erfolgt auf Remote HA via SSH!

**Connection Details:**
- **Host:** 100.97.159.88 (via Tailscale VPN)
- **User:** phil
- **Auth:** SSH-Key (`~/.ssh/id_rsa`) - passwortlos
- **Target:** `/config/custom_components/luxor_living/` (root-owned, needs `sudo`)
- **System:** Home Assistant OS mit s6-overlay (nicht systemd!)

### SSH-Besonderheiten

**CRITICAL:** Lokale `~/.ssh/config` hat ungültige Einträge!

**Lösung:** Immer `-F /dev/null` verwenden:
```bash
ssh -F /dev/null phil@100.97.159.88 "command"
GIT_SSH_COMMAND='ssh -F /dev/null' git push
```

**System-Details:**
- Init: s6-overlay (nicht systemd)
- SSH: `/etc/ssh/authorized_keys` (nicht `~/.ssh/authorized_keys`)
- HA Restart via SSH: **funktioniert nicht** → UI verwenden

### Deployment zu Remote HA

**3-Step Process:**

```bash
# Step 1: Sync zu Temp (als User phil)
ssh -F /dev/null phil@100.97.159.88 "mkdir -p /tmp/luxor_deploy"
rsync -avz --exclude="__pycache__" \
  -e "ssh -F /dev/null" \
  custom_components/luxor_living/ \
  phil@100.97.159.88:/tmp/luxor_deploy/

# Step 2: Copy mit sudo (files owned by root)
ssh -F /dev/null phil@100.97.159.88 \
  "sudo cp -r /tmp/luxor_deploy/* /config/custom_components/luxor_living/ && \
   rm -rf /tmp/luxor_deploy"

# Step 3: HA Restart (manuell!)
# → http://100.97.159.88:8123
# → Einstellungen → System → Neustart
```

### Pre-Release Testing Checklist

1. ✅ Deploy zu Remote HA (siehe oben)
2. ✅ HA neustarten (via UI)
3. ✅ Integration konfigurieren
4. ✅ Options Flow testen
5. ✅ Diagnostik herunterladen
6. ✅ Services aufrufen
7. ✅ HA Logs prüfen
8. ✅ Bei Erfolg → Release erstellen

---

## 📦 Release-Prozess

### Vor jedem Release

**1. Tests laufen lassen:**
```bash
python -m pytest tests/ -v
# ERWARTUNG: Alle Tests passing
```

**2. Optional:** Deploy + Test auf Remote HA (siehe oben)

**3. Version bumpen:**
- `custom_components/luxor_living/manifest.json` → "version"
- `CHANGELOG.md` aktualisieren

**4. Git Operations (mit SSH workaround!):**
```bash
git add -A
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Release notes..."

# IMPORTANT: Use -F /dev/null for git operations!
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin main
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin vX.Y.Z
```

**5. GitHub Release erstellen:**
```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z - Title" \
  --notes-file RELEASE_NOTES.md \
  --latest
```

### Nach Release

- ✅ Release Notes committen
- ✅ Archiv aufräumen (falls gewünscht)
- ✅ `CHANGELOG.md` für nächste Version vorbereiten

---

## 🔒 Security Guidelines

### SSH Key Authentication

**Setup:**
- Local: `~/.ssh/id_rsa`
- Remote: `/etc/ssh/authorized_keys` (auf HA-Server)
- **NEVER commit** SSH keys oder credentials!

### Credentials Management

**NEVER commit:**
- Passwords, tokens, API keys
- SSH private keys
- Deployment scripts mit hardcoded credentials

**Bei versehentlichem Commit:**

```bash
# 1. History zurücksetzen
git reset --hard HEAD~N  # N = Anzahl Commits

# 2. Force push (mit SSH workaround!)
GIT_SSH_COMMAND='ssh -F /dev/null' git push -f origin main

# 3. Tags löschen
git tag -d vX.Y.Z
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin :refs/tags/vX.Y.Z

# 4. GitHub Release löschen
gh release delete vX.Y.Z -y

# 5. SOFORT Credential ändern!
```

### Deployment Scripts

- ✅ SSH-Key Auth → können committet werden
- ✅ Template-Skripte ohne Credentials committen
- ❌ Hardcoded Passwords → `.gitignore`

---

## 🔗 Wichtige Links

- **Projekt Setup & Tests:** [AGENTS.md](/AGENTS.md)
- **Projekt Context:** [.github/copilot/CONTEXT.md](/.github/copilot/CONTEXT.md)
- **Repository:** https://github.com/phismith91/luxorliving
- **Issues:** https://github.com/phismith91/luxorliving/issues
