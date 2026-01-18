import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.luxor_living.config_flow import LuxorLivingOptionsFlow
from custom_components.luxor_living.const import CONF_ALLOW_DIAGNOSTICS


@pytest.mark.asyncio
async def test_options_flow_contains_allow_diagnostics(mock_config_entry):
    flow = LuxorLivingOptionsFlow()
    # Attach a mock hass and config entry to emulate runtime
    flow.hass = MagicMock()
    # Emulate Home Assistant linking: handler == config_entry.entry_id
    flow.handler = mock_config_entry.entry_id
    # Ensure hass.config_entries.async_get_known_entry returns the config entry
    flow.hass.config_entries = MagicMock(async_get_known_entry=MagicMock(return_value=mock_config_entry))

    # Show options form
    result = await flow.async_step_init()

    assert result["type"] == "form"
    schema = result["data_schema"].schema
    assert CONF_ALLOW_DIAGNOSTICS in schema


@pytest.mark.asyncio
async def test_options_flow_update_allow_diagnostics(mock_config_entry):
    flow = LuxorLivingOptionsFlow()
    flow.hass = MagicMock()
    # Attach into instance dict
    flow.__dict__["config_entry"] = mock_config_entry

    # Enable diagnostics via options flow
    result = await flow.async_step_init({CONF_ALLOW_DIAGNOSTICS: True})

    assert result["type"] == "create_entry"
    assert result["data"][CONF_ALLOW_DIAGNOSTICS] is True
