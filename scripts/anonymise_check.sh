#!/usr/bin/env bash
# Fail if tracked files contain private data (hosts, local paths, customer files).
# Extra patterns can be kept out of the repo in .anonymise-denylist (one regex per line, gitignored).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

patterns=(
  '100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]+\.[0-9]+'  # Tailscale CGNAT range
  '/home/[a-z][a-z0-9_-]*/'                                      # personal home paths
  'Nextcloud'
)
[ -f .anonymise-denylist ] && while IFS= read -r p; do [ -n "$p" ] && patterns+=("$p"); done < .anonymise-denylist

status=0
for p in "${patterns[@]}"; do
  hits=$(git grep -nIE -e "$p" -- . ':!scripts/anonymise_check.sh' ':!*.lock' | grep -vE '/home/(user|runner|vscode|homeassistant)/' || true)
  if [ -n "$hits" ]; then echo "private-data pattern '$p':"; echo "$hits" | head -20; status=1; fi
done

bad=$(git ls-files | grep -iE '\.(lxp|log|zip|knxprod)$|^docs/.*\.pdf$' | grep -v '^tests/fixtures/' || true)
if [ -n "$bad" ]; then echo "tracked private/vendor files:"; echo "$bad"; status=1; fi
exit $status
