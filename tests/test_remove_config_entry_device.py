"""Tests for async_remove_config_entry_device (Gold: stale-device handling)."""

from unittest.mock import MagicMock

import pytest
from homeassistant.const import Platform

from custom_components.luxor_living import async_remove_config_entry_device
from custom_components.luxor_living.const import DOMAIN
from custom_components.luxor_living.integration_state import IntegrationState
from custom_components.luxor_living.mapped_entity import MappedEntity


def _entry_with_device_ids(device_ids):
    """Build a config entry whose runtime mapper reports the given device ids."""
    mapper = MagicMock()
    mapper.entities = [
        MappedEntity(
            platform=Platform.LIGHT,
            unique_id=f"uid_{i}",
            name="Entity",
            device_name="Device",
            device_id=did,
            entity_type="light",
            datapoints={},
            attributes={},
            parameters={},
        )
        for i, did in enumerate(device_ids)
    ]
    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.runtime_data = IntegrationState(mapper=mapper, config={}, overrides={})
    return entry


def _device(*identifiers):
    device = MagicMock()
    device.identifiers = set(identifiers)
    return device


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_stale_device_is_removable():
    """A device no longer produced by the integration may be removed."""
    entry = _entry_with_device_ids(["devA"])
    device = _device((DOMAIN, "devB"))
    assert await async_remove_config_entry_device(MagicMock(), entry, device) is True


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_active_device_is_not_removable():
    """A device still mapped by the integration may not be removed."""
    entry = _entry_with_device_ids(["devA", "devB"])
    device = _device((DOMAIN, "devA"))
    assert await async_remove_config_entry_device(MagicMock(), entry, device) is False


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_hub_device_is_not_removable():
    """The gateway hub device (identifier == entry_id) may not be removed."""
    entry = _entry_with_device_ids(["devA"])
    device = _device((DOMAIN, "entry1"))
    assert await async_remove_config_entry_device(MagicMock(), entry, device) is False


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_missing_runtime_data_allows_removal():
    """Without runtime data (entry already torn down) stale devices are removable."""
    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.runtime_data = None
    device = _device((DOMAIN, "devA"))
    assert await async_remove_config_entry_device(MagicMock(), entry, device) is True


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_foreign_identifier_is_removable():
    """A device with no matching DOMAIN identifier is removable."""
    entry = _entry_with_device_ids(["devA"])
    device = _device(("other_domain", "devA"))
    assert await async_remove_config_entry_device(MagicMock(), entry, device) is True
