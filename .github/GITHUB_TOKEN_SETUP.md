# GitHub Token Setup - WICHTIG FÜR AGENTS

## 🔑 Token Location
**Das GitHub Personal Access Token ist gespeichert in:**
```
~/.github-token
```

## 🚀 Release erstellen (STANDARD-VERFAHREN)

### Methode 1: Direkt mit gespeichertem Token
```bash
cd /home/phil/gitlab_github/luxorliving
export GITHUB_TOKEN=$(cat ~/.github-token)
python3 /tmp/create_github_release.py
```

### Methode 2: One-Liner
```bash
GITHUB_TOKEN=$(cat ~/.github-token) python3 /tmp/create_github_release.py
```

## 📋 Release-Script Template
Das Python-Script `/tmp/create_github_release.py` wird automatisch erstellt und nutzt:
- Release Notes aus: `/tmp/release_notes.md`
- Token aus: `$GITHUB_TOKEN` Environment Variable oder `~/.github-token`

## ⚠️ FÜR ALLE AGENTS

**BEVOR ihr nach einem Token fragt:**
1. ✅ Prüft `~/.github-token`
2. ✅ Nutzt es direkt: `GITHUB_TOKEN=$(cat ~/.github-token)`
3. ❌ NICHT nach Token fragen wenn die Datei existiert!

**Standard-Ablauf für GitHub Releases:**
```bash
# 1. Release Notes erstellen
cat > /tmp/release_notes.md << 'EOF'
... Release Notes ...
EOF

# Optional: README für HACS vorbereiten
# Vor dem Erstellen des GitHub Release die README aktualisieren, damit HACS/HA nur das aktuelle Release anzeigt:
# ./scripts/update_readme_release.sh

# 2. Python-Script erstellen (falls nicht vorhanden)
cat > /tmp/create_github_release.py << 'PYTHON_EOF'
... Script Code ...
PYTHON_EOF

# 3. Release direkt erstellen
GITHUB_TOKEN=$(cat ~/.github-token) python3 /tmp/create_github_release.py
```

## 🔒 Token Permissions
Das Token hat `repo` Scope und wurde erstellt für:
- Release Creation
- Tag Management
- Repository Access

## 📝 Token erneuern (falls nötig)
```bash
# Neues Token erstellen:
https://github.com/settings/tokens/new?scopes=repo&description=CLI-Release

# Token speichern:
echo "ghp_xxxxxxxxxxxx" > ~/.github-token
chmod 600 ~/.github-token
```

## ✅ Erfolgreiche Verwendung
- ✅ Beta 7.6 Release: 23. Dezember 2025
- Token-Location: `~/.github-token` ← **MERKEN!**
