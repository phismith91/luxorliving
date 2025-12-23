"""Switch platform for LUXORliving integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from xknx.telegram.address import GroupAddress

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
        self._address_status = mapped_entity.datapoints.get("status@OnOff") or mapped_entity.datapoints.get("StatusOnOff")
        
        # Debug: Log extracted addresses
        _LOGGER.debug(
            "🔧 Switch '%s' addresses: ON=%s, STATUS=%s",
            self._attr_name,
            f"{self._address_on} ({GroupAddress(self._address_on)})" if self._address_on else "None",
            f"{self._address_status} ({GroupAddress(self._address_status)})" if self._address_status else "None"
        )
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mapped_entity.device_id)},
            "name": mapped_entity.device_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }
        
        # Register listeners for BOTH status AND control addresses
        # GroupValueResponse can come on either address!
        # STATUS address: for state updates from other devices
        # CONTROL address: for GroupValueResponse to our GroupValueRead
        self._listen_addresses = []
        
        if self._address_status:
            self._knx_gateway.register_listener(
                self._address_status,
                self._handle_knx_update
            )
            self._listen_addresses.append(self._address_status)
        
        if self._address_on and self._address_on != self._address_status:
            self._knx_gateway.register_listener(
                self._address_on,
                self._handle_knx_update
            )
            self._listen_addresses.append(self._address_on)

    async def async_added_to_hass(self) -> None:
        """Entity added to hass - request current state from KNX."""
        await super().async_added_to_hass()
        
        # Wait for KNX connection to be ready (max 5 seconds)
        if not self._knx_gateway._connected:
            _LOGGER.debug("⏳ Waiting for KNX connection for switch '%s'...", self._attr_name)
            for i in range(50):
                if self._knx_gateway._connected:
                    _LOGGER.debug("✅ KNX connected after %.1fs for '%s'", i * 0.1, self._attr_name)
                    break
                await asyncio.sleep(0.1)
            
            if not self._knx_gateway._connected:
                _LOGGER.error("KNX not connected after 5s for switch '%s', skipping initial read!", self._attr_name)
                return
        # Request current state from KNX bus via GroupValueRead
        # Read BOTH addresses to work around stale BAOS StatusOnOff values
        # StatusOnOff may be stale if light was ON at BAOS startup or switched manually
        # OnOff reflects actual actuator state more reliably
        addresses_to_read = []
        
        if self._address_status:
            addresses_to_read.append((self._address_status, "STATUS"))
        if self._address_on and self._address_on != self._address_status:
            addresses_to_read.append((self._address_on, "CONTROL"))
        
        if addresses_to_read:
            _LOGGER.info(
                "📖 Switch '%s' requesting initial state from %d address(es): %s",
                self._attr_name,
                len(addresses_to_read),
                ", ".join([f"{GroupAddress(addr)} ({typ})" for addr, typ in addresses_to_read])
            )
            for address, address_type in addresses_to_read:
                await self._knx_gateway.async_read_group_address(address, is_initial=True)
        else:
            _LOGGER.warning(
                "⚠️ Switch '%s' has NO read address! Cannot request initial state.",
                self._attr_name
            )

    def _handle_knx_update(self, group_address: str, value: Any) -> None:
        """Handle KNX status update."""
        # Accept updates from both status and control addresses
        # Convert integer addresses to strings for comparison
        valid_addresses = []
        if self._address_on is not None:
            valid_addresses.append(str(GroupAddress(self._address_on)))
        if self._address_status is not None:
            valid_addresses.append(str(GroupAddress(self._address_status)))
        
        if group_address in valid_addresses:
            self._attr_is_on = bool(value)
            self.schedule_update_ha_state()
            _LOGGER.debug("Updated %s state: %s (from %s)", self._attr_name, value, group_address)

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
        if hasattr(self, '_listen_addresses') and self._listen_addresses:
            for addr in list(self._listen_addresses):
                self._knx_gateway.unregister_listener(
                    addr,
                    self._handle_knx_update
                )
        await super().async_will_remove_from_hass()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        attrs = {}
        
        # Convert integer KNX addresses to group address strings
        if self._address_on is not None:
            attrs["knx_address_on"] = str(GroupAddress(self._address_on))
        
        if self._address_status is not None:
            attrs["knx_address_status"] = str(GroupAddress(self._address_status))
        
        return attrs
