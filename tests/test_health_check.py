#!/usr/bin/env python3
"""Tests for Health Check endpoint."""

import json
from unittest.mock import MagicMock, patch

import pytest

from custom_components.luxor_living import LuxorLivingHealthView
from custom_components.luxor_living.health_view import _get_manifest_version


class TestLuxorLivingHealthView:
    """Test the Health Check endpoint."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant instance."""
        hass = MagicMock()
        hass.data = {
            "luxor_living": {
                "entry_1": {
                    "mapper": MagicMock(),
                    "config": {"discovered_sensors": {"addr1": {}, "addr2": {}}},
                    "overrides": {},
                },
                "_health_registered": True,  # Prevent double registration
            }
        }

        # Mock mapper entities
        hass.data["luxor_living"]["entry_1"]["mapper"].entities = [MagicMock(), MagicMock()]

        # Mock KNX gateway
        mock_gateway = MagicMock()
        mock_gateway.is_connected.return_value = True
        mock_gateway.simulation_mode = False
        mock_gateway._known_addresses = {"1/1/1", "1/1/2"}
        mock_gateway.get_traffic_stats.return_value = {
            "reads_last_minute": 2,
            "writes_last_minute": 1,
        }
        hass.data["luxor_living"]["entry_1"]["knx_gateway"] = mock_gateway

        return hass

    @pytest.fixture
    def health_view(self, mock_hass):
        """Create health view instance."""
        return LuxorLivingHealthView(mock_hass)

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_health_endpoint_success(self, health_view, mock_hass):
        """Test successful health check response."""
        # Mock request
        request = MagicMock()

        # Call health endpoint
        response = await health_view.get(request)

        # Parse JSON response
        import json

        data = json.loads(response.body.decode())

        # Verify structure
        assert "status" in data
        assert "timestamp" in data
        assert "integration" in data
        assert "entries" in data
        assert "system" in data

        # Verify integration info
        assert data["integration"]["name"] == "LUXORliving"
        # Version should match manifest version
        import json as _json

        with open("custom_components/luxor_living/manifest.json") as _f:
            _manifest = _json.load(_f)
        assert data["integration"]["version"] == _manifest["version"]

        # Verify system info
        assert "cache" in data["system"]
        assert "circuit_breakers" in data["system"]

        # Verify circuit breakers
        cb = data["system"]["circuit_breakers"]
        assert "rest_api" in cb
        assert "knx_connection" in cb

        # Verify entries
        assert "entry_1" in data["entries"]
        entry = data["entries"]["entry_1"]
        assert entry["connected"] is True
        assert entry["simulation_mode"] is False
        assert entry["entity_count"] == 2
        assert entry["discovered_sensors"] == 2
        assert entry["known_addresses"] == 2
        assert entry["traffic"]["reads_last_minute"] == 2

    @pytest.mark.asyncio
    async def test_health_endpoint_no_entries(self, mock_hass):
        """Test health check with no config entries."""
        # Clear entries
        mock_hass.data["luxor_living"] = {"_health_registered": True}

        health_view = LuxorLivingHealthView(mock_hass)
        request = MagicMock()

        response = await health_view.get(request)
        import json

        data = json.loads(response.body.decode())

        assert data["status"] == "healthy"
        assert data["entries"] == {}

    @pytest.mark.asyncio
    async def test_health_endpoint_unhealthy(self, health_view, mock_hass):
        """Test health check when gateway is disconnected."""
        # Make gateway disconnected
        mock_gateway = mock_hass.data["luxor_living"]["entry_1"]["knx_gateway"]
        mock_gateway.is_connected.return_value = False
        mock_gateway.simulation_mode = False

        request = MagicMock()
        response = await health_view.get(request)

        import json

        data = json.loads(response.body.decode())

        assert data["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_endpoint_simulation_mode(self, health_view, mock_hass):
        """Test health check in simulation mode."""
        # Make gateway in simulation mode
        mock_gateway = mock_hass.data["luxor_living"]["entry_1"]["knx_gateway"]
        mock_gateway.is_connected.return_value = False
        mock_gateway.simulation_mode = True

        request = MagicMock()
        response = await health_view.get(request)

        import json

        data = json.loads(response.body.decode())

        # Should be healthy even when disconnected in simulation mode
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_endpoint_circuit_breaker_open(self, health_view, mock_hass):
        """Test health check when circuit breaker is open."""
        from custom_components.luxor_living.circuit_breaker import (
            _knx_circuit_breaker,
            _rest_api_circuit_breaker,
        )

        # Mock the circuit breaker instances directly
        with (
            patch.object(
                _rest_api_circuit_breaker,
                "get_stats",
                return_value={
                    "state": "open",
                    "failure_count": 5,
                    "last_failure_time": 1234567890.0,
                },
            ),
            patch.object(
                _knx_circuit_breaker,
                "get_stats",
                return_value={
                    "state": "closed",
                    "failure_count": 0,
                    "last_failure_time": None,
                },
            ),
        ):

            request = MagicMock()
            response = await health_view.get(request)

            import json

            data = json.loads(response.body.decode())

            # Should be degraded when circuit breaker is open
            assert data["status"] == "degraded"


@pytest.mark.smoke
class TestHealthViewMutationTargets:
    """Kill surviving mutants in health_view.py."""

    def test_get_manifest_version_returns_real_version(self):
        """Kill: manifest path mutations that cause fallback to 'unknown'.

        _get_manifest_version() is called at module import time and cached.
        By calling it directly in a smoke test, mutmut can attribute coverage
        to it and kill mutations that cause it to return 'unknown'.
        """
        version = _get_manifest_version()
        assert version != "unknown"
        assert isinstance(version, str)
        assert "." in version  # semver: "1.1.x"

    def test_get_manifest_version_reads_version_key(self):
        """Kill: data.get('version') → data.get('VERSION') / None mutations."""
        version = _get_manifest_version()
        # If 'version' key mutation → None → falls back to 'unknown'
        assert version is not None
        assert version != "XXunknownXX"
        assert version != "UNKNOWN"

    @pytest.mark.asyncio
    async def test_status_value_is_healthy_lowercase(self):
        """Kill: 'status': 'healthy' → 'HEALTHY' mutation."""
        hass = MagicMock()
        hass.data = {"luxor_living": {}}
        view = LuxorLivingHealthView(hass)
        resp = await view.get(MagicMock())
        data = json.loads(resp.body.decode())
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_integration_domain_key_present(self):
        """Kill: 'domain' → 'XXdomainXX' / 'DOMAIN' key mutations."""
        from custom_components.luxor_living.const import DOMAIN

        hass = MagicMock()
        hass.data = {"luxor_living": {}}
        view = LuxorLivingHealthView(hass)
        resp = await view.get(MagicMock())
        data = json.loads(resp.body.decode())
        assert "domain" in data["integration"]
        assert data["integration"]["domain"] == DOMAIN

    @pytest.mark.asyncio
    async def test_integration_name_is_luxorliving(self):
        """Kill: 'LUXORliving' string → mutation (already in existing test but now explicit)."""
        hass = MagicMock()
        hass.data = {"luxor_living": {}}
        view = LuxorLivingHealthView(hass)
        resp = await view.get(MagicMock())
        data = json.loads(resp.body.decode())
        assert data["integration"]["name"] == "LUXORliving"

    @pytest.mark.asyncio
    async def test_domain_data_defaults_to_empty_dict_not_none(self):
        """Kill: hass.data.get(DOMAIN, {}) → default=None mutation."""
        hass = MagicMock()
        hass.data = {}  # No DOMAIN key → should default to {}
        view = LuxorLivingHealthView(hass)
        # Should not raise TypeError even if domain_data is empty
        resp = await view.get(MagicMock())
        data = json.loads(resp.body.decode())
        assert data["status"] == "healthy"
        assert data["entries"] == {}
