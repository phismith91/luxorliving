"""Light platform for LUXORliving integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from xknx.telegram.address import GroupAddress

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
        
        # Debug: Log extracted addresses
        _LOGGER.debug(
            "💡 Light '%s' addresses: ON=%s, STATUS=%s",
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
            _LOGGER.debug("⏳ Waiting for KNX connection for light '%s'...", self._attr_name)
            for i in range(50):
                if self._knx_gateway._connected:
                    _LOGGER.debug("✅ KNX connected after %.1fs for '%s'", i * 0.1, self._attr_name)
                    break
                await asyncio.sleep(0.1)
            
            if not self._knx_gateway._connected:
                _LOGGER.error("❌ KNX not connected after 5s for light '%s', skipping initial read!", self._attr_name)
                return
        
        # BETA 7.7: Use KNX GroupValueRead for initial state
        # REST API mapping removed (BAOS Datapoints ≠ GroupAddresses)
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
                "💡 Light '%s' requesting initial state from %d address(es): %s",
                self._attr_name,
                len(addresses_to_read),
                ", ".join([f"{GroupAddress(addr)} ({typ})" for addr, typ in addresses_to_read])
            )
            for address, address_type in addresses_to_read:
                await self._knx_gateway.async_read_group_address(address, is_initial=True)
        else:
            _LOGGER.warning(
                "⚠️ Light '%s' has NO read address! Cannot request initial state.",
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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        attrs = {}
        
        # Convert integer KNX addresses to group address strings
        if self._address_on is not None:
            attrs["knx_address_on"] = str(GroupAddress(self._address_on))
        
        if self._address_status is not None:
            attrs["knx_address_status"] = str(GroupAddress(self._address_status))
        
        if self._address_dim is not None:
            attrs["knx_address_dim"] = str(GroupAddress(self._address_dim))
        
        return attrs

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners when entity is removed."""
        if self._address_dim:
            self._knx_gateway.unregister_listener(
                self._address_dim,
                self._handle_brightness_update
            )
        await super().async_will_remove_from_hass()
