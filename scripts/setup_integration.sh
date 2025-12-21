#!/bin/bash
# Quick Setup Script for LUXORliving Integration

set -e

echo "🔥 LUXORliving Integration Setup Script"
echo "========================================"
echo ""

# Configuration
LXP_FILE="/home/phil/.homeassistant/luxor_living/Schmidt_Madeira_V0.8.lxp"
HOST="localhost"
PORT="3671"
USERNAME="admin"
PASSWORD="admin"
CONNECTION_TYPE="tunneling"
SIMULATION_MODE="false"

# Verify LXP file exists
if [ ! -f "$LXP_FILE" ]; then
    echo "❌ ERROR: LXP file not found: $LXP_FILE"
    exit 1
fi

echo "✅ LXP file found: $LXP_FILE"
echo ""

# Stop Home Assistant
echo "🛑 Stopping Home Assistant..."
pkill -f "hass -c" 2>/dev/null || true
sleep 2

# Create config entry
echo "📝 Creating config entry..."
python3 << 'EOF'
import json
from pathlib import Path
from datetime import datetime, timezone
import secrets
import os

# Configuration from environment
lxp_file = os.environ.get('LXP_FILE', '/home/phil/.homeassistant/luxor_living/Schmidt_Madeira_V0.8.lxp')
host = os.environ.get('HOST', 'localhost')
port = int(os.environ.get('PORT', '3671'))
username = os.environ.get('USERNAME', 'admin')
password = os.environ.get('PASSWORD', 'admin')
connection_type = os.environ.get('CONNECTION_TYPE', 'tunneling')
simulation_mode = os.environ.get('SIMULATION_MODE', 'false').lower() == 'true'

storage_file = Path.home() / '.homeassistant/.storage/core.config_entries'

# Load existing data
with open(storage_file) as f:
    data = json.load(f)

# Remove any existing luxor_living entries
original_count = len(data['data']['entries'])
data['data']['entries'] = [e for e in data['data']['entries'] if e['domain'] != 'luxor_living']
removed = original_count - len(data['data']['entries'])

if removed > 0:
    print(f"🗑️  Removed {removed} old luxor_living entry/entries")

# Create new entry
now = datetime.now(timezone.utc).isoformat()
entry_id = secrets.token_urlsafe(20).replace('-', '').replace('_', '').upper()[:26]

new_entry = {
    "entry_id": entry_id,
    "version": 1,
    "minor_version": 1,
    "domain": "luxor_living",
    "title": "LUXORliving",
    "data": {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "lxp_file": lxp_file,
        "connection_type": connection_type,
        "simulation_mode": simulation_mode
    },
    "options": {},
    "pref_disable_new_entities": False,
    "pref_disable_polling": False,
    "source": "user",
    "unique_id": None,
    "disabled_by": None,
    "created_at": now,
    "modified_at": now,
    "discovery_keys": {}
}

data['data']['entries'].append(new_entry)

# Save
with open(storage_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"✅ Created config entry: {entry_id}")
print(f"   Host: {host}:{port}")
print(f"   LXP: {lxp_file}")
print(f"   Connection: {connection_type}")
print(f"   Simulation: {simulation_mode}")
EOF

export LXP_FILE HOST PORT USERNAME PASSWORD CONNECTION_TYPE SIMULATION_MODE

echo ""
echo "🧹 Cleaning Python cache..."
find ~/.homeassistant/custom_components/luxor_living -name "*.pyc" -delete 2>/dev/null || true
find ~/.homeassistant/custom_components/luxor_living -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "🚀 Starting Home Assistant..."
cd /home/phil/gitlab_github/luxorliving/scripts
./start_homeassistant.sh &

echo ""
echo "⏳ Waiting for startup (5 seconds)..."
sleep 5

echo ""
echo "📋 Checking logs..."
tail -50 ~/.homeassistant/home-assistant.log | grep -E "luxor_living|LUXOR SETUP" | tail -20

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next Steps:"
echo "   1. Open Home Assistant UI"
echo "   2. Go to Settings → Devices & Services"
echo "   3. Find 'LUXORliving' integration"
echo "   4. Check if entities are loaded"
echo "   5. Monitor logs: tail -f ~/.homeassistant/home-assistant.log"
echo ""
echo "🔍 Debug Commands:"
echo "   # Check config entry:"
echo "   python3 -c 'import json; d=json.load(open(\"~/.homeassistant/.storage/core.config_entries\".replace(\"~\",\"$HOME\"))); print([e for e in d[\"data\"][\"entries\"] if e[\"domain\"]==\"luxor_living\"])'"
echo ""
echo "   # Watch logs:"
echo "   tail -f ~/.homeassistant/home-assistant.log | grep luxor_living"
echo ""
