# BAOS REST API Limitations

## Zusammenfassung

Die BAOS 777 REST API **kann keine GroupAddress-Mappings** für Licht- und Schalter-Steuerung bereitstellen.

## Erkenntnisse aus Beta 7.3-7.6 (19.-23. Dez 2025)

### Versuchte Lösung: REST API Datapoint Mapping
**Ziel:** BAOS Datapoints → KNX GroupAddresses mappen um initial states ohne GroupValueRead zu erhalten.

**Implementierung (Beta 7.3-7.6):**
- REST API `/rest/datapoints` → Liste aller Datapoints
- Für jeden Datapoint: `/rest/datapoints/{id}` → Details abfragen
- Erwartung: `"name"` Feld enthält GroupAddress (z.B. `"1/1/0"`)

### Tatsächliche BAOS Datapoint-Struktur

```json
{
  "Format": "DPT9",
  "description": {
    "name": "Windstärke",           // ← Beschreibender Text, KEINE GroupAddress!
    "datapoint_type": "9.001",
    "flags": {...}
  },
  "id": 1,
  "value": 0
}
```

### BAOS Datapoints sind NICHT GroupAddresses

**Tatsächlicher Inhalt der 196 BAOS Datapoints:**

| Datapoint IDs | Typ | Zweck |
|--------------|-----|-------|
| 1-13 | Wetterstation | Windstärke, Temperatur, Helligkeit, Alarme |
| 14-16 | Zentral | Zentral ein/aus, Panik, Auf/Ab |
| 17-28 | Jalousien | Fassade 1-4 Höhe/Lamelle/Sperre |
| 29-31 | Automatik | Morgens/Abends, Urlaub |
| 32-39 | Schwellwerte | Konfigurationswerte |
| 40-41 | Status | Wettersensor, Shelly |
| 42-50 | Szenen | Unbenutzte Szenen 1-9 |

**Keine einzige GroupAddress für Lights (1/1/0, 1/1/1, etc.)!**

### Beta 7.6 Produktions-Logs (Madeira-VM)

```
10:12:44.864 INFO 📁 Datapoint 1 response: {..., "description": {"name": "Windstärke", ...}, ...}
10:12:44.864 WARNING ❌ Datapoint 1 has no 'name' field: {...}
... (50 mal wiederholt)
10:12:46.800 INFO ✅ Loaded 0 GroupAddress → Datapoint-ID mappings from BAOS
```

**Resultat:** 0 Mappings, weil alle Datapoints beschreibende Namen haben, keine GroupAddresses.

## Korrekte Lösung: GroupValueRead

### Warum GroupValueRead funktioniert:
1. **BAOS Cache:** BAOS 777 speichert alle KNX-Telegramme im Bus-Cache
2. **Sofortige Antwort:** GroupValueRead wird vom BAOS-Cache beantwortet (keine Bus-Belastung)
3. **Aktuelle Werte:** Cache wird durch alle Bus-Telegramme aktualisiert
4. **Standard KNX:** Unterstützt von allen KNX-Geräten

### Performance-Messungen:
- **Pro Light:** ~30ms für GroupValueRead
- **27 Lights:** ~800ms Gesamtzeit beim Startup
- **Keine Timeouts:** BAOS-Cache antwortet zuverlässig

## Architektur-Empfehlung

### ✅ Verwenden:
- **Initial States:** GroupValueRead (BAOS-Cache)
- **Live Updates:** KNX Tunneling + Telegram Listener
- **Befehle senden:** GroupValueWrite via Tunneling

### ❌ Nicht verwenden:
- **REST API Datapoints** für GroupAddress-Lookups
- **Polling** via REST API für State Updates

## Code-Changes (Beta 7.7)

**Entfernt:**
- `_async_load_datapoint_mapping()` Funktion
- `async_read_via_rest()` Funktion
- `_datapoint_mapping` Dictionary
- `_datapoint_urls` Dictionary

**Behalten:**
- REST API Login (für Tunneling-Authentication)
- `enable_tunneling()` (erforderlich für BAOS 777)
- Alle KNX Tunneling Funktionen

## Lessons Learned

1. **BAOS Datapoints ≠ KNX GroupAddresses**
   - Datapoints sind interne BAOS-Variablen
   - Keine Korrelation zu Light-GroupAddresses
   
2. **Dokumentation war irreführend**
   - Annahme: Datapoints enthalten GroupAddresses
   - Realität: Datapoints sind für Wetterstation/Jalousien/Szenen
   
3. **GroupValueRead ist die richtige Lösung**
   - Standard KNX-Methode
   - BAOS-Cache optimiert
   - Zuverlässig und schnell

## Referenzen

- **Beta 7.3:** REST API Mapping Implementierung (19.12.2025)
- **Beta 7.4:** Mapping-Funktion Aufruf korrigiert (20.12.2025)
- **Beta 7.5:** REST API Endpoint korrigiert (21.12.2025)
- **Beta 7.6:** Debug-Logging offenbart Struktur (22.12.2025)
- **Beta 7.7:** REST API Mapping entfernt (23.12.2025)

## Siehe auch

- [BAOS_REST_API_DISCOVERY.md](BAOS_REST_API_DISCOVERY.md) - Vollständige API-Dokumentation
- [ARCHITECTURE_DECISION.md](ARCHITECTURE_DECISION.md) - Architektur-Entscheidungen
- [KNX_IMPLEMENTATION.md](KNX_IMPLEMENTATION.md) - KNX-Implementierungs-Details
