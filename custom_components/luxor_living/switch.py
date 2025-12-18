"""Switch platform for LUXORliving integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DATA_KNX_GATEWAY
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving switches from a config entry."""
    _LOGGER.info("Setting up LUXORliving switches")
    
    # Get mapper and KNX gateway from integration data
    from homeassistant.const import Platform
    mapper = hass.data[DOMAIN][entry.entry_id].get("mapper")
    knx_gateway: LuxorKNXGateway = hass.data[DOMAIN][entry.entry_id].get(DATA_KNX_GATEWAY)
    
    if not mapper:
        _LOGGER.warning("No mapper found, skipping switch setup")
        return
    
    if not knx_gateway:
        _LOGGER.error("No KNX gateway found, skipping switch setup")
        return
    
    # Get all switch entities
    switch_entities = mapper.get_entities_by_platform(Platform.SWITCH)
    _LOGGER.info("Creating %d switch entities", len(switch_entities))
    
    entities = []
    for mapped_entity in switch_entities:
        entity = LuxorLivingSwitch(mapped_entity, knx_gateway)
        entities.append(entity)
    
    async_add_entities(entities)


class LuxorLivingSwitch(SwitchEntity):
    """Representation of a LUXORliving switch."""

    _attr_has_entity_name = True

    def __init__(self, mapped_entity: Any, knx_gateway: LuxorKNXGateway) -> None:
        """Initialize the switch."""
        self._mapped = mapped_entity
        self._knx_gateway = knx_gateway
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
        
        # Register listener for status updates
        if self._address_status:
            self._knx_gateway.register_listener(
                self._address_status,
                self._handle_knx_update
            )

    async def async_added_to_hass(self) -> None:
        """Entity added to hass - request current state from KNX."""
        await super().async_added_to_hass()
        
        # Request current state from KNX bus
        if self._address_status:
            _LOGGER.debug("Requesting initial state for %s from %s", self._attr_name, self._address_status)
            await self._knx_gateway.async_read_group_address(self._address_status)

    def _handle_knx_update(self, group_address: str, value: Any) -> None:
        """Handle KNX status update."""
        if group_address == self._address_status:
            self._attr_is_on = bool(value)
            self.schedule_update_ha_state()
            _LOGGER.debug("Updated %s state: %s", self._attr_name, value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if self._address_on:
            success = await self._knx_gateway.async_send_telegram(
                self._address_on,
                True,
                "binary"
            )
            if success:
                self._attr_is_on = True
                self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        if self._address_on:
            success = await self._knx_gateway.async_send_telegram(
                self._address_on,
                False,
                "binary"
            )
            if success:
                self._attr_is_on = False
                self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listener when entity is removed."""
        if self._address_status:
            self._knx_gateway.unregister_listener(
                self._address_status,
                self._handle_knx_update
            )
        await super().async_will_remove_from_hass()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        return {
            "knx_address_on": self._address_on,
            "knx_address_status": self._address_status,
        }
