import pytest
from unittest.mock import MagicMock
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.luxor_living.diagnostics import async_get_config_entry_diagnostics
from custom_components.luxor_living.const import DOMAIN


@pytest.mark.asyncio
async def test_diagnostics_consent_disabled(mock_config_entry):
    hass = MagicMock(spec=HomeAssistant)
    # Ensure options explicitly disable diagnostics
    mock_config_entry.options = {}
    hass.data = {DOMAIN: {mock_config_entry.entry_id: {}}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diag["diagnostics_allowed"] is False
    assert "entities" not in diag
    assert "knx_gateway" not in diag


@pytest.mark.asyncio
async def test_diagnostics_consent_enabled(mock_config_entry, mock_hass_data):
    hass = MagicMock(spec=HomeAssistant)
    # Enable diagnostics explicitly
    mock_config_entry.options = {"allow_diagnostics": True}
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_hass_data}}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diag["diagnostics_allowed"] is not False
    assert "entities" in diag
    assert "knx_gateway" in diag
