# KNX Tunneling mit REST API Authentifizierung

**Problem gefunden:** Natives KNX Tunneling funktioniert nicht, weil das BAOS 777 (IP1) erst durch REST API aktiviert werden muss!

---

## 🔍 Die Entdeckung

Laut **LUXORliving API Documentation**:

> **10.2 Activation/deactivation of tunneling**
> 
> To enable tunneling, a PUT request must be sent to `/rest/device/authtunneling`.
> A timeout of the session token or logging out automatically deactivates the
> tunneling again. To disable tunneling directly, a PUT request can be sent with
> `{"enabled": false}`

### Das erklärt alles!

```
❌ FALSCHE Annahme (vorher):
   Tunnel ist blockiert durch LuxorPlug → Muss VM stoppen

✅ RICHTIGE Realität:
   Tunnel ist DEAKTIVIERT → Muss per REST API aktiviert werden!
```

---

## 🔑 Warum es nicht funktioniert hat

### Natives HA KNX Integration

```yaml
# configuration.yaml
knx:
  tunneling:
    host: 192.168.1.3
    port: 3671
```

**Problem:** 
- Home Assistant versucht direkt KNX Tunneling Connection
- BAOS 777 lehnt ab: **Tunneling nicht aktiviert**
- HA weiß nichts von der REST API Aktivierung

### LuxorPlug funktioniert

```
LuxorPlug VM:
1. REST Login → Session Token erhalten
2. PUT /rest/device/authtunneling {"enabled": true}
3. KNX Tunneling verbinden (localhost:3671)
4. Bei Logout → Tunneling automatisch deaktiviert
```

**Das ist, warum der Tunnel "frei wird" wenn LuxorPlug stoppt:**
- Nicht weil der Tunnel-Slot frei wird
- Sondern weil die Session ausläuft → Tunneling deaktiviert!

---

## 🛠️ Die Lösung

### Architektur: REST API + KNX Tunneling

```python
class LuxorLivingGateway:
    """Gateway mit REST API Authentifizierung"""
    
    async def async_setup(self):
        # 1. REST API Login
        self.session_token = await self.rest_login()
        
        # 2. Tunneling aktivieren
        await self.enable_tunneling()
        
        # 3. KNX Tunneling verbinden
        await self.knx_connect()
    
    async def rest_login(self) -> str:
        """Login via REST API"""
        response = await self.session.post(
            f"http://{self.host}/rest/auth/login",
            json={
                "username": self.username,
                "password": self.password
            }
        )
        data = await response.json()
        return data["sessionToken"]
    
    async def enable_tunneling(self):
        """Aktiviere KNX Tunneling"""
        await self.session.put(
            f"http://{self.host}/rest/device/authtunneling",
            json={"enabled": True},
            headers={"Authorization": f"Bearer {self.session_token}"}
        )
    
    async def knx_connect(self):
        """Verbinde KNX Tunneling (nach Aktivierung!)"""
        self.knx = XknxGateway(
            host=self.host,
            port=3671,
            connection_type="tunneling"
        )
        await self.knx.start()
    
    async def async_shutdown(self):
        """Cleanup: Tunneling wird auto-deaktiviert bei Session-Ende"""
        await self.knx.stop()
        await self.rest_logout()  # Deaktiviert Tunneling
```

---

## 📋 Implementierungsplan

### Phase 1: REST API Client

**Datei:** `custom_components/luxor_living/rest_client.py`

```python
class BAOSRestClient:
    """REST API Client für BAOS 777"""
    
    async def login(self, username: str, password: str) -> str:
        """Login und Session Token erhalten"""
        pass
    
    async def enable_tunneling(self) -> bool:
        """PUT /rest/device/authtunneling {"enabled": true}"""
        pass
    
    async def disable_tunneling(self) -> bool:
        """PUT /rest/device/authtunneling {"enabled": false}"""
        pass
    
    async def logout(self):
        """Session beenden (deaktiviert Tunneling)"""
        pass
```

### Phase 2: Config Flow erweitern

**Datei:** `custom_components/luxor_living/config_flow.py`

```python
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT, default=3671): int,
    vol.Required("username", default="admin"): str,
    vol.Required("password"): str,  # NEU!
})
```

### Phase 3: Gateway Integration

**Datei:** `custom_components/luxor_living/knx_gateway.py`

```python
class KNXGateway:
    def __init__(self, host, port, username, password):
        self.rest_client = BAOSRestClient(host)
        self.knx_client = None
        self.credentials = (username, password)
    
    async def async_setup(self):
        # 1. REST Login
        await self.rest_client.login(*self.credentials)
        
        # 2. Tunneling aktivieren
        await self.rest_client.enable_tunneling()
        
        # 3. KNX verbinden
        self.knx_client = await xknx_connect(...)
```

---

## 🧪 Test-Szenarien

### Test 1: Erfolgreiche Aktivierung

```python
async def test_tunneling_activation():
    """Test REST API aktiviert Tunneling erfolgreich"""
    gateway = LuxorLivingGateway("192.168.1.3", "admin", "admin")
    
    # Should succeed
    await gateway.async_setup()
    
    assert gateway.rest_client.session_token is not None
    assert gateway.knx_client.connected is True
```

### Test 2: Fehlerhafte Credentials

```python
async def test_invalid_credentials():
    """Test falsches Passwort"""
    gateway = LuxorLivingGateway("192.168.1.3", "admin", "wrong")
    
    with pytest.raises(AuthenticationError):
        await gateway.async_setup()
```

### Test 3: Session Timeout

```python
async def test_session_timeout():
    """Test Tunneling wird bei Session-Timeout deaktiviert"""
    gateway = LuxorLivingGateway(...)
    await gateway.async_setup()
    
    # Simuliere Session Timeout
    await asyncio.sleep(SESSION_TIMEOUT + 1)
    
    # KNX sollte disconnected sein
    assert gateway.knx_client.connected is False
```

### Test 4: Graceful Shutdown

```python
async def test_graceful_shutdown():
    """Test sauberes Herunterfahren"""
    gateway = LuxorLivingGateway(...)
    await gateway.async_setup()
    await gateway.async_shutdown()
    
    # Tunneling sollte deaktiviert sein
    assert gateway.rest_client.session_token is None
```

---

## 🔍 REST API Endpunkte (zu entdecken)

### Login/Logout

```http
POST /rest/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}

Response:
{
  "sessionToken": "abc123...",
  "expiresIn": 3600
}
```

```http
POST /rest/auth/logout
Authorization: Bearer abc123...
```

### Tunneling Control

```http
PUT /rest/device/authtunneling
Authorization: Bearer abc123...
Content-Type: application/json

{
  "enabled": true
}

Response:
{
  "status": "ok",
  "tunneling": true
}
```

### Status Check

```http
GET /rest/device/authtunneling
Authorization: Bearer abc123...

Response:
{
  "enabled": true,
  "connectedClients": 0,
  "maxSlots": 1
}
```

---

## ✅ Vorteile dieser Lösung

### 1. Kein Konflikt mehr mit LuxorPlug
```
Beide Ansätze sind identisch:
- REST Login
- Tunneling aktivieren
- KNX nutzen
- Logout (Tunneling deaktiviert)
```

### 2. Saubere Session-Verwaltung
```python
async def async_setup_entry(hass, entry):
    """Setup mit auto-cleanup"""
    gateway = await create_gateway(entry.data)
    
    # Cleanup bei HA Stop
    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP,
        gateway.async_shutdown
    )
```

### 3. Diagnostics
```python
@property
def diagnostics(self):
    return {
        "rest_session": self.rest_client.session_token is not None,
        "tunneling_enabled": self.rest_client.tunneling_enabled,
        "knx_connected": self.knx_client.connected,
        "session_expires_at": self.rest_client.session_expires
    }
```

---

## 🚀 Nächste Schritte

1. **REST API Endpunkte identifizieren**
   ```bash
   # Browser DevTools (F12) auf http://192.168.1.3
   # Network Tab → XHR requests beobachten
   # Login durchführen und Requests dokumentieren
   ```

2. **REST Client implementieren**
   ```bash
   custom_components/luxor_living/rest_client.py
   ```

3. **Config Flow aktualisieren**
   ```python
   # Username/Password hinzufügen
   # Validation: Test Login vor Save
   ```

4. **Gateway umbauen**
   ```python
   # async_setup: REST → Tunneling → KNX
   # async_shutdown: KNX → Logout
   ```

5. **Tests schreiben**
   ```python
   tests/test_rest_client.py
   tests/test_tunneling_auth.py
   ```

---

## 📚 Weiterführende Dokumentation

- [BAOS_REST_API.md](BAOS_REST_API.md) - REST API Übersicht
- [BAOS_REST_API_DISCOVERY.md](BAOS_REST_API_DISCOVERY.md) - API Endpunkte finden
- [ARCHITECTURE_DECISION.md](ARCHITECTURE_DECISION.md) - Architektur-Entscheidungen

---

## 🎯 Fazit

**Das Problem war nie ein "blockierter Tunnel"** - es war **fehlende Authentifizierung**!

Die Lösung:
1. ✅ REST API Login
2. ✅ Tunneling aktivieren via `/rest/device/authtunneling`
3. ✅ KNX Tunneling verbinden
4. ✅ Bei Shutdown: Session beenden (deaktiviert Tunneling)

**LuxorPlug und unsere Integration können parallel laufen**, solange beide:
- Sich anmelden
- Tunneling aktivieren
- Sich sauber abmelden

Nur **1 aktive Tunneling-Session** gleichzeitig, aber keine permanente Blockade!
