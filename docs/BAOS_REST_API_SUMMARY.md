# BAOS 777 REST API - Summary Report

## Executive Summary

**Status**: ❌ REST API documentation is **NOT included** in the device manual

**Date**: December 20, 2025  
**Source**: weinzierl-777-knx-ip-baos-5193-manual-de.pdf (German manual, 73 pages)  
**Analyzed**: Complete manual text extraction and keyword search

## What the Manual Contains

### REST API Mentions
The manual mentions "KNX IP BAOS RESTful Web Services" in several places:

1. **Page 4/5**: Listed as one of three protocol variants:
   - KNX IP BAOS Binary
   - KNX IP BAOS Web Services
   - **KNX IP BAOS RESTful Web Services** ← Mentioned but not documented

2. **Page 54**: Services configuration page
   - Shows that REST Services can be enabled/disabled
   - Warning: Disabling breaks client applications and web interface

3. **General Description**:
   - "URL-based protocol with RESTful JSON-Syntax"
   - "For integration in browser-based web applications"
   - "Compatible with BAOS 771/772/773/774"

### What IS Documented

The manual focuses on:
- ✅ Physical installation (DIN rail mounting)
- ✅ Network configuration (DHCP, manual IP)
- ✅ Web interface usage
- ✅ ETS integration
- ✅ Room/function configuration (25 rooms, 16 functions each)
- ✅ Datapoint architecture (up to 2000 datapoints)
- ✅ Email notifications
- ✅ Timer functions
- ✅ History recording
- ✅ Firmware updates

### Default Configuration

```yaml
Default Credentials:
  username: admin
  password: admin
  warning: "Should be changed via ETS"

Network:
  ip_assignment: DHCP
  default_ip: Unknown (assigned by DHCP server)
  
KNX Addresses:
  device: 15.15.255
  tunnel_1: 15.15.240
  tunnel_2: 15.15.241
  # ... up to tunnel_8: 15.15.247

Ports (Typical):
  http: 80 (assumed, not explicitly stated)
  https: 443 (assumed, not explicitly stated)
  knxnet_ip: 3671 (standard KNX port)
  binary_protocol: 12004 (typical BAOS port)
```

## What the Manual DOES NOT Contain

### Missing REST API Information

❌ **Endpoints**: No endpoint paths documented
- Not listed: `/rest/datapoints`, `/rest/datapoint/{id}`, etc.
- Not specified: Resource paths, query parameters

❌ **HTTP Methods**: No method specifications
- Not documented: GET, PUT, POST, DELETE usage
- Not specified: Which operations use which methods

❌ **Request Format**: No request examples
- Not shown: JSON payload structure
- Not specified: Required/optional fields

❌ **Response Format**: No response examples
- Not shown: Response JSON structure
- Not specified: Status codes, error formats

❌ **Authentication**: No auth details
- Not specified: HTTP Basic Auth vs. session-based
- Not shown: How to authenticate API requests
- Not clear: If API uses same credentials as web interface

❌ **Data Types**: No datapoint type mappings
- Not documented: How to encode/decode values
- Not specified: Type conversion rules
- Not shown: DPT (DataPoint Type) handling

❌ **Subscriptions**: No real-time update mechanism
- Not documented: WebSocket support
- Not specified: Server-Sent Events
- Not shown: Long-polling patterns

❌ **Port Numbers**: No explicit API port
- Not stated: Which port REST API listens on
- Assumed: Likely 80/443 but not confirmed

## How to Get REST API Documentation

### Option 1: Browser DevTools (RECOMMENDED ✅)

**Why**: The web interface uses the REST API internally

**Steps**:
1. Access device at `http://<device_ip>` (default: admin/admin)
2. Open browser Developer Tools (F12)
3. Go to Network tab → Filter XHR/Fetch
4. Interact with web interface
5. Observe and document API calls

**Result**: Real endpoint paths, payload structures, authentication

**See**: [BAOS_REST_API_DISCOVERY.md](BAOS_REST_API_DISCOVERY.md) for detailed guide

### Option 2: BAOS SDK Download

**Where**: www.weinzierl.de  
**What**: Free SDK may contain API documentation  
**Format**: Likely includes API reference, examples  
**Languages**: Probably supports multiple languages

### Option 3: Contact Weinzierl Support

**Email**: support@weinzierl.de  
**Request**: "REST API documentation for BAOS 777"  
**Include**: Product name, firmware version  
**Response Time**: Unknown

### Option 4: Check Similar Models

**Models**: BAOS 771, 772, 773, 774  
**Reason**: Manual states REST API is "compatible"  
**Assumption**: Endpoints might be identical  
**Risk**: May differ in details

### Option 5: Use Binary Protocol Instead

**Port**: 12004  
**Documentation**: Available in SDK  
**Advantage**: Well-documented, stable  
**Disadvantage**: More complex than REST

## Educated Guesses (NOT Confirmed)

Based on typical BAOS implementations and REST conventions:

### Probable Base URL
```
http://<device_ip>/rest/
# or
http://<device_ip>/api/
```

### Likely Endpoints
```
GET  /rest/datapoints              → List all datapoints
GET  /rest/datapoint/{id}          → Get datapoint details
GET  /rest/datapoint/{id}/value    → Get current value
PUT  /rest/datapoint/{id}/value    → Set new value
POST /rest/datapoint/{id}/value    → Set new value (alternative)
GET  /rest/rooms                   → List rooms
GET  /rest/room/{id}               → Get room details
GET  /rest/functions               → List functions
```

### Probable Authentication
```http
Authorization: Basic <base64(admin:admin)>
# or
Cookie: session=<session_token>
```

### Probable JSON Format
```json
{
  "id": 1,
  "name": "Living Room Light",
  "value": true,
  "type": "DPT-1.001",
  "room": "Living Room",
  "function": "Lighting",
  "timestamp": "2025-12-20T22:30:00Z"
}
```

⚠️ **Warning**: These are guesses based on patterns from similar devices. **DO NOT** rely on them for production code without verification.

## Recommendations

### For Immediate Development

1. **If you have a physical device**:
   - ✅ Use DevTools method (see BAOS_REST_API_DISCOVERY.md)
   - ✅ Document findings
   - ✅ Share with community

2. **If you don't have a device**:
   - ⚠️ Download BAOS SDK and check documentation
   - ⚠️ Contact Weinzierl support
   - ⚠️ Use Binary Protocol (port 12004) instead

3. **For your Home Assistant integration**:
   - ✅ Continue using KNX tunneling (port 3671) - already working
   - ⚠️ Add REST API as optional enhancement later
   - ⚠️ Implement with proper error handling for unknown API

### Documentation to Create

Once you discover the real API:

```markdown
docs/
  ├── BAOS_REST_API.md              ← Already created (theoretical)
  ├── BAOS_REST_API_DISCOVERY.md    ← Already created (how-to guide)
  ├── BAOS_REST_API_REFERENCE.md    ← To create (real endpoints)
  └── BAOS_REST_API_EXAMPLES.md     ← To create (real examples)
```

## Files Created

1. **[BAOS_REST_API.md](BAOS_REST_API.md)**
   - Theoretical REST API documentation
   - Based on manual mentions and educated guesses
   - Includes Python client template
   - Comparison with Binary Protocol

2. **[BAOS_REST_API_DISCOVERY.md](BAOS_REST_API_DISCOVERY.md)**
   - Practical guide to discover real API
   - Browser DevTools method (step-by-step)
   - Network capture alternatives
   - Testing scripts and examples

3. **BAOS_REST_API_SUMMARY.md** (this file)
   - Executive summary of findings
   - What's documented vs. what's missing
   - Recommendations and next steps

## Conclusion

**The Weinzierl BAOS 777 manual does NOT contain REST API documentation.**

The manual:
- ✅ Confirms REST API exists
- ✅ States it uses "RESTful JSON-Syntax"
- ✅ Shows it can be enabled/disabled
- ❌ Does NOT document endpoints, methods, or data formats
- ❌ Does NOT provide examples or specifications

**Next Steps**:
1. Use browser DevTools on real device (recommended)
2. Download BAOS SDK from www.weinzierl.de
3. Contact support@weinzierl.de for API docs
4. Consider using Binary Protocol (well-documented alternative)
5. Check documentation for BAOS 771/772/773/774 models

**For Your Project**:
- Current KNX tunneling implementation (port 3671) should continue working
- REST API can be added later as enhancement
- Focus on discovering real API through DevTools method
- Document findings for community benefit

---

**Report Generated**: December 20, 2025  
**Source Document**: weinzierl-777-knx-ip-baos-5193-manual-de.pdf  
**Pages Analyzed**: 73 pages (2549 lines of text)  
**Keywords Searched**: REST, API, HTTP, endpoint, JSON, GET, PUT, POST, DELETE, datapoint, value
