#!/usr/bin/env bash
set -euo pipefail

# Simple HACS metadata validator for Gold compliance
ROOT=$(git rev-parse --show-toplevel)
HACS_FILE="$ROOT/hacs.json"
MANIFEST_FILE="$ROOT/custom_components/luxor_living/manifest.json"

if [ ! -f "$HACS_FILE" ]; then
  echo "ERROR: hacs.json not found at repository root"
  exit 1
fi

python - <<'PY'
import json,sys
h=json.load(open('hacs.json'))
req_keys=['name','filename','zip_release','content_in_root','homeassistant']
for k in req_keys:
    if k not in h:
        print('ERROR: hacs.json missing key:',k)
        sys.exit(2)
# filename should look like *.zip
if not h['filename'].endswith('.zip'):
    print('ERROR: hacs.json filename must end with .zip')
    sys.exit(2)
print('hacs.json basic checks passed')
PY

# Basic manifest checks
if [ ! -f "$MANIFEST_FILE" ]; then
  echo "ERROR: manifest.json not found in custom_components/luxor_living"
  exit 1
fi

python - <<'PY'
import json,sys
m=json.load(open('custom_components/luxor_living/manifest.json'))
req=['domain','name','documentation','issue_tracker','version']
for k in req:
    if k not in m:
        print('ERROR: manifest.json missing key:',k)
        sys.exit(2)
print('manifest.json basic checks passed')
PY

echo "HACS validation: OK"
exit 0
