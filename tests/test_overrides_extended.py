"""Extended tests for overrides.py covering all branches."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from custom_components.luxor_living.overrides import load_overrides


class TestLoadOverrides:
    def test_returns_empty_dict_when_no_file_exists(self, tmp_path):
        result = load_overrides(tmp_path)
        assert result == {}

    def test_loads_json_file(self, tmp_path):
        data = {"sensors": [{"name": "Test", "address": "1/0/0"}]}
        (tmp_path / "luxor_living_overrides.json").write_text(json.dumps(data))
        result = load_overrides(tmp_path)
        assert result == data

    def test_json_non_dict_returns_empty(self, tmp_path):
        (tmp_path / "luxor_living_overrides.json").write_text(json.dumps([1, 2, 3]))
        result = load_overrides(tmp_path)
        assert result == {}

    def test_loads_yaml_file(self, tmp_path):
        yaml_content = "sensors:\n  - name: Test\n    address: '1/0/0'\n"
        (tmp_path / "luxor_living_overrides.yaml").write_text(yaml_content)
        result = load_overrides(tmp_path)
        assert "sensors" in result

    def test_yaml_non_dict_returns_empty(self, tmp_path):
        (tmp_path / "luxor_living_overrides.yaml").write_text("- item1\n- item2\n")
        result = load_overrides(tmp_path)
        assert result == {}

    def test_prefers_yaml_over_json(self, tmp_path):
        json_data = {"source": "json"}
        (tmp_path / "luxor_living_overrides.yaml").write_text("source: yaml\n")
        (tmp_path / "luxor_living_overrides.json").write_text(json.dumps(json_data))
        result = load_overrides(tmp_path)
        # YAML is listed first in DEFAULT_FILENAMES
        assert result.get("source") == "yaml"

    def test_json_loaded_when_yaml_missing(self, tmp_path):
        data = {"key": "value"}
        (tmp_path / "luxor_living_overrides.json").write_text(json.dumps(data))
        result = load_overrides(tmp_path)
        assert result == data

    def test_invalid_json_returns_empty(self, tmp_path):
        (tmp_path / "luxor_living_overrides.json").write_text("{invalid json")
        result = load_overrides(tmp_path)
        assert result == {}

    def test_invalid_yaml_returns_empty(self, tmp_path):
        (tmp_path / "luxor_living_overrides.yaml").write_text(":\t invalid: yaml")
        result = load_overrides(tmp_path)
        assert result == {}

    def test_yaml_none_module_skips_and_returns_empty(self, tmp_path):
        """When yaml module is None, YAML files are skipped."""
        (tmp_path / "luxor_living_overrides.yaml").write_text("key: value\n")
        with patch("custom_components.luxor_living.overrides.yaml", None):
            result = load_overrides(tmp_path)
        assert result == {}

    def test_empty_base_path_no_crash(self, tmp_path):
        # No files at all → should return {} cleanly
        result = load_overrides(tmp_path / "nonexistent_subdir")
        assert result == {}
