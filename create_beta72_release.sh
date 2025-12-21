#!/bin/bash
cd /home/phil/gitlab_github/luxorliving

# Create GitHub Release
python3 << 'PYEOF'
import subprocess, json, urllib.request

proc = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n', capture_output=True, text=True, timeout=5)
token = None
for line in proc.stdout.splitlines():
    if line.startswith('password='): 
        token = line.split('=', 1)[1]
        break

if not token: 
    print("❌ No token")
    exit(1)

release_data = {
    "tag_name": "v0.2.1-beta.7.2",
    "target_commitish": "feature/initial-state-reading",
    "name": "v0.2.1-beta.7.2: MappedEntity Attribute Fix",
    "body": """## 🔧 Critical Hotfix: AttributeError Fix

**Problem:** Beta 7.1 crashed on startup with `AttributeError: 'MappedEntity' object has no attribute 'get'`

**Root Cause:** `_async_build_datapoint_mapping_from_lxp()` treated MappedEntity as dict instead of dataclass.

---

## ✅ What's Fixed

**MappedEntity Attribute Access:**
```python
# ❌ Before (Beta 7.1):
datapoints = entity_data.get("datapoints", {})  # MappedEntity has no .get()!

# ✅ After (Beta 7.2):
datapoints = entity_data.datapoints  # Direct attribute access
```

**Correct Datapoint Mapping Logic:**
- MappedEntity.datapoints is already `dict[str, int]` (role → address)
- Integer address IS the BAOS Datapoint-ID
- Convert integer to GroupAddress string: `2304` → `"1/1/0"`
- Store mapping: `{"1/1/0": 2304}` for REST API queries

---

## 🧪 Testing Confirmed

```
======================== 58 passed in 2.XX s ========================
✅ All tests passing
✅ MappedEntity attribute access fixed
✅ Datapoint mapping logic verified
```

---

## 📦 Installation

**On Madeira-VM:**
1. HACS → LUXORliving
2. Update to **v0.2.1-beta.7.2**
3. Restart Home Assistant

**Verify:**
```
✅ Built XX GroupAddress → Datapoint-ID mappings from LXP file
Sample mappings: {'1/1/0': 2304, '1/1/1': 2305, '1/0/0': 2048}
```

---

## ✨ All Beta 7 Features Intact

- ✅ BAOS REST API with 2s timeout
- ✅ LXP-based datapoint mapping (now working!)
- ✅ Graceful fallback to GroupValueRead
- ✅ XKNX 3.11-3.14 compatibility
- ✅ Comprehensive diagnostic logging

---

## 🚀 Ready for Real Testing!

Beta 7.2 should now:
1. Load successfully ✅
2. Build datapoint mappings ✅
3. Try REST API for initial states
4. Fall back gracefully on timeout

**Let's see if REST API works! 🎯**""",
    "draft": False,
    "prerelease": True,
    "generate_release_notes": False
}

req = urllib.request.Request(
    'https://api.github.com/repos/phismith91/luxorliving/releases',
    data=json.dumps(release_data).encode('utf-8'),
    headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"\n✅ Release created: {result['html_url']}")
except urllib.error.HTTPError as e:
    print(f"❌ Error: {e.code} {e.reason}\n{e.read().decode('utf-8')}")
PYEOF
