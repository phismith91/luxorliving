# Weinzierl KNX IP BAOS 777 - REST API Documentation

> **Note**: This documentation is extracted from the German manual "weinzierl-777-knx-ip-baos-5193-manual-de.pdf". The manual mentions "KNX IP BAOS RESTful Web Services" but does not contain detailed REST API endpoint documentation. This document combines information from the manual with typical BAOS REST API patterns.

## Overview

The Weinzierl KNX IP BAOS 777 supports three protocol variants:

1. **KNX IP BAOS Binary** - Binary protocol for microcontrollers
2. **KNX IP BAOS Web Services** - URL-based protocol with JSON syntax (compatible with BAOS 771/772/773/774)
3. **KNX IP BAOS RESTful Web Services** - RESTful JSON-based protocol for browser-based web applications

## Status: Incomplete Documentation

⚠️ **Important**: The manual does NOT contain detailed REST API documentation with specific endpoints, request/response examples, or API specifications. 

The manual only mentions:
- REST Services exist and can be enabled/disabled in the device settings
- The protocol uses "RESTful JSON-Syntax"
- It's designed for browser-based web applications
- Access to datapoints via REST services can be disabled in configuration

## What We Know from the Manual

### 1. Base Access
- **Web Interface**: `http://<IP_Address>` or `https://<IP_Address>`
- **Default Credentials**: 
  - Username: `admin`
  - Password: `admin`
  - ⚠️ Should be changed after installation via ETS download

### 2. Default Network Configuration
- IP assignment via DHCP (default)
- Can be configured manually via:
  - Device display menu
  - ETS software (version 4.2 or higher)

### 3. Services Configuration
The device supports enabling/disabling of:
- KNXnet/IP Tunnelling
- KNXnet/IP Search Response
- Indications Sending
- BAOS Binary
- BAOS Web Services
- **BAOS REST Services** ← Can be disabled
- BAOS Webserver (hosts the web interface)

⚠️ **Warning from Manual**: Disabling BAOS REST Services will break any client application using these services. The web interface also uses REST services internally.

### 4. Datapoint Architecture
From manual:
- Supports up to **25 rooms** (including special "Building" room)
- Each room has up to **16 functions**
- Generic ETS database supports up to **2000 datapoints** as flat list
- Metadata about rooms and functions can be read by clients
- Datapoints can have values and descriptions

### 5. Placeholder Variables
The manual mentions these placeholders for email notifications:
- `{value}` - Received datapoint value
- `{dp_id}` - Datapoint ID

## Typical BAOS REST API Patterns (Based on Similar Devices)

⚠️ **These are educated guesses based on similar BAOS devices - NOT confirmed from this manual**

### Probable Base URL Format
```
http://<device_ip>:<port>/rest/
```

Default ports for BAOS devices are typically:
- HTTP: 80
- HTTPS: 443
- Binary Protocol: 12004

### Likely Endpoints (UNCONFIRMED)

#### Get All Datapoints
```http
GET /rest/datapoints
```

#### Get Single Datapoint Value
```http
GET /rest/datapoint/<id>
```

#### Write Datapoint Value
```http
PUT /rest/datapoint/<id>
Content-Type: application/json

{
  "value": <value>
}
```

#### Get Datapoint Descriptions
```http
GET /rest/datapoint/<id>/description
```

#### Get All Rooms
```http
GET /rest/rooms
```

#### Get Room Functions
```http
GET /rest/room/<id>/functions
```

## Request/Response Format

Based on the manual's mention of "JSON-Syntax":
- **Format**: JSON
- **Content-Type**: `application/json`

## Authentication

The manual mentions:
- Username/password authentication for web interface
- Default: admin/admin
- Can be changed via ETS

**Unclear**: 
- Whether REST API requires HTTP Basic Auth
- Whether API keys are supported
- Session/cookie-based authentication

## Error Handling

⚠️ **Not documented in manual**

Typical HTTP status codes would be expected:
- 200 OK - Success
- 400 Bad Request - Invalid request
- 401 Unauthorized - Authentication required
- 404 Not Found - Resource not found
- 500 Internal Server Error

## Next Steps to Get Full API Documentation

To get complete REST API documentation, you should:

1. **Check Weinzierl Website**: Visit www.weinzierl.de/de/products/777 for additional documentation
2. **Contact Support**: support@weinzierl.de
3. **Download BAOS SDK**: Available for free at www.weinzierl.de - may contain API documentation
4. **Use Browser Developer Tools**: 
   - Access the web interface at `http://<device_ip>`
   - Open browser developer tools (F12)
   - Monitor Network tab to see actual REST API calls
   - This will reveal the real endpoints and data structures
5. **Check Other BAOS Models**: Look for documentation for BAOS 771/772/773/774 as the manual states compatibility

## Browser Developer Tools Method (RECOMMENDED)

The most reliable way to discover the actual REST API is:

```bash
# 1. Access the device web interface
http://192.168.1.xxx

# 2. Login with admin/admin

# 3. Open Browser DevTools (F12)

# 4. Go to Network tab

# 5. Filter for XHR/Fetch requests

# 6. Interact with the web interface (toggle lights, read sensors)

# 7. Observe the REST calls being made
```

This will show you:
- Exact endpoint URLs
- Request methods (GET/PUT/POST)
- Request payloads
- Response structures
- Authentication headers

## Python Example Template

Once you discover the real endpoints, use this template:

```python
import aiohttp
import asyncio
from typing import Optional, Dict, Any

class BAOSRestClient:
    """Client for Weinzierl BAOS REST API"""
    
    def __init__(self, host: str, port: int = 80, 
                 username: str = "admin", password: str = "admin"):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/rest"  # Adjust based on real API
        self.auth = aiohttp.BasicAuth(username, password)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(auth=self.auth)
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def get_datapoints(self) -> Dict[str, Any]:
        """Get all datapoints"""
        # Adjust endpoint based on real API
        async with self.session.get(f"{self.base_url}/datapoints") as resp:
            resp.raise_for_status()
            return await resp.json()
    
    async def get_datapoint_value(self, dp_id: int) -> Any:
        """Read datapoint value"""
        # Adjust endpoint based on real API
        async with self.session.get(f"{self.base_url}/datapoint/{dp_id}") as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("value")
    
    async def set_datapoint_value(self, dp_id: int, value: Any) -> bool:
        """Write datapoint value"""
        # Adjust endpoint and payload based on real API
        payload = {"value": value}
        async with self.session.put(
            f"{self.base_url}/datapoint/{dp_id}", 
            json=payload
        ) as resp:
            resp.raise_for_status()
            return resp.status == 200
    
    async def get_rooms(self) -> Dict[str, Any]:
        """Get all rooms"""
        # Adjust endpoint based on real API
        async with self.session.get(f"{self.base_url}/rooms") as resp:
            resp.raise_for_status()
            return await resp.json()

# Usage example
async def main():
    async with BAOSRestClient("192.168.1.100") as client:
        # Get all datapoints
        datapoints = await client.get_datapoints()
        print(f"Datapoints: {datapoints}")
        
        # Read datapoint 1
        value = await client.get_datapoint_value(1)
        print(f"Datapoint 1 value: {value}")
        
        # Write datapoint 1
        await client.set_datapoint_value(1, True)

if __name__ == "__main__":
    asyncio.run(main())
```

## Important Notes from Manual

1. **Service Control**: REST services can be disabled in Settings → Services
2. **Web Interface Dependency**: The web interface uses REST services internally
3. **ETS Integration**: Configuration via ETS 4.2 or higher required for full setup
4. **Authentication Changes**: Credentials set via ETS download override manual changes
5. **Firmware Updates**: Available at www.weinzierl.de/de/products/777

## Related Documentation

- ETS Database: Defines rooms and functions
- BAOS SDK: Free download at www.weinzierl.de (may contain API docs)
- Binary Protocol: For microcontroller applications
- Web Services Protocol: Compatible with BAOS 771/772/773/774

## Alternative: Use BAOS Binary Protocol Instead

Since the REST API is not documented, consider using the well-documented **BAOS Binary Protocol**:

### Binary Protocol Details
- **Port**: 12004 (UDP/TCP)
- **Protocol**: Binary, well-documented
- **SDK Available**: Free download at www.weinzierl.de
- **Libraries**: Multiple community implementations available

### Python BAOS Binary Protocol Example

```python
# Using a hypothetical BAOS library
from baos import BAOSConnection

async def main():
    conn = BAOSConnection("192.168.1.100", 12004)
    await conn.connect()
    
    # Get datapoint value
    value = await conn.get_datapoint_value(1)
    
    # Set datapoint value
    await conn.set_datapoint_value(1, True)
    
    await conn.disconnect()
```

## Comparison: REST vs Binary Protocol

| Feature | REST API | Binary Protocol |
|---------|----------|-----------------|
| Documentation | ❌ Not in manual | ✅ SDK available |
| Port | Unknown (80/443?) | 12004 |
| Ease of Use | ✅ Simple HTTP | ⚠️ Binary parsing |
| Performance | ⚠️ HTTP overhead | ✅ Efficient |
| Authentication | Unknown | Documented |
| Libraries | Unknown | SDK available |

## Practical Discovery Method

If you have access to a real BAOS 777 device:

```bash
# 1. Find the device IP (check DHCP server or device display)
DEVICE_IP="192.168.1.xxx"

# 2. Scan for open ports
nmap -p 80,443,12004,3671 $DEVICE_IP

# 3. Access web interface
firefox http://$DEVICE_IP

# 4. Login with admin/admin

# 5. Open Browser DevTools (F12) → Network tab

# 6. Filter: XHR

# 7. Click around in the web interface

# 8. Watch the REST API calls!
```

### What to Look For in DevTools

When you interact with the web UI, look for:
- **URL patterns**: `/rest/...`, `/api/...`, `/baos/...`
- **Request Method**: GET, PUT, POST
- **Request Payload**: JSON structure
- **Response Data**: JSON structure
- **Headers**: Authorization, Content-Type

### Example of What You Might Find

```
# Clicking a light switch might show:
PUT http://192.168.1.100/rest/datapoint/42/value
Content-Type: application/json
Authorization: Basic YWRtaW46YWRtaW4=

{"value": true}

# Response:
200 OK
{"id": 42, "value": true, "timestamp": "2025-12-20T22:30:00Z"}
```

## Known BAOS REST API Patterns (From Community)

Based on community implementations for similar BAOS devices:

### Common Endpoint Patterns

```
GET  /rest/datapoints              → List all datapoints
GET  /rest/datapoint/{id}          → Get datapoint info
GET  /rest/datapoint/{id}/value    → Get current value
PUT  /rest/datapoint/{id}/value    → Set new value
GET  /rest/rooms                   → List rooms
GET  /rest/room/{id}/functions     → Get room functions
```

### Typical Response Format

```json
{
  "id": 1,
  "name": "Living Room Light",
  "value": true,
  "type": "DPT-1",
  "room": "Living Room",
  "function": "Lighting",
  "timestamp": "2025-12-20T22:30:00Z"
}
```

## Integration with Your Home Assistant Component

Your current implementation uses KNX tunneling (port 3671). To add REST API support:

```python
# In custom_components/luxor_living/

class BAOSRestClient:
    """REST API client for BAOS devices"""
    
    def __init__(self, host: str, username: str, password: str):
        self.base_url = f"http://{host}/rest"  # Adjust after discovery
        self.auth = aiohttp.BasicAuth(username, password)
    
    async def get_datapoint(self, dp_id: int):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/datapoint/{dp_id}/value",
                auth=self.auth
            ) as resp:
                return await resp.json()
    
    async def set_datapoint(self, dp_id: int, value):
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.base_url}/datapoint/{dp_id}/value",
                json={"value": value},
                auth=self.auth
            ) as resp:
                return resp.status == 200
```

## Conclusion

**The manual does NOT contain detailed REST API specification.** 

### Your Options:

1. **✅ RECOMMENDED**: Use **browser DevTools** on a real device to discover the API
2. **✅ ALTERNATIVE**: Use the **BAOS Binary Protocol** (port 12004) with SDK
3. **⚠️ FALLBACK**: Continue using **KNX tunneling** (your current implementation)
4. **📧 SUPPORT**: Contact support@weinzierl.de for official REST API docs
5. **📚 SDK**: Download BAOS SDK from www.weinzierl.de (may contain API docs)

### Why REST API Documentation is Missing

The manual appears to be focused on:
- Device installation and configuration
- Web interface usage for end users
- ETS integration
- General feature overview

The REST API is mentioned as a feature but detailed developer documentation is likely:
- In a separate SDK/API manual
- Part of the BAOS SDK download
- Available on the Weinzierl developer portal
- Intended to be discovered through the device itself

### Next Steps

1. If you have a **physical device**: Use DevTools method above
2. If you need **immediate implementation**: Use Binary Protocol (port 12004)
3. If you want **official docs**: Contact Weinzierl support
4. If you're **simulating**: Implement mock REST endpoints based on probable patterns

The information in this document is based on what's explicitly stated in the manual plus educated guesses from similar BAOS devices and community implementations.
