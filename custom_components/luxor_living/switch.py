"""Switch platform for LUXORliving integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving switches from a config entry."""
    _LOGGER.info("Setting up LUXORliving switches")
    
    # Get mapper from integration data
    from homeassistant.const import Platform
    mapper = hass.data[DOMAIN][entry.entry_id].get("mapper")
    
    if not mapper:
        _LOGGER.warning("No mapper found, skipping switch setup")
        return
    
    # Get all switch entities
    switch_entities = mapper.get_entities_by_platform(Platform.SWITCH)
    _LOGGER.info("Creating %d switch entities", len(switch_entities))
    
    entities = []
    for mapped_entity in switch_entities:
        entity = LuxorLivingSwitch(mapped_entity)
        entities.append(entity)
    
    async_add_entities(entities)


class LuxorLivingSwitch(SwitchEntity):
    """Representation of a LUXORliving switch."""

    _attr_has_entity_name = True

    def __init__(self, mapped_entity: Any) -> None:
        """Initialize the switch."""
        self._mapped = mapped_entity
        self._attr_unique_id = mapped_entity.unique_id
        self._attr_name = mapped_entity.name
        self._attr_is_on = False
        
        # Store datapoint addresses
        self._address_on = (
            mapped_entity.datapoints.get("OnOff")
            or mapped_entity.datapoints.get("SchaltenOnOff")
        )
        self._address_status = mapped_entity.datapoints.get("status@OnOff")
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mapped_entity.device_id)},
            "name": mapped_entity.device_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (simulation mode)."""
        _LOGGER.warning(
            "🔥 SIMULATION: Would send ON to KNX address %s for %s", 
            self._address_on, self._attr_name
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (simulation mode)."""
        _LOGGER.warning(
            "🔥 SIMULATION: Would send OFF to KNX address %s for %s",
            self._address_on, self._attr_name
        )
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        return {
            "knx_address_on": self._address_on,
            "knx_address_status": self._address_status,
        }
