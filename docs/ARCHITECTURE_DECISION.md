# Architekturentscheidung: IP1 vs. LXP-Parser Ansatz

**Datum:** 21.-23. Dezember 2025  
**Branch:** `main` (merged)  
**Finale Entscheidung:** Native Integration mit KNX Tunneling + REST API Authentication

## Updates

### 23. Dezember 2025 - Beta 7.7 Repository Cleanup
**BAOS REST API Datapoint Mapping entfernt:**
- Beta 7.3-7.6 Versuch: BAOS Datapoints → GroupAddresses mappen
- **Erkenntnisse:** BAOS Datapoints sind NICHT GroupAddresses!
  - Datapoints: Wetterstation, Jalousien, Szenen (nicht Lights)
  - Namen: "Windstärke", "Außentemperatur" (nicht "1/1/0")
- **Lösung:** GroupValueRead ist korrekt (BAOS-Cache antwortet schnell)
- Siehe: [BAOS_REST_API_LIMITATIONS.md](BAOS_REST_API_LIMITATIONS.md)

**Code bereinigt:**
- ❌ `_async_load_datapoint_mapping()` entfernt
- ❌ `async_read_via_rest()` entfernt
- ✅ REST API nur für Tunneling-Authentication
- ✅ GroupValueRead für Initial States (30ms pro Light)

---

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

| Feature                   | Unterstützung                  | Implikation                               |
| ------------------------- | ------------------------------ | ----------------------------------------- |
| **KNX Routing**           | ❌ Nein                         | Multicast nicht möglich                   |
| **KNX Tunneling**         | ⚠️ Blockiert                    | LuxorPlug belegt Tunnel-Slot              |
| **Tunneling Aktivierung** | ⚠️ **Authentifizierung nötig!** | REST API Login erforderlich               |
| **REST API**              | ✅ Vollständig                  | Login, Tunneling Control, Status          |
| **Binary Protocol**       | ✅ Ja                           | Vollständige Kontrolle via localhost:3671 |

**KRITISCHER BEFUND (21. Dez 2025):**

Laut **LUXORliving API Documentation**:
> **10.2 Activation/deactivation of tunneling**
> To enable tunneling, a PUT request must be sent to `/rest/device/authtunneling`.

**Das Problem war nie "blockierter Tunnel" - es war fehlende Authentifizierung!**

Die native HA KNX-Integration kann **nicht direkt** Tunneling nutzen, weil:
1. ❌ Sie macht keinen REST API Login
2. ❌ Sie aktiviert Tunneling nicht via `/rest/device/authtunneling`
3. ❌ Der BAOS 777 lehnt unauthentifizierte Tunneling-Verbindungen ab

**LuxorPlug funktioniert**, weil es:
1. ✅ REST Login macht → Session Token erhält
2. ✅ `PUT /rest/device/authtunneling {"enabled": true}` sendet
3. ✅ Dann KNX Tunneling verbindet
4. ✅ Bei Logout → Tunneling automatisch deaktiviert

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

## Empfehlung: Hybrid-Ansatz mit REST API Authentifizierung

### Strategie (AKTUALISIERT 21. Dez 2025)

**1. Primär: REST API + KNX Tunneling**
- REST API für Authentifizierung und Tunneling-Aktivierung
- KNX Tunneling für Realtime Control (nach Aktivierung!)
- Custom Component `luxor_living` orchestriert beide

**2. Unterstützend: LXP-Parser**
- Automatische Entity-Generierung aus LXP-Datei
- Mapping von KNX-Adressen zu Namen/Typen
- Entity Discovery beim Setup

### Implementierungsplan

#### Phase 1: REST API Client
```python
# custom_components/luxor_living/rest_client.py
class BAOSRestClient:
    """REST API Client für BAOS 777 mit Tunneling-Aktivierung"""
    
    async def login(self, username: str, password: str) -> str:
        """Login via REST API → Session Token"""
        response = await self.session.post(
            f"{self.base_url}/rest/auth/login",
            json={"username": username, "password": password}
        )
        data = await response.json()
        return data["sessionToken"]
    
    async def enable_tunneling(self) -> bool:
        """PUT /rest/device/authtunneling {"enabled": true}"""
        response = await self.session.put(
            f"{self.base_url}/rest/device/authtunneling",
            json={"enabled": True},
            headers={"Authorization": f"Bearer {self.session_token}"}
        )
        return response.status == 200
    
    async def disable_tunneling(self):
        """Deaktiviert bei Logout automatisch"""
        await self.logout()
```

#### Phase 2: Gateway Integration
```python
# custom_components/luxor_living/knx_gateway.py
class KNXGateway:
    def __init__(self, host, username, password):
        self.rest_client = BAOSRestClient(host)
        self.knx_client = None
        self.credentials = (username, password)
    
    async def async_setup(self):
        # 1. REST Login
        await self.rest_client.login(*self.credentials)
        
        # 2. Tunneling aktivieren
        await self.rest_client.enable_tunneling()
        
        # 3. KNX Tunneling verbinden (jetzt erlaubt!)
        self.knx_client = XknxGateway(
            host=self.host,
            port=3671,
            connection_type="tunneling"
        )
        await self.knx_client.start()
    
    async def async_shutdown(self):
        """Cleanup: Logout deaktiviert Tunneling automatisch"""
        await self.knx_client.stop()
        await self.rest_client.logout()
```

#### Phase 3: Config Flow erweitern
```python
# custom_components/luxor_living/config_flow.py
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT, default=3671): int,
    vol.Required("username", default="admin"): str,
    vol.Required("password"): str,  # NEU!
})

async def async_step_user(self, user_input):
    # Validate: Test REST Login
    try:
        rest_client = BAOSRestClient(user_input[CONF_HOST])
        await rest_client.login(
            user_input["username"],
            user_input["password"]
        )
        await rest_client.logout()
    except AuthenticationError:
        return self.async_show_form(
            errors={"base": "invalid_auth"}
        )
```

#### Phase 4: LXP-Parser Integration
```python
# lxp_parser.py
def parse_lxp_to_entities(lxp_file: Path) -> dict:
    """Parse LXP → Entity Definitions"""
    return {
        "light": [
            {
                "name": "Badlicht",
                "address": "1/0/0",
                "state_address": "1/1/0",
                "unique_id": "luxor_light_1_0_0"
            }
        ]
    }

# custom_components/luxor_living/__init__.py
async def async_setup_entry(hass, entry):
    # Lade entities.json (generiert aus LXP)
    entities_config = load_entities_from_lxp()
    
    # Setup Gateway mit Auth
    gateway = KNXGateway(
        entry.data[CONF_HOST],
        entry.data["username"],
        entry.data["password"]
    )
    await gateway.async_setup()
    
    # Erstelle Entities
    for entity in entities_config["light"]:
        await async_create_light(hass, entity, gateway)
```

---

## Entscheidungsmatrix

| Kriterium                   | LXP+KNX (Ansatz 1)          | IP1 Native (Ansatz 2) | Hybrid         |
| --------------------------- | --------------------------- | --------------------- | -------------- |
| **Funktioniert jetzt**      | ❌ Nein                      | ✅ Ja                  | ✅ Ja           |
| **Standardintegration**     | ✅ Ja (KNX)                  | ❌ Custom              | ⚠️ Custom       |
| **Wartungsaufwand**         | ⚠️ Mittel                    | ⚠️ Mittel              | ⚠️ Mittel       |
| **Vollständige Kontrolle**  | ❌ Nein (keine Verbindung)   | ✅ Ja                  | ✅ Ja           |
| **Entity-Autodiscovery**    | ✅ Ja (aus LXP)              | ❌ Manuell             | ✅ Ja (aus LXP) |
| **Hardware-Kompatibilität** | ❌ BAOS 777 nicht kompatibel | ✅ Kompatibel          | ✅ Kompatibel   |

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
