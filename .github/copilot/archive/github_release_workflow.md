---
description: GitHub Release Workflow - Token ist bereits vorhanden!
applyTo: '**'
priority: 1000
---

# ⚠️ KRITISCH: GitHub Token Setup

## 🔑 TOKEN IST BEREITS VORHANDEN
```bash
~/.github-token
```

## ✅ STANDARD-WORKFLOW FÜR RELEASES

### 1. Release Notes erstellen
```bash
cat > /tmp/release_notes.md << 'EOF'
## Release Title
... content ...
EOF
```

### 2. Python Release Script erstellen
```bash
cat > /tmp/create_github_release.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import json, urllib.request, urllib.error, sys, os

token = os.environ.get('GITHUB_TOKEN')
if not token:
    print("❌ GITHUB_TOKEN fehlt!")
    sys.exit(1)

with open('/tmp/release_notes.md', 'r') as f:
    body = f.read()

release_data = {
    "tag_name": "v0.x.x-beta.x.x",  # Anpassen!
    "target_commitish": "feature/initial-state-reading",
    "name": "Release Title",  # Anpassen!
    "body": body,
    "draft": False,
    "prerelease": True
}

url = 'https://api.github.com/repos/phismith91/luxorliving/releases'
headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {token}',
    'X-GitHub-Api-Version': '2022-11-28',
    'Content-Type': 'application/json'
}

data = json.dumps(release_data).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"✅ Release erstellt: {result['html_url']}")
except Exception as e:
    print(f"❌ Fehler: {e}")
    sys.exit(1)
PYTHON_EOF
chmod +x /tmp/create_github_release.py
```

### 3. Release erstellen (ONE-LINER)
```bash
GITHUB_TOKEN=$(cat ~/.github-token) python3 /tmp/create_github_release.py
```

## ❌ NICHT TUN
- ❌ NICHT nach Token fragen
- ❌ NICHT User auffordern, Token einzugeben
- ❌ NICHT manuelle Browser-Schritte vorschlagen wenn Token existiert

## ✅ TUN
- ✅ Token automatisch aus `~/.github-token` laden
- ✅ Release direkt erstellen
- ✅ Nur bei Fehler eskalieren

## 📋 Vollständiges Beispiel (Beta 7.6)
```bash
# 1. Notes
cat > /tmp/release_notes.md << 'EOF'
## 🔍 Beta 7.6: Debug-Logging
...
EOF

# 2. Script (siehe oben)

# 3. Release
GITHUB_TOKEN=$(cat ~/.github-token) python3 /tmp/create_github_release.py
# ✅ Release erfolgreich erstellt!
# 🔗 https://github.com/phismith91/luxorliving/releases/tag/v0.2.6-beta.7.6
```

## 🎯 Erfolgreiche Verwendung
- ✅ 23. Dezember 2025: Beta 7.6 Release erfolgreich erstellt
- ✅ Token-Location dokumentiert: `~/.github-token`
