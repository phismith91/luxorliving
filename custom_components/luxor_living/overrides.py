"""Overrides loader for LUXORliving.

Allows defining sensors that are not exported as 'affected=1' or lack roles
in the LXP, by providing a YAML/JSON file with role→address mapping.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

_LOGGER = logging.getLogger(__name__)


DEFAULT_FILENAMES = [
    "luxor_living_overrides.yaml",
    "luxor_living_overrides.json",
]


def load_overrides(base_path: Path) -> dict[str, Any]:
    """Load overrides from YAML/JSON located at Home Assistant config path.

    Args:
        base_path: Home Assistant config directory (hass.config.path(""))

    Returns:
        dict overrides with keys like 'sensors': [...]. Empty dict if none.
    """
    for fname in DEFAULT_FILENAMES:
        fpath = base_path / fname
        if not fpath.exists():
            continue

        try:
            if fpath.suffix.lower() == ".json":
                with fpath.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    _LOGGER.info("Loaded overrides from %s", fpath)
                    return data if isinstance(data, dict) else {}
            else:
                if yaml is None:
                    _LOGGER.warning(
                        "PyYAML not installed; cannot read %s. Install 'PyYAML' or use JSON.",
                        fpath,
                    )
                    continue
                with fpath.open("r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
                    _LOGGER.info("Loaded overrides from %s", fpath)
                    return data if isinstance(data, dict) else {}
        except Exception as err:
            _LOGGER.error("Failed to load overrides %s: %s", fpath, err)

    return {}
