#!/usr/bin/env bash
set -euo pipefail

# Automated deploy: commit, push, tag and GitHub release (stable by default)
# Usage:
#   scripts/deploy_release.sh [--version X.Y.Z] [--tag vX.Y.Z-beta.<label>] [--message "msg"] [--notes "text"] [--prerelease] [--stable]
# Examples:
#   scripts/deploy_release.sh --message "release: auto" --notes "Fixes and improvements"
#   scripts/deploy_release.sh --version 0.2.12 --tag v0.2.12-beta.20251223 --message "release: 0.2.12"
#   scripts/deploy_release.sh --prerelease --notes "Beta validation"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI 'gh' not found. Install and authenticate first (gh auth login)." >&2
  exit 1
fi

VERSION_OVERRIDE=""
TAG_OVERRIDE=""
COMMIT_MSG=""
RELEASE_NOTES=""
PRERELEASE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VERSION_OVERRIDE="$2"; shift 2 ;;
    --tag)
      TAG_OVERRIDE="$2"; shift 2 ;;
    --message)
      COMMIT_MSG="$2"; shift 2 ;;
    --notes)
      RELEASE_NOTES="$2"; shift 2 ;;
    --prerelease)
      PRERELEASE=true; shift 1 ;;
    --stable)
      PRERELEASE=false; shift 1 ;;
    --help|-h)
      echo "Usage: $0 [--version X.Y.Z] [--tag vX.Y.Z-beta.<label>] [--message \"msg\"] [--notes \"text\"] [--prerelease] [--stable]";
      exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

# Read version from manifest.json unless overridden
read_version() {
  python3 - "$ROOT_DIR" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
mf = root / 'custom_components' / 'luxor_living' / 'manifest.json'
data = json.loads(mf.read_text())
print(data.get('version',''))
PY
}

VERSION="${VERSION_OVERRIDE:-$(read_version)}"
if [[ -z "$VERSION" ]]; then
  echo "Error: Could not read version from manifest.json and no --version provided." >&2
  exit 3
fi

# Assemble tag (override or default)
DEFAULT_LABEL="beta.$(date +%Y%m%d%H%M)"
TAG="${TAG_OVERRIDE:-v${VERSION}-${DEFAULT_LABEL}}"

# Ensure git is cleanly configured
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REMOTE="origin"

# Stage and commit if there are changes
if ! git diff --quiet || ! git diff --cached --quiet; then
  git add -A
  if [[ -z "$COMMIT_MSG" ]]; then
    COMMIT_MSG="release: ${VERSION} auto-deploy"
  fi
  git commit -m "$COMMIT_MSG"
else
  echo "No changes to commit"
fi

# Push branch
git push "$REMOTE" "$BRANCH"

# Create tag if missing
if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then
  echo "Tag ${TAG} already exists locally"
else
  git tag -a "$TAG" -m "Auto deploy tag for ${VERSION}"
fi

# Push tag
git push "$REMOTE" "$TAG"

TITLE="Release (${VERSION})"

# Resolve release notes: explicit --notes arg → RELEASE_NOTES file → CHANGELOG extract
NOTES_FILE=""
if [[ -n "$RELEASE_NOTES" ]]; then
  NOTES_FILE=$(mktemp /tmp/release_notes_XXXXXX.md)
  echo "$RELEASE_NOTES" > "$NOTES_FILE"
elif [[ -f "docs/releases/RELEASE_NOTES_v${VERSION}.md" ]]; then
  NOTES_FILE="docs/releases/RELEASE_NOTES_v${VERSION}.md"
elif [[ -f "RELEASE_NOTES_v${VERSION}.md" ]]; then
  NOTES_FILE="RELEASE_NOTES_v${VERSION}.md"
else
  # Extract section for this version from CHANGELOG.md
  NOTES_FILE=$(mktemp /tmp/release_notes_XXXXXX.md)
  awk "/^## \[${VERSION}\]/{flag=1; next} /^## \[/{if(flag) exit} flag" CHANGELOG.md > "$NOTES_FILE"
  if [[ ! -s "$NOTES_FILE" ]]; then
    echo "Warning: no CHANGELOG entry found for ${VERSION} — using last commit message" >&2
    git log -1 --pretty=%B > "$NOTES_FILE"
  fi
fi

# Create or update GitHub release
if gh release view "$TAG" >/dev/null 2>&1; then
  echo "Release ${TAG} already exists on GitHub"
  if [[ "$PRERELEASE" == true ]]; then
    gh release edit "$TAG" --prerelease --draft=false
  else
    gh release edit "$TAG" --prerelease=false --draft=false
  fi
else
  if [[ "$PRERELEASE" == true ]]; then
    gh release create "$TAG" --title "$TITLE" --notes-file "$NOTES_FILE" --prerelease
  else
    gh release create "$TAG" --title "$TITLE" --notes-file "$NOTES_FILE"
  fi
fi

# Build ZIP: manifest.json at root (required by HACS with content_in_root: false)
ARTIFACT="luxor_living-${VERSION}.zip"
echo "Packing artifact: ${ARTIFACT}"
rm -f "$ARTIFACT"
pushd "$ROOT_DIR/custom_components/luxor_living" > /dev/null
zip -r "$ROOT_DIR/$ARTIFACT" . -x "*.pyc" "*/__pycache__/*" "*.git*"
popd > /dev/null

# Validate ZIP structure
if ! unzip -l "$ARTIFACT" | awk '{print $4}' | grep -qx "manifest.json"; then
  echo "Error: manifest.json not at ZIP root — HACS install would fail" >&2
  exit 4
fi
echo "ZIP structure valid (manifest.json at root)"

echo "Uploading artifact to release: ${ARTIFACT}"
gh release upload "$TAG" "$ARTIFACT" --clobber

# Print release info
gh release view "$TAG" --json name,tagName,url,isPrerelease,isDraft,assets | cat

echo "✅ Deploy finished: ${TAG}"
