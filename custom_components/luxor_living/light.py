"""Light platform for LUXORliving integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DATA_KNX_GATEWAY
from .entity_mapper import EntityMapper
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving lights from a config entry."""
    _LOGGER.info("Setting up LUXORliving lights")
    
    # Get mapper and KNX gateway from integration data
    mapper: EntityMapper = hass.data[DOMAIN][entry.entry_id].get("mapper")
    knx_gateway: LuxorKNXGateway = hass.data[DOMAIN][entry.entry_id].get(DATA_KNX_GATEWAY)
    
    if not mapper:
        _LOGGER.warning("No mapper found, skipping light setup")
        return
    
    if not knx_gateway:
        _LOGGER.error("No KNX gateway found, skipping light setup")
        return
    
    # Get all light entities
    light_entities = mapper.get_entities_by_platform(Platform.LIGHT)
    _LOGGER.info("Creating %d light entities", len(light_entities))
    
    entities: list[LightEntity] = []
    for mapped_entity in light_entities:
        entity: LightEntity
        if mapped_entity.entity_type == "dimmable_light":
            entity = LuxorLivingDimmableLight(mapped_entity, knx_gateway)
        else:
            entity = LuxorLivingLight(mapped_entity, knx_gateway)
        entities.append(entity)
    
    async_add_entities(entities)


class LuxorLivingLight(LightEntity):
    """Representation of a LUXORliving light."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, mapped_entity: Any, knx_gateway: LuxorKNXGateway) -> None:
        """Initialize the light."""
        self._mapped = mapped_entity
        self._knx_gateway = knx_gateway
        self._attr_unique_id = mapped_entity.unique_id
        self._attr_name = mapped_entity.name
        self._attr_is_on = False
        
        # Store datapoint addresses
        self._address_on = mapped_entity.datapoints.get("OnOff") or mapped_entity.datapoints.get("SchaltenOnOff")
        self._address_status = mapped_entity.datapoints.get("StatusOnOff") or mapped_entity.datapoints.get("status@OnOff")
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mapped_entity.device_id)},
            "name": mapped_entity.device_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }
        
        # Register listener for status updates
        # Listen on status address if available, otherwise on control address
        listen_address = self._address_status or self._address_on
        if listen_address:
            self._knx_gateway.register_listener(
                listen_address,
                self._handle_knx_update
            )
            self._listen_address = listen_address  # Store for cleanup

    async def async_added_to_hass(self) -> None:
        """Entity added to hass - request current state from KNX."""
        await super().async_added_to_hass()
        
        # Request current state from KNX bus
        # Try status address first, fallback to control address
        read_address = self._address_status or self._address_on
        if read_address:
            _LOGGER.debug("Requesting initial state for %s from %s", self._attr_name, read_address)
            await self._knx_gateway.async_read_group_address(read_address, is_initial=True)

    def _handle_knx_update(self, group_address: str, value: Any) -> None:
        """Handle KNX status update."""
        # Accept updates from both status and control addresses
        if group_address in (self._address_status, self._address_on):
            self._attr_is_on = bool(value)
            self.schedule_update_ha_state()
            _LOGGER.debug("Updated %s state: %s", self._attr_name, value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
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
        """Turn the light off."""
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
        if hasattr(self, '_listen_address'):
            self._knx_gateway.unregister_listener(
                self._listen_address,
                self._handle_knx_update
            )
        await super().async_will_remove_from_hass()


class LuxorLivingDimmableLight(LuxorLivingLight):
    """Representation of a dimmable LUXORliving light."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, mapped_entity: Any, knx_gateway: LuxorKNXGateway) -> None:
        """Initialize the dimmable light."""
        super().__init__(mapped_entity, knx_gateway)
        self._attr_brightness = 255
        
        # Additional datapoints for dimming
        self._address_dim = mapped_entity.datapoints.get("Dimmen%")
        self._address_dim_rel = mapped_entity.datapoints.get("DimmenRel")
        
        # Register listener for brightness status
        if self._address_dim:
            self._knx_gateway.register_listener(
                self._address_dim,
                self._handle_brightness_update
            )

    async def async_added_to_hass(self) -> None:
        """Entity added to hass - request current state from KNX."""
        await super().async_added_to_hass()
        
        # Request current brightness from KNX bus
        if self._address_dim:
            _LOGGER.debug("Requesting initial brightness for %s from %s", self._attr_name, self._address_dim)
            await self._knx_gateway.async_read_group_address(self._address_dim, is_initial=True)

    def _handle_brightness_update(self, group_address: str, value: Any) -> None:
        """Handle KNX brightness update."""
        if group_address == self._address_dim:
            # Convert percentage (0-100) to brightness (0-255)
            if isinstance(value, (int, float)):
                self._attr_brightness = int(value * 255 / 100)
                self._attr_is_on = self._attr_brightness > 0
                self.schedule_update_ha_state()
                _LOGGER.debug(
                    "Updated %s brightness: %d%%",
                    self._attr_name,
                    value
                )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        
        # Send brightness value if dimming address exists
        if self._address_dim:
            # Convert brightness (0-255) to percentage (0-100)
            percent = int(brightness * 100 / 255)
            success = await self._knx_gateway.async_send_telegram(
                self._address_dim,
                percent,
                "percent"
            )
            if success:
                self._attr_is_on = True
                self._attr_brightness = brightness
                self.async_write_ha_state()
        else:
            # Fallback to simple on/off
            await super().async_turn_on(**kwargs)

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners when entity is removed."""
        if self._address_dim:
            self._knx_gateway.unregister_listener(
                self._address_dim,
                self._handle_brightness_update
            )
        await super().async_will_remove_from_hass()
