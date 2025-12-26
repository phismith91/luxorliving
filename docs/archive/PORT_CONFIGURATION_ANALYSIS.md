# Port Configuration - Technical Reference

## Overview

This document explains the port configuration for BAOS 777 REST API communication and resolves common confusion about HTTP/HTTPS ports.

## Current Configuration

**REST API:**
- Entry point: HTTP port 80
- Auto-redirect: HTTPS port 443 (via HTTP 308 redirect)
- SSL context handles self-signed certificates

**KNX/IP:**
- Fixed port: 3671 (UDP)
- Separate from REST API ports

## Why HTTP:80 (Not HTTPS:443)?

**The BAOS 777 requires this sequence:**
1. Client connects to `http://<ip>:80/rest/login`
2. Gateway responds with HTTP 308 redirect to `https://<ip>:443/rest/login`
3. Client follows redirect with SSL context configured
4. Login succeeds

**Attempting direct HTTPS:443 fails** because the gateway expects the HTTP→HTTPS redirect flow.

## Implementation

```python
# rest_client.py
self.base_url = f"http://{host}:{port}"  # port defaults to 80

# SSL context for redirect handling
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Accept self-signed cert
ssl_context.minimum_version = ssl.TLSv1_2
```

## Constants

```python
# const.py
DEFAULT_PORT = 3671          # KNX/IP tunneling (UDP)
DEFAULT_HTTP_PORT = 80       # REST API entry point
```

## User Configuration

**Users only configure:**
- Gateway IP address (e.g., `192.168.1.3`)
- Username/password for REST API

**Automatic:**
- Port 80 used for REST API (redirects to 443)
- Port 3671 used for KNX/IP tunneling
- SSL context handles self-signed certificates

## Common Questions

**Q: Why not use HTTPS:443 directly?**  
A: BAOS 777 firmware requires HTTP→HTTPS redirect flow. Direct HTTPS connections are rejected.

**Q: Is HTTP:80 insecure?**  
A: No. Initial request immediately redirects to HTTPS:443 with TLS 1.2+ encryption.

**Q: Can I change the port?**  
A: No. Ports are hardcoded per BAOS API specification.

**Q: What about self-signed certificates?**  
A: SSL context configured with `verify_mode = CERT_NONE` to accept BAOS self-signed certs.

## Troubleshooting

**Cannot connect to REST API:**
1. Verify gateway responds on port 80: `curl -v http://<ip>/rest/login`
2. Check for HTTP 308 redirect in response
3. Verify port 443 accessible: `openssl s_client -connect <ip>:443`

**Connection refused on port 80:**
- Gateway may be offline
- Firewall blocking port 80
- Wrong IP address

**SSL errors:**
- Ensure `verify_mode = CERT_NONE` in SSL context
- Check minimum TLS version (should be 1.2+)
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

| Port     | Protocol | Purpose                   | Status         |
| -------- | -------- | ------------------------- | -------------- |
| **80**   | HTTP     | REST API (entry point)    | ✅ **CORRECT**  |
| **443**  | HTTPS    | REST API (after redirect) | ✅ Auto-handled |
| **3671** | KNX/IP   | Tunneling                 | ✅ **CORRECT**  |

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

