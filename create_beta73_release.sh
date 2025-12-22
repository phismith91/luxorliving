#!/bin/bash

# Beta 7.3 Release Script

RELEASE_TAG="v0.2.3-beta.7.3"
RELEASE_NAME="Beta 7.3 - SSL Blocking Fix + REST Datapoint Mapping"

RELEASE_BODY="## 🐛 Beta 7.3: Kritische Fixes für SSL und Datapoint Mapping

### 🚨 KRITISCHE FIXES

#### 1️⃣ SSL Blocking Call behoben
- **Problem**: \`ssl.create_default_context()\` blockierte den Home Assistant Event Loop
- **Symptom**: Home Assistant Warnung über blockierende Operationen
- **Lösung**: SSL Context wird jetzt asynchron in Executor erstellt
- **Ergebnis**: Keine Warnungen mehr, bessere Performance

#### 2️⃣ REST Datapoint Mapping korrigiert
- **Problem**: LXP-Datapoint-IDs ≠ BAOS-Datapoint-IDs
- **Symptom**: \`Datapoint 2322 not found\` - REST API konnte Datapoints nicht finden
- **Lösung**: Fetche echte BAOS Datapoints mit GroupAddress-Namen
- **Ergebnis**: Korrekte Mappings, REST API sollte jetzt funktionieren

---

### 📝 ÄNDERUNGEN IM DETAIL

#### \`rest_client.py\`
\`\`\`python
# NEU: SSL Context in Executor (nicht blockierend)
async def __aenter__(self):
    def create_ssl_context():
        ssl_context = ssl.create_default_context()
        # ... Konfiguration ...
        return ssl_context
    
    loop = asyncio.get_event_loop()
    ssl_context = await loop.run_in_executor(None, create_ssl_context)
\`\`\`

- ✅ Neue Methode: \`async_get_datapoint_details()\`
  - Fetcht vollständige Datapoint-Info inkl. GroupAddress \"name\"
  - Timeout: 2 Sekunden (konfigurierbar)
  - Gibt komplettes Dict zurück: {\"id\", \"name\", \"value\", \"type\", ...}

#### \`knx_gateway.py\`
\`\`\`python
# NEU: Echte BAOS Datapoints fetchen
async def _async_load_datapoint_mapping(self):
    datapoints = await self._rest_client.async_get_datapoints()
    
    for dp_ref in datapoints[:50]:  # Erste 50 Datapoints
        dp_details = await self._rest_client.async_get_datapoint_details(dp_id)
        if dp_details and \"name\" in dp_details:
            group_addr = dp_details[\"name\"]  # z.B. \"1/1/0\"
            self._datapoint_mapping[group_addr] = dp_id
\`\`\`

- ✅ Fetcht bis zu 50 Datapoints einzeln vom BAOS
- ✅ Extrahiert GroupAddress aus \"name\" Feld
- ✅ Baut korrekte Mappings: \`{\"1/1/0\": 2048, \"1/1/1\": 2049}\`
- ✅ Startup-Zeit: ~2 Sekunden zusätzlich (50 × ~40ms)

#### \`__init__.py\`
- ❌ **ENTFERNT**: Alte LXP-basierte Mapping-Funktion
- ✅ Mapping erfolgt jetzt automatisch in \`knx_gateway.async_setup()\`
- ✅ Keine doppelte Logik mehr

---

### 🧪 TEST-STATUS
\`\`\`
===== 58 passed, 6 warnings in 2.80s =====
\`\`\`

**Warnungen** (erwartet):
- 6× \`ssl.TLSVersion.TLSv1 is deprecated\` → Normal für BAOS 777 (altes TLS)

---

### 📊 ERWARTETE VERBESSERUNGEN

#### ✅ Keine Home Assistant Warnungen
- Vorher: \`Detected blocking call to load_default_certs\`
- Nachher: Keine SSL-Warnungen mehr

#### ✅ REST API findet Datapoints
- Vorher: \`Datapoint 2322 not found\` (68× im Log)
- Nachher: Korrekte BAOS Datapoint-IDs verwendet

#### ✅ Initiale Zustände via REST
- Vorher: Fallback zu GroupValueRead (stale cache)
- Nachher: REST API sollte echte Werte liefern

#### ⏱️ Startup-Zeit
- Zusätzlich: ~2 Sekunden (50 Datapoints × ~40ms)
- Akzeptabel für korrekte initiale Zustände

---

### 🚀 INSTALLATION

#### Via HACS (Empfohlen)
1. HACS → LUXORliving öffnen
2. \"Show beta versions\" aktivieren
3. **v0.2.3-beta.7.3** auswählen
4. Home Assistant neu starten

#### Manuell
\`\`\`bash
cd /config/custom_components/luxor_living
git fetch --tags
git checkout v0.2.3-beta.7.3
\`\`\`

---

### 🔍 DEBUGGING

#### Logs überprüfen
\`\`\`bash
# Datapoint Mapping
grep \"Loading BAOS datapoint mappings\" home-assistant.log

# SSL Context
grep \"ssl_context\" home-assistant.log

# REST API Erfolg
grep \"✅ Loaded\" home-assistant.log
\`\`\`

#### Erwartete Logs
\`\`\`
🔍 Loading BAOS datapoint mappings from REST API...
✅ Loaded 50 GroupAddress → Datapoint-ID mappings from BAOS
Sample mappings: {'1/1/0': 2048, '1/1/1': 2049, '1/1/2': 2050}
\`\`\`

---

### 📋 NÄCHSTE SCHRITTE

1. ✅ Beta 7.3 auf Madeira-VM installieren
2. 🔍 Startup-Logs prüfen (Datapoint Mapping erfolgreich?)
3. 🎯 REST API Verhalten testen (Timeouts? Erfolge?)
4. 📊 Initiale Zustände mit Webcam vergleichen

---

### ⚠️ BEKANNTE EINSCHRÄNKUNGEN

- **Datapoint Limit**: Nur erste 50 Datapoints werden gemappt
  - Grund: Startup-Zeit begrenzen (~2s)
  - Falls mehr benötigt: Limit in \`knx_gateway.py\` Zeile 221 erhöhen

- **TLSv1 Deprecation**: Warnings für altes BAOS-TLS
  - Erwartet und harmlos
  - BAOS 777 unterstützt kein TLS 1.2+

---

### 🐛 BUGFIXES SEIT BETA 7.2
1. SSL blocking call → Executor-basiert
2. Datapoint mapping → Echte BAOS-IDs statt LXP-Werte
3. Performance → Asynchrone SSL-Erstellung

---

**Version**: 0.2.3-beta.7.3  
**Branch**: feature/initial-state-reading  
**Tests**: 58/58 passing ✅  
**Commits**: 3a72877  
**Release Date**: $(date +'%Y-%m-%d %H:%M:%S')
"

# GitHub CLI Release erstellen
gh release create "$RELEASE_TAG" \
    --title "$RELEASE_NAME" \
    --notes "$RELEASE_BODY" \
    --prerelease \
    --target feature/initial-state-reading

echo "✅ Release created: https://github.com/phismith91/luxorliving/releases/tag/$RELEASE_TAG"
