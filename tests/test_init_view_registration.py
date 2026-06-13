"""Tests for one-time health/push view registration in async_setup_entry."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.luxor_living import async_setup_entry
from custom_components.luxor_living.const import DOMAIN
from custom_components.luxor_living.health_view import LuxorLivingHealthView


def _make_hass():
    hass = MagicMock()
    hass.data = {}
    hass.http.register_view = MagicMock()
    hass.config.path = MagicMock(return_value="/config")
    hass.async_add_executor_job = AsyncMock(return_value={})
    return hass


def _make_entry():
    entry = MagicMock()
    entry.entry_id = "entry_view"
    # No CONF_LXP_FILE → async_setup_entry returns False right after view
    # registration, so we exercise only the registration guard.
    entry.data = {}
    entry.options = {}
    return entry


@pytest.mark.asyncio
async def test_health_view_registered_only_once_across_setups():
    """Calling setup twice must register the health view exactly once."""
    hass = _make_hass()

    await async_setup_entry(hass, _make_entry())
    await async_setup_entry(hass, _make_entry())

    health_registrations = [
        c
        for c in hass.http.register_view.call_args_list
        if isinstance(c.args[0], LuxorLivingHealthView)
    ]
    assert len(health_registrations) == 1
    assert hass.data[DOMAIN]["_health_registered"] is True
