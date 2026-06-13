import json
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.luxor_living.const import DATA_KNX_GATEWAY, DOMAIN
from custom_components.luxor_living.diagnostics import async_get_config_entry_diagnostics


def _make_state(gateway=None, mapper=None, coordinator=None, overrides=None):
    """Build a minimal IntegrationState-like mock for runtime_data."""
    state = MagicMock()
    state.knx_gateway = gateway
    state.mapper = mapper or MagicMock(entities=[])
    state.coordinator = coordinator
    state.overrides = overrides or {}
    return state


@pytest.mark.asyncio
async def test_diagnostics_consent_disabled(mock_config_entry):
    hass = MagicMock(spec=HomeAssistant)
    # Ensure options explicitly disable diagnostics
    object.__setattr__(mock_config_entry, "options", {})
    hass.data = {DOMAIN: {mock_config_entry.entry_id: {}}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diag["diagnostics_allowed"] is False
    assert "entities" not in diag
    assert "knx_gateway" not in diag


@pytest.mark.asyncio
async def test_diagnostics_consent_enabled(mock_config_entry):
    hass = MagicMock(spec=HomeAssistant)
    # Enable diagnostics explicitly
    object.__setattr__(mock_config_entry, "options", {"allow_diagnostics": True})

    # Minimal hass data to exercise diagnostics
    mock_gateway = MagicMock()
    mock_gateway._connected = True
    mock_gateway._tunneling_enabled = False
    mock_gateway.simulation_mode = False
    mock_gateway.host = "192.168.1.100"
    mock_gateway._datapoint_mapping = {"1/2/3": "OnOff"}

    mock_mapper = MagicMock()
    mock_mapper.entities = []

    mock_coordinator = MagicMock()
    mock_coordinator.last_update_success = True
    mock_coordinator.last_exception = None
    mock_coordinator.update_interval = MagicMock()
    mock_coordinator.update_interval.total_seconds = MagicMock(return_value=30.0)
    mock_coordinator._scan_interval = 30

    hass.data = {
        DOMAIN: {
            mock_config_entry.entry_id: {
                "mapper": mock_mapper,
                DATA_KNX_GATEWAY: mock_gateway,
                "coordinator": mock_coordinator,
            }
        }
    }

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diag["diagnostics_allowed"] is not False
    assert "entities" in diag
    assert "knx_gateway" in diag


# ── Token-redaction tests ─────────────────────────────────────────────────────


def _entry(**options):
    """Create a MockConfigEntry with given options for diagnostics tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="diag_test_entry",
        title="Diag Test",
        data={},
        options=options,
        version=1,
    )


@pytest.mark.asyncio
async def test_minimal_payload_redacts_push_token():
    """push_token must not appear in minimal (no-consent) diagnostics payload."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    entry = _entry(
        allow_diagnostics=False, push_token="secret-abc123", push_ws_token="wssecret-xyz"
    )

    diag = await async_get_config_entry_diagnostics(hass, entry)

    payload = json.dumps(diag)
    assert "secret-abc123" not in payload
    assert "wssecret-xyz" not in payload


@pytest.mark.asyncio
async def test_full_payload_redacts_push_token():
    """push_token must not appear in full (consent-enabled) diagnostics payload."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    entry = _entry(allow_diagnostics=True, push_token="secret-abc123", push_ws_token="wssecret-xyz")

    diag = await async_get_config_entry_diagnostics(hass, entry)

    payload = json.dumps(diag)
    assert "secret-abc123" not in payload
    assert "wssecret-xyz" not in payload


# ── runtime_data tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_diagnostics_reads_gateway_from_runtime_data():
    """Gateway info must come from entry.runtime_data, not hass.data."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}  # intentionally empty

    mock_gateway = MagicMock()
    mock_gateway._connected = True
    mock_gateway._tunneling_enabled = True
    mock_gateway.simulation_mode = False
    mock_gateway.host = "10.0.0.1"
    mock_gateway._datapoint_mapping = {}

    entry = _entry(allow_diagnostics=True)
    entry.runtime_data = _make_state(gateway=mock_gateway)

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert "knx_gateway" in diag
    assert diag["knx_gateway"]["host"] == "10.0.0.1"
    assert diag["knx_gateway"]["connected"] is True


@pytest.mark.asyncio
async def test_diagnostics_runtime_data_missing_returns_empty_sections():
    """No runtime_data and no hass.data → diagnostics still returns valid shape."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    entry = _entry(allow_diagnostics=True)
    # entry has no runtime_data attribute

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert diag["diagnostics_allowed"] is True
    assert "knx_gateway" not in diag
