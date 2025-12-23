# Port Configuration Analysis – History & Architecture Decision

## 🔍 Issue Summary

The LUXORliving IP1 Gateway (BAOS 777) REST API has caused multiple port configuration issues throughout development. The following analysis documents the evolution and final correct configuration.

---

## 📊 Port Configuration Timeline

### Phase 1: Initial HTTP:80 (v0.1.x)
**Commit:** `0debd30`  
**Config:** `DEFAULT_HTTP_PORT = 80`  
**Result:** ❌ **HTTP:80 → 308 Redirect Loop**

**Problem:**
- BAOS 777 redirects HTTP:80 → HTTPS:443 (HTTP 308 Permanent Redirect)
- aiohttp didn't follow redirects by default
- Caused connection failures

---

### Phase 2: Direct HTTPS:443 Attempt (21. Dec 2025)
**Commits:** `bf2d0eb`, `738d9be`  
**Config:** `DEFAULT_HTTP_PORT = 443`  
**Result:** ❌ **HTTPS:443 Still Failing**

**Problem:**
- Changed to HTTPS directly: `base_url = f"https://{host}:{port}"`
- Device still rejected connections
- SSL context configuration was incomplete

**Evidence from Commit bf2d0eb:**
```
Problem: BAOS 777 antwortet mit 308 Redirect von HTTP:80 zu HTTPS:443
Lösung: Verwende direkt HTTPS:443 mit ssl=False
```

---

### Phase 3: Final Solution – HTTP:80 with SSL Context (21. Dec 2025)
**Commit:** `860cf4b` ✅ **WORKING**  
**Config:** `DEFAULT_HTTP_PORT = 80`  
**Result:** ✅ **Connected Successfully**

**Solution:**
```
base_url = "http://{host}:{80}"  ← Start with HTTP
SSL-Context configured for redirect handling
allow_redirects = True (default)

Flow:
1. POST http://IP:80/rest/login
2. 308 Redirect → https://IP:443/rest/login
3. SSL-Context accepts self-signed cert
4. Login successful ✓
```

**Key Configuration (rest_client.py):**
```python
self.base_url = f"http://{host}:{port}"  # port=80 by default

# SSL Context handles the redirect:
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
ssl_context.minimum_version = ssl.TLSv1_2  # (upgraded in v0.3.0-beta.1)
```

---

## 🏗️ Architectural Decision

### Why HTTP:80 Instead of HTTPS:443?

**✅ Correct Approach:**
1. **Follow BAOS API Documentation**
   - Official docs specify: `POST http://IP/rest/login`
   - Not `https://IP:443`

2. **Let aiohttp Handle Redirects**
   - HTTP client libraries are designed for this
   - HTTPS 308 redirects are standard protocol
   - SSL context manages the encrypted connection

3. **Single Configuration**
   - Users only need: `host = 192.168.1.3`
   - REST API port defaults to 80 → auto-redirects to 443
   - KNX/IP port always 3671 (separate from HTTP)

### Constants (const.py)
```python
DEFAULT_PORT = 3671  # KNX/IP tunneling (fixed, user-configurable in theory)
DEFAULT_HTTP_PORT = 80  # REST API (fixed, auto-redirects to 443)
```

### Why NOT Direct HTTPS:443?

❌ **Problems with Direct HTTPS:**
- Device rejects connections to 443 that don't start with HTTP redirect flow
- Documentation explicitly shows HTTP endpoints
- SSL context negotiation was incomplete
- More complex for users (would need `https://` config)

---

## 🧪 Verification

### Test Flow
```
Config: host="192.168.1.3", http_port=80, knx_port=3671

1. REST Client connects to http://192.168.1.3:80
   ↓ (308 Permanent Redirect)
2. aiohttp follows to https://192.168.1.3:443
   ↓ (SSL Context validates self-signed cert)
3. REST API responds ✓
   ↓
4. Tunneling enabled ✓
   ↓
5. KNX/IP connects to 192.168.1.3:3671 ✓
```

### Historical Commits Verifying Success
- `860cf4b`: "HTTP:80 mit SSL-Context für HTTPS-Redirects" – **First successful login**
- `84e5e2f`: Port field removed from UI (always 3671 for KNX, 80 for REST)
- `87c9089`: Fixed missing DEFAULT_PORT import for KNX port

---

## 📋 Current Configuration (v0.3.0-beta.1)

### const.py
```python
DEFAULT_PORT = 3671              # KNX/IP (never changed, correct since v0.1)
DEFAULT_HTTP_PORT = 80           # REST API (correct since commit 860cf4b)
```

### rest_client.py
```python
self.base_url = f"http://{host}:{port}"  # port from DEFAULT_HTTP_PORT (80)
                                          # Redirect to 443 handled by aiohttp + SSL context
```

### __init__.py (v0.3.0-beta.1)
```python
from .const import DEFAULT_PORT, DEFAULT_HTTP_PORT
...
port = DEFAULT_PORT              # 3671 for KNX/IP
http_port = DEFAULT_HTTP_PORT    # 80 for REST API (redirects to 443)
```

---

## ✅ Conclusion

### Which Port Actually Works?

| Port | Protocol | Purpose | Status |
|------|----------|---------|--------|
| **80** | HTTP | REST API (entry point) | ✅ **CORRECT** |
| **443** | HTTPS | REST API (after redirect) | ✅ Auto-handled |
| **3671** | KNX/IP | Tunneling | ✅ **CORRECT** |

### Architecture is Sound

The current configuration (HTTP:80 for REST API entry point) is the **correct and working solution**. It:

1. ✅ Follows official BAOS API documentation
2. ✅ Leverages HTTP client library's redirect handling
3. ✅ Properly configured SSL context for HTTPS negotiation
4. ✅ Tested and verified in production (last successful state was 860cf4b)
5. ✅ Simplified user configuration (no need to specify protocol/port)

### Recent Bug Fix (v0.3.0-beta.1)

The DEFAULT_PORT import was missing in `__init__.py` (commit `87c9089`), but this doesn't change the port values—it only fixes the import statement. The port configuration itself has been correct since commit `860cf4b`.

---

## 📚 References

- **Commit 860cf4b:** "HTTP:80 mit SSL-Context für HTTPS-Redirects" – Final working solution
- **Commit bf2d0eb:** "Verwende HTTPS Port 443" – Earlier failed attempt (documented for learning)
- **BAOS API Docs:** Reference in rest_client.py (HTTP endpoints, not HTTPS)

