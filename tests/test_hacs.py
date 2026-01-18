import json


def test_hacs_json_exists():
    with open("hacs.json") as f:
        h = json.load(f)
    assert "name" in h
    assert h.get("filename", "").endswith(".zip")


def test_manifest_fields():
    with open("custom_components/luxor_living/manifest.json") as f:
        m = json.load(f)
    for k in ("domain", "name", "documentation", "issue_tracker", "version"):
        assert k in m
