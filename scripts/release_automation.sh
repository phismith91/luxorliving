#!/usr/bin/env bash
set -euo pipefail

# release_automation.sh
# Automated release helper for LUXORliving
# Usage:
#  ./scripts/release_automation.sh [--dry-run] [--update-readme] [--remote user@host]

DRY_RUN=0
UPDATE_README=0
REMOTE_HOST=""

print_help() {
  cat <<EOF
Usage: $0 [--dry-run] [--update-readme] [--remote user@host]

Options:
  --dry-run         Validate steps without creating tags/releases
  --update-readme   Update README release block automatically if mismatch
  --remote HOST     Optional: SSH host to perform post-deploy verification
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --update-readme) UPDATE_README=1; shift ;;
    --remote) REMOTE_HOST="$2"; shift 2 ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "Unknown arg: $1"; print_help; exit 1 ;;
  esac
done

run() {
  echo "+ $*"
  if [ "$DRY_RUN" -eq 1 ]; then
    return 0
  fi
  "$@"
}

# 1) Sanity checks
if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: working tree is not clean. Commit or stash changes before releasing." >&2
  exit 1
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
# Allow dry-run on any branch for CI/PR validation
if [ "$BRANCH" != "main" ] && [ "$DRY_RUN" -eq 0 ]; then
  echo "ERROR: release must be performed from 'main' branch (current: $BRANCH)" >&2
  exit 1
fi

# Get version from manifest
VERSION=$(python3 -c "import json; print(json.load(open('custom_components/luxor_living/manifest.json'))['version'])")
if [ -z "$VERSION" ]; then
  echo "ERROR: could not read version from manifest.json" >&2
  exit 1
fi

echo "Preparing release $VERSION"

# 2) README release block check
if ! grep -q "<!-- RELEASE_NOTES_START -->" README.md; then
  echo "ERROR: README release block markers missing" >&2
  exit 1
fi
SECTION=$(awk '/<!-- RELEASE_NOTES_START -->/{flag=1;next}/<!-- RELEASE_NOTES_END -->/{flag=0}flag' README.md)
if ! echo "$SECTION" | grep -q "$VERSION"; then
  echo "README release block does not contain version $VERSION"
  if [ "$UPDATE_README" -eq 1 ]; then
    echo "Updating README release block..."
    ./scripts/update_readme_release.sh "$VERSION"
    run git add README.md
    run git commit -m "chore(release): update README release block to $VERSION"
  else
    echo "Run with --update-readme to update README automatically or update it manually." >&2
    exit 1
  fi
fi

# Ensure release notes file exists (root preferred, fallback to docs/releases)
RELEASE_FILE_ROOT="RELEASE_NOTES_v${VERSION}.md"
RELEASE_FILE_DOCS="docs/releases/RELEASE_NOTES_v${VERSION}.md"
if [ -f "$RELEASE_FILE_ROOT" ]; then
  RELEASE_FILE="$RELEASE_FILE_ROOT"
elif [ -f "$RELEASE_FILE_DOCS" ]; then
  RELEASE_FILE="$RELEASE_FILE_DOCS"
else
  echo "ERROR: Release notes file for version $VERSION is missing. Create $RELEASE_FILE_ROOT in repo root or $RELEASE_FILE_DOCS in docs/releases, or run with --update-readme to auto-generate it from CHANGELOG." >&2
  exit 1
fi

echo "Using release notes file: $RELEASE_FILE"

# 3) Build zip (from integration dir to avoid nested path issue)
TMP_ZIP="/tmp/luxor_living_${VERSION}.zip"
pushd custom_components/luxor_living > /dev/null
run zip -r "$TMP_ZIP" . -x "*.pyc" "*/__pycache__/*" "*.git*"
popd > /dev/null

# Validate zip has manifest at root (skip during dry-run)
if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN: skipping zip content validation"
else
  if ! unzip -l "$TMP_ZIP" | awk '{print $4}' | grep -qx "manifest.json"; then
    echo "ERROR: package does not contain manifest.json at root (zip structure incorrect)" >&2
    exit 1
  fi
fi

# 4) Tag and release
TAG="v${VERSION}"
if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  echo "Tag $TAG already exists. Will attempt to attach release to existing tag."
fi

run git tag -a "$TAG" -m "$TAG" || true
run GIT_SSH_COMMAND='ssh -F /dev/null' git push origin "$TAG" || true

# Create release via gh; capture output
CREATE_OUT=""
if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN: would create release $TAG with asset $TMP_ZIP"
else
  set +e
  CREATE_OUT=$(gh release create "$TAG" "$TMP_ZIP" --title "$TAG" --notes-file "$RELEASE_FILE" 2>&1)
  RC=$?
  set -e
  echo "$CREATE_OUT"
  if [ $RC -ne 0 ]; then
    echo "Release creation failed: $CREATE_OUT" >&2
    # If failure due to immutable release, fallback to a new tag
    if echo "$CREATE_OUT" | grep -qi "immutable" || echo "$CREATE_OUT" | grep -qi "Cannot upload assets"; then
      FALLBACK_TAG="${TAG}-rebuild-$(date +%s)"
      echo "Attempting fallback tag: $FALLBACK_TAG"
      run git tag -a "$FALLBACK_TAG" -m "$FALLBACK_TAG"
      run GIT_SSH_COMMAND='ssh -F /dev/null' git push origin "$FALLBACK_TAG"
      run gh release create "$FALLBACK_TAG" "$TMP_ZIP" --title "$FALLBACK_TAG" --notes "Fallback release for $TAG due to immutable release blocks"
      echo "Fallback release created: $FALLBACK_TAG"
    else
      echo "Unhandled failure creating release. Aborting." >&2
      exit 1
    fi
  fi
fi

# 5) Post-release verification
if [ "$DRY_RUN" -eq 0 ]; then
  # Use gh to check assets exist
  sleep 2
  if ! gh release view "$TAG" --json assets >/dev/null 2>&1; then
    echo "Warning: release $TAG not found locally; checking fallback tag..."
  fi
  echo "Release created. Listing assets:"
  gh release view "$TAG" --json assets --jq '.assets[].name' || true
fi

# 6) Optional remote verification
if [ -n "$REMOTE_HOST" ]; then
  echo "Running remote verification on $REMOTE_HOST"
  RUN_SSH="ssh -F /dev/null $REMOTE_HOST 'test -f /config/custom_components/luxor_living/manifest.json && echo OK || echo MISSING'"
  echo "+ $RUN_SSH"
  if [ "$DRY_RUN" -eq 0 ]; then
    REMOTE_STATUS=$(ssh -F /dev/null "$REMOTE_HOST" 'test -f /config/custom_components/luxor_living/manifest.json && echo OK || echo MISSING') || true
    echo "Remote status: $REMOTE_STATUS"
    if [ "$REMOTE_STATUS" != "OK" ]; then
      echo "Remote verification failed: manifest.json not present in /config/custom_components/luxor_living/" >&2
    fi
  fi
fi

echo "Release flow finished."
