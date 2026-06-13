"""Tests for async_setup_entry retry behaviour (ConfigEntryNotReady)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.luxor_living import async_setup_entry
from custom_components.luxor_living.const import (
    CONF_CONNECTION_TYPE,
    CONF_LXP_FILE,
    CONF_SIMULATION_MODE,
)


def _make_hass():
    hass = MagicMock()
    hass.data = {}
    hass.http.register_view = MagicMock()
    hass.config.path = MagicMock(return_value="/config")
    hass.async_add_executor_job = AsyncMock(return_value={})
    return hass


def _make_entry(simulation_mode=False):
    entry = MagicMock()
    entry.entry_id = "entry_retry"
    entry.data = {
        CONF_LXP_FILE: "/config/test.lxp",
        CONF_HOST: "192.168.1.3",
        CONF_CONNECTION_TYPE: "tunneling",
        CONF_SIMULATION_MODE: simulation_mode,
    }
    entry.options = {}
    entry.runtime_data = None
    return entry


@pytest.mark.asyncio
async def test_gateway_unreachable_raises_config_entry_not_ready():
    """Non-simulation gateway failure must raise ConfigEntryNotReady (HA retries)."""
    hass = _make_hass()
    entry = _make_entry(simulation_mode=False)

    gateway = MagicMock()
    gateway.async_setup = AsyncMock(return_value=False)

    with (
        patch("custom_components.luxor_living.Path") as mock_path,
        patch(
            "custom_components.luxor_living.LXPParser.parse_cached",
            new=AsyncMock(return_value=MagicMock()),
        ),
        patch("custom_components.luxor_living.EntityMapper") as mock_mapper,
        patch("custom_components.luxor_living.LuxorKNXGateway", return_value=gateway),
    ):
        mock_path.return_value.expanduser.return_value.exists.return_value = True
        mock_mapper.return_value.entities = []

        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)
