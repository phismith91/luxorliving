from unittest.mock import MagicMock

import pytest

from custom_components.luxor_living.const import DATA_KNX_GATEWAY, DOMAIN
from custom_components.luxor_living.diagnostics import async_get_config_entry_diagnostics


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_diagnostics_consent_flow(mock_config_entry):
    """E2E-style test: user enables diagnostics via options and diagnostics are returned."""
    hass = MagicMock()

    # Start with diagnostics disabled
    object.__setattr__(mock_config_entry, "options", {})
    hass.data = {DOMAIN: {mock_config_entry.entry_id: {}}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    assert diag["diagnostics_allowed"] is False

    # Simulate user enabling diagnostics via options (e.g., OptionsFlow -> apply)
    object.__setattr__(mock_config_entry, "options", {"allow_diagnostics": True})

    # Provide minimal runtime data (gateway + mapper + coordinator)
    mock_gateway = MagicMock()
    mock_gateway._connected = True
    mock_gateway._datapoint_mapping = {"1/1/1": "OnOff"}

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
    assert diag["diagnostics_allowed"] is True
    assert "entities" in diag
    assert "knx_gateway" in diag
