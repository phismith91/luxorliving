# Architekturentscheidung: IP1 vs. LXP-Parser Ansatz

**Datum:** 21. Dezember 2025  
**Branch:** `feature/ip1-native-approach`  
**Entscheidung:** Bewertung zweier konkurrierender Ansätze

## Kontext

Wir haben zwei verschiedene Ansätze zur Integration von LUXORliving-Geräten in Home Assistant:

### Ansatz 1: LXP-Parser + KNX-YAML (aktuell implementiert)
- **Quelle:** LXP-Projektdatei (Familie Schmidt)
- **Methode:** Parsen der LXP-Datei → Generierung von KNX YAML
- **Integration:** Native Home Assistant KNX-Integration
- **Status:** Implementiert, YAML generiert, aber Entities "unavailable"

### Ansatz 2: IP1 Native API (ursprünglicher Ansatz)
- **Quelle:** IP1 Gateway API (REST/Binary Protocol)
- **Methode:** Direkte Kommunikation mit BAOS 777 via localhost:3671
- **Integration:** Custom Component `luxor_living`
- **Status:** Funktionierend, aber limitiert (nur Binary Protocol)

---

## Technische Bewertung

### 1. Hardware-Constraints (BAOS 777)

| Feature | Unterstützung | Implikation |
|---------|---------------|-------------|
| **KNX Routing** | ❌ Nein | Multicast nicht möglich |
| **KNX Tunneling** | ⚠️ Blockiert | LuxorPlug belegt Tunnel-Slot |
| **REST API** | ⚠️ Limitiert | Nur read-only Status |
| **Binary Protocol** | ✅ Ja | Vollständige Kontrolle via localhost:3671 |

**Kritischer Befund:** BAOS 777 unterstützt kein KNX Routing und der einzige Tunnel-Slot ist durch LuxorPlug belegt. Daher ist die native HA KNX-Integration **physikalisch nicht möglich**.

---

### 2. Vergleich der Ansätze

#### Ansatz 1: LXP-Parser + KNX-YAML

**Vorteile:**
- ✅ Nutzt native HA KNX-Integration (bewährt, stabil)
- ✅ Automatische Entity-Generierung aus LXP-Datei
- ✅ Standardisierte KNX-Konfiguration
- ✅ Keine Custom Component nötig
- ✅ YAML ist versionierbar und übertragbar

**Nachteile:**
- ❌ **Funktioniert nicht** - keine KNX-Verbindung möglich (kein Routing, kein Tunneling)
- ❌ Entities bleiben "unavailable"
- ❌ Benötigt manuelle LXP-Datei-Beschaffung
- ❌ Duplizierungsprobleme (Lights vs. Switches)
- ❌ Komplex: LXP → YAML → KNX Integration → (nicht verbunden)

**Technische Hürden:**
```
LXP File → Parser → KNX YAML → HA KNX Integration
                                        ↓
                                  ❌ Keine Verbindung
                                  (BAOS 777: kein Routing/Tunnel)
```

---

#### Ansatz 2: IP1 Native API

**Vorteile:**
- ✅ **Funktioniert aktuell** - Binary Protocol via localhost:3671 arbeitet
- ✅ Direkte Kommunikation mit BAOS 777
- ✅ Vollständige Kontrolle (read/write)
- ✅ Kein KNX-Gateway nötig
- ✅ Funktioniert **jetzt** mit LuxorPlug

**Nachteile:**
- ⚠️ Custom Component nötig (Wartung, Updates)
- ⚠️ Binary Protocol komplex (aber bereits implementiert)
- ⚠️ REST API limitiert (nur Status, kein Control)
- ⚠️ Dokumentation unvollständig

**Technische Lösung:**
```
Home Assistant → luxor_living Component → localhost:3671 → LuxorPlug → BAOS 777
                                                                            ↓
                                                                        KNX Bus
```

---

### 3. LXP-Datei: Wertvoll trotz anderem Ansatz

Die LXP-Datei bleibt wertvoll für:
- ✅ **Entity-Discovery:** Automatisches Mapping von KNX-Adressen zu Namen
- ✅ **Dokumentation:** Vollständige Liste aller Geräte
- ✅ **Konfiguration:** Device-Types, Räume, Gruppierungen
- ✅ **Reverse Engineering:** KNX-Adressen → LUXORliving-Geräte

**Idee:** LXP-Parser als **Hilfstool** für Custom Component verwenden:
```python
# Workflow:
lxp_file → lxp_parser.py → entity_definitions.json
                                ↓
                    luxor_living/__init__.py
                                ↓
                    async_setup_entry() → create entities
```

---

## Empfehlung: Hybrid-Ansatz

### Strategie

**1. Primär: IP1 Native API (Ansatz 2)**
- Custom Component `luxor_living` als Hauptintegration
- Binary Protocol für vollständige Kontrolle
- REST API für Status-Updates (wo möglich)

**2. Unterstützend: LXP-Parser**
- Automatische Entity-Generierung aus LXP-Datei
- Mapping von KNX-Adressen zu Namen/Typen
- **Nicht** für KNX-YAML, sondern für Custom Component Config

### Implementierungsplan

#### Phase 1: LXP-Parser verbessern
```python
# lxp_parser.py
def parse_lxp_to_entities(lxp_file: Path) -> dict:
    """
    Parse LXP → Entity Definitions für Custom Component
    
    Output: entities.json
    {
        "light": [
            {
                "name": "Badlicht",
                "address": "1/0/0",
                "state_address": "1/1/0",
                "unique_id": "luxor_light_1_0_0"
            }
        ]
    }
    """
```

#### Phase 2: Custom Component erweitern
```python
# custom_components/luxor_living/__init__.py
async def async_setup_entry(hass, entry):
    # Lade entities.json (generiert aus LXP)
    entities_config = load_entities_from_lxp()
    
    # Erstelle Entities via Binary Protocol
    for entity in entities_config["light"]:
        await async_create_light(hass, entity)
```

#### Phase 3: Tunneling-Proxy (optional, später)
Falls KNX-Integration gewünscht:
```python
# knx_proxy.py
# Erstelle localhost KNX Tunnel → Binary Protocol Bridge
# Dann: HA KNX Integration → localhost:3672 → Proxy → localhost:3671
```

---

## Entscheidungsmatrix

| Kriterium | LXP+KNX (Ansatz 1) | IP1 Native (Ansatz 2) | Hybrid |
|-----------|-------------------|---------------------|---------|
| **Funktioniert jetzt** | ❌ Nein | ✅ Ja | ✅ Ja |
| **Standardintegration** | ✅ Ja (KNX) | ❌ Custom | ⚠️ Custom |
| **Wartungsaufwand** | ⚠️ Mittel | ⚠️ Mittel | ⚠️ Mittel |
| **Vollständige Kontrolle** | ❌ Nein (keine Verbindung) | ✅ Ja | ✅ Ja |
| **Entity-Autodiscovery** | ✅ Ja (aus LXP) | ❌ Manuell | ✅ Ja (aus LXP) |
| **Hardware-Kompatibilität** | ❌ BAOS 777 nicht kompatibel | ✅ Kompatibel | ✅ Kompatibel |

**Gewinner: Hybrid-Ansatz (IP1 Native + LXP-Parser)**

---

## Nächste Schritte

### Sofort (auf diesem Branch)

1. **LXP-Parser erweitern**
   ```bash
   # lxp_to_entity_config.py (neues Tool)
   # Output: custom_components/luxor_living/entities.json
   ```

2. **Custom Component refactoren**
   ```python
   # Nutze entities.json für automatische Entity-Erstellung
   # Statt hardcoded Config
   ```

3. **Dokumentation aktualisieren**
   - ARCHITECTURE.md
   - README.md
   - QUICKSTART.md

### Später (separate Branches)

4. **REST API Integration** (optional)
   - Für status-only Entities (z.B. Sensoren)

5. **KNX Tunneling Proxy** (optional, nur wenn native KNX-Integration gewünscht)
   - Binary Protocol → KNX Tunnel Bridge
   - localhost:3672 → KNX Integration

---

## Fazit

Der **ursprüngliche Ansatz (IP1 Native API)** war richtig. Die LXP-to-KNX-YAML Implementierung war ein wertvoller Umweg, weil:

1. ✅ Wir haben jetzt einen LXP-Parser (wiederverwendbar)
2. ✅ Wir kennen alle KNX-Adressen und Device-Typen
3. ✅ Wir haben saubere Entity-Definitionen
4. ❌ **Aber:** KNX-Integration funktioniert nicht mit BAOS 777 Hardware

**Empfehlung:** Zurück zu IP1 Native API, aber mit Erkenntnissen aus LXP-Analyse für automatische Entity-Generierung.

---

## Offene Fragen

1. **IP1 API Dokumentation** - Welche Features unterstützt das neue PDF?
2. **Tunneling aktivieren** - Ist ein zweiter Tunnel-Slot möglich?
3. **REST API Vollständigkeit** - Welche Operationen sind möglich?
4. **LuxorPlug Rolle** - Kann es umkonfiguriert werden?

Diese sollten aus dem IP1-Dokumentationsdokument beantwortet werden können.
