#!/usr/bin/env python3
"""Grep recent HA core release notes for keywords relevant to this integration.

Covers KNX/xknx, TLS, device registry, config entry, deprecations. Run
monthly by .github/workflows/ha-release-check.yml. No AI, no API key —
keyword match only; a human still reads the matched lines and decides.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request

# ponytail: flat keyword list, no config file — edit here when it drifts
KEYWORDS = [
    "knx",
    "xknx",
    "ssl",
    "tls",
    "cipher",
    "via_device",
    "device registry",
    "config entry",
    "config_entry",
    "deprecat",
    "breaking change",
]
RELEASES_URL = "https://api.github.com/repos/home-assistant/core/releases?per_page=20"


def fetch_releases() -> list[dict]:
    req = urllib.request.Request(RELEASES_URL, headers={"User-Agent": "luxorliving-release-check"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def defuse_mentions(line: str) -> str:
    """Break GitHub @mention autolinking so copied lines don't ping HA core devs.

    HA's release notes attribute changes as `([@farmio] - [#178598])`; copied
    verbatim into one of our issues, GitHub still notifies @farmio even though
    the `[...]` reference link is dangling here (#214).
    """
    return re.sub(r"@(?=\w)", "@​", line)


def matching_lines(body: str) -> list[str]:
    pattern = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.IGNORECASE)
    lines = (line.strip() for line in body.splitlines())
    return [defuse_mentions(line.lstrip("- ")) for line in lines if line and pattern.search(line)]


def main() -> int:
    # skip pre-releases (beta/rc) — only stable monthly + patch releases matter here
    releases = [r for r in fetch_releases() if not r.get("prerelease")]
    report: list[str] = []
    for rel in releases:
        hits = matching_lines(rel.get("body") or "")
        if hits:
            report.append(
                f"### {rel['tag_name']} — {rel['html_url']}\n" + "\n".join(f"- {h}" for h in hits)
            )

    if not report:
        print("No keyword matches in the last 10 HA core releases.")
        return 0

    body = "\n\n".join(report)
    print(body)
    # emit for the workflow step to pick up as the issue body
    with open("ha_release_check_report.md", "w") as f:
        f.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
