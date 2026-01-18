import pytest
from unittest.mock import MagicMock
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.diagnostics import async_get_config_entry_diagnostics
from custom_components.luxor_living.const import DOMAIN, DATA_KNX_GATEWAY


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
