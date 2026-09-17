"""Regression test for #214: bot must not ping unrelated HA core devs."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_ha_release_notes",
    Path(__file__).parent.parent / ".github" / "scripts" / "check_ha_release_notes.py",
)
check_ha_release_notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_ha_release_notes)


def test_matching_lines_defuses_mentions():
    body = "- Update xknx to 3.19.0 ([@farmio] - [#178652]) ([knx docs])"
    (result,) = check_ha_release_notes.matching_lines(body)
    assert "@farmio" not in result
    assert "@​farmio" in result


def test_matching_lines_skips_non_keyword_lines():
    body = "- Bump some unrelated dependency ([@someone] - [#1])"
    assert check_ha_release_notes.matching_lines(body) == []
