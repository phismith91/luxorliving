# BAOS 777 REST API Discovery Guide

## Quick Start: Discover the Real API

The manual doesn't document the REST API endpoints. Here's how to discover them yourself.

## Method 1: Browser DevTools (RECOMMENDED)

### Step-by-Step Guide

#### 1. Access the Device
```bash
# Find your BAOS device IP
# Check your DHCP server or look at the device display

# Open in browser
http://192.168.1.xxx
# or
https://192.168.1.xxx
```

#### 2. Open Developer Tools
- **Chrome/Edge**: Press `F12` or `Ctrl+Shift+I`
- **Firefox**: Press `F12` or `Ctrl+Shift+K`
- **Safari**: Enable Developer menu, then press `Cmd+Opt+I`

#### 3. Navigate to Network Tab
- Click on "Network" tab
- Click the filter icon
- Select "XHR" or "Fetch" to show only API calls

#### 4. Login to Web Interface
- Username: `admin`
- Password: `admin` (unless changed)

#### 5. Interact with the Interface
- Turn lights on/off
- Adjust dimmers
- Open/close blinds
- Read sensor values

#### 6. Observe the API Calls

For each action, you'll see API calls like:

```
Request:
PUT http://192.168.1.100/rest/datapoint/42/value
Content-Type: application/json
Authorization: Basic YWRtaW46YWRtaW4=

Request Payload:
{"value": true}

Response:
Status: 200 OK
{
  "id": 42,
  "value": true,
  "timestamp": "2025-12-20T22:30:00Z"
}
```

#### 7. Document What You Find

Create a table like this:

| Action | Method | Endpoint | Payload | Response |
|--------|--------|----------|---------|----------|
| Get all DPs | GET | /rest/datapoints | - | Array of DP objects |
| Get DP value | GET | /rest/datapoint/{id} | - | DP object with value |
| Set DP value | PUT | /rest/datapoint/{id}/value | {"value": ...} | Success status |
| Get rooms | GET | /rest/rooms | - | Array of rooms |

## Method 2: Network Packet Capture

If DevTools doesn't work (HTTPS with cert issues), use packet capture:

```bash
# Install Wireshark or use tcpdump
sudo tcpdump -i eth0 -A 'host 192.168.1.xxx and port 80' -w baos_capture.pcap

# Then open in Wireshark and filter for HTTP
```

## Method 3: Port Scanning

Find which ports are open:

```bash
# Scan common ports
nmap -p 80,443,12004,3671 192.168.1.xxx

# Detailed scan
nmap -sV -p- 192.168.1.xxx
```

Expected results:
- **Port 80**: HTTP (Web interface + REST API)
- **Port 443**: HTTPS (Secure web interface + REST API)
- **Port 3671**: KNXnet/IP (Tunneling protocol)
- **Port 12004**: BAOS Binary Protocol

## Method 4: API Fuzzing

Try common REST API patterns:

```bash
#!/bin/bash
DEVICE="192.168.1.xxx"
AUTH="admin:admin"

# Test common endpoints
endpoints=(
    "/rest/datapoints"
    "/rest/datapoint/1"
    "/rest/datapoint/1/value"
    "/api/datapoints"
    "/api/v1/datapoints"
    "/baos/datapoints"
    "/datapoints"
    "/dp"
    "/rest/rooms"
    "/rest/functions"
)

for endpoint in "${endpoints[@]}"; do
    echo "Testing: $endpoint"
    curl -u "$AUTH" -s -o /dev/null -w "HTTP %{http_code}\n" "http://$DEVICE$endpoint"
done
```

## Method 5: Reverse Engineer JavaScript

```bash
# Download the web interface JavaScript
wget http://192.168.1.xxx/app.js
wget http://192.168.1.xxx/main.js

# Search for API endpoints
grep -E "(http|fetch|axios|ajax)" *.js | grep -E "(rest|api|datapoint)"

# Look for REST calls
grep -E "\.get\(|\.post\(|\.put\(" *.js
```

## Expected API Structure

Based on typical BAOS implementations:

### Authentication
```http
Authorization: Basic YWRtaW46YWRtaW4=
# or
Cookie: session=xxx
```

### Datapoint Operations

#### List All Datapoints
```http
GET /rest/datapoints HTTP/1.1
Host: 192.168.1.xxx
Authorization: Basic YWRtaW46YWRtaW4=

Response:
[
  {
    "id": 1,
    "name": "Light Kitchen",
    "value": false,
    "type": "DPT-1.001",
    "room": "Kitchen",
    "function": "Lighting"
  },
  ...
]
```

#### Read Datapoint
```http
GET /rest/datapoint/1 HTTP/1.1

Response:
{
  "id": 1,
  "name": "Light Kitchen",
  "value": false,
  "type": "DPT-1.001",
  "updatedAt": "2025-12-20T22:30:00Z"
}
```

#### Write Datapoint
```http
PUT /rest/datapoint/1/value HTTP/1.1
Content-Type: application/json

{"value": true}

Response:
{
  "success": true,
  "id": 1,
  "value": true
}
```

### Room Operations

#### List Rooms
```http
GET /rest/rooms HTTP/1.1

Response:
[
  {
    "id": 1,
    "name": "Living Room",
    "functions": [...]
  },
  ...
]
```

#### Get Room Details
```http
GET /rest/room/1 HTTP/1.1

Response:
{
  "id": 1,
  "name": "Living Room",
  "functions": [
    {
      "id": 1,
      "name": "Ceiling Light",
      "type": "switch",
      "datapointId": 42
    }
  ]
}
```

## Creating a Test Script

Once you know the endpoints, test them:

```python
#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth

DEVICE_IP = "192.168.1.xxx"
USERNAME = "admin"
PASSWORD = "admin"

def test_api():
    base_url = f"http://{DEVICE_IP}/rest"
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    
    # Test 1: Get all datapoints
    print("Testing GET /rest/datapoints...")
    resp = requests.get(f"{base_url}/datapoints", auth=auth)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Response: {resp.json()}")
    
    # Test 2: Get single datapoint
    print("\nTesting GET /rest/datapoint/1...")
    resp = requests.get(f"{base_url}/datapoint/1", auth=auth)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Response: {resp.json()}")
    
    # Test 3: Write datapoint
    print("\nTesting PUT /rest/datapoint/1/value...")
    resp = requests.put(
        f"{base_url}/datapoint/1/value", 
        json={"value": True},
        auth=auth
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Response: {resp.json()}")

if __name__ == "__main__":
    test_api()
```

## Common Issues & Solutions

### Issue: 401 Unauthorized
**Solution**: Check username/password. Default is admin/admin unless changed via ETS.

### Issue: 404 Not Found
**Solution**: The endpoint path is different. Use DevTools to find the real path.

### Issue: CORS Errors
**Solution**: Not an issue when using Python/curl, only in browser. For browser testing, disable CORS or use a proxy.

### Issue: Certificate Errors (HTTPS)
**Solution**: 
```python
# Python: Disable SSL verification (only for testing!)
requests.get(url, verify=False)

# Curl: Disable SSL verification
curl -k https://...
```

### Issue: Connection Refused
**Solution**: 
- Check if REST services are enabled in device settings
- Verify the device IP is correct
- Check firewall rules

## After Discovery: Update Your Code

Once you've discovered the real API, update your implementation:

```python
# custom_components/luxor_living/baos_rest_client.py

import aiohttp
from typing import Any, Dict, List

class BAOSRestClient:
    """Client for BAOS REST API - Updated with real endpoints"""
    
    def __init__(self, host: str, username: str = "admin", password: str = "admin"):
        # Update base_url based on discovery
        self.base_url = f"http://{host}/rest"  # Adjust as needed
        self.auth = aiohttp.BasicAuth(username, password)
    
    async def get_datapoints(self) -> List[Dict[str, Any]]:
        """Get all datapoints"""
        # Update endpoint based on discovery
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/datapoints",
                auth=self.auth
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
    
    async def get_datapoint_value(self, dp_id: int) -> Any:
        """Read datapoint value"""
        # Update endpoint based on discovery
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/datapoint/{dp_id}",
                auth=self.auth
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["value"]  # Adjust field name based on discovery
    
    async def set_datapoint_value(self, dp_id: int, value: Any) -> bool:
        """Write datapoint value"""
        # Update endpoint and payload based on discovery
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.base_url}/datapoint/{dp_id}/value",
                json={"value": value},  # Adjust payload structure
                auth=self.auth
            ) as resp:
                resp.raise_for_status()
                return True
```

## Summary

1. ✅ **Use Browser DevTools** - Most reliable method
2. ✅ **Test with curl/Python** - Verify findings
3. ✅ **Document everything** - Create API reference for your team
4. ✅ **Update your code** - Implement based on real API
5. ✅ **Share findings** - Help the community!

## Community Resources

If you successfully discover the API, please share:
- GitHub repository with findings
- Documentation on Home Assistant forum
- Issue/PR to this project

This helps other developers working with BAOS devices!

## Alternative: Use Binary Protocol

If REST API proves too difficult to discover or is not available:

```python
# Use the well-documented BAOS Binary Protocol
# Port: 12004
# SDK: Available at www.weinzierl.de

# Many Python libraries exist for BAOS Binary Protocol:
# - pybaosBinary Protocol instead of REST. It's well-documented and has SDK support.

## Contact Support

If all else fails:
- **Email**: support@weinzierl.de
- **Website**: www.weinzierl.de
- **Request**: "REST API documentation for BAOS 777"
