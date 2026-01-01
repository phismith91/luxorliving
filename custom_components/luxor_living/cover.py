"""Cover platform for LUXORliving integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DATA_KNX_GATEWAY
from .coordinator import LuxorLivingCoordinator
from .entity_mapper import EntityMapper
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving covers from a config entry."""
    _LOGGER.info("Setting up LUXORliving covers")

    # Get coordinator, mapper and KNX gateway from integration data
    try:
        integration_data = hass.data[DOMAIN][entry.entry_id]
        if not isinstance(integration_data, dict):
            _LOGGER.error("Integration data is not a dictionary: %s", type(integration_data))
            return
        coordinator: LuxorLivingCoordinator = integration_data.get("coordinator")
        mapper: EntityMapper = integration_data.get("mapper")
        knx_gateway: LuxorKNXGateway = integration_data.get(DATA_KNX_GATEWAY)
    except (KeyError, AttributeError) as err:
        _LOGGER.error("Failed to get integration data: %s", err)
        return

    if not mapper:
        _LOGGER.warning("No mapper found, skipping cover setup")
        return

    if not coordinator:
        _LOGGER.error("No coordinator found, skipping cover setup")
        return

    # Get all cover entities from mapper
    cover_entities = mapper.get_entities_by_platform(Platform.COVER)
    _LOGGER.info("Creating %d cover entities", len(cover_entities))

    # Create cover entities asynchronously
    entities = await asyncio.gather(
        *[
            _create_cover_entity(coordinator, entry, mapped_entity, knx_gateway)
            for mapped_entity in cover_entities
        ]
    )

    async_add_entities(entities)


async def _create_cover_entity(
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
    knx_gateway: LuxorKNXGateway,
) -> CoverEntity:
    """Create a cover entity asynchronously."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, lambda: _create_cover_entity_sync(coordinator, entry, mapped_entity, knx_gateway)
    )


def _create_cover_entity_sync(
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
    knx_gateway: LuxorKNXGateway,
) -> LuxorCover:
    """Create a cover entity synchronously."""
    return LuxorCover(
        coordinator=coordinator,
        knx_gateway=knx_gateway,
        mapped_entity=mapped_entity,
        entry_id=entry.entry_id,
    )


class LuxorCover(CoverEntity):
    """Representation of a LUXORliving cover device (J8/J4 shutter/blind actuator)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        knx_gateway: LuxorKNXGateway,
        mapped_entity: Any,
        entry_id: str,
    ) -> None:
        """Initialize the cover entity."""
        self.coordinator = coordinator
        self.knx_gateway = knx_gateway
        self._mapped_entity = mapped_entity
        self._entry_id = entry_id

        # Map datapoint addresses by role
        self._datapoints = {dp["role"]: dp["address"] for dp in mapped_entity.get("datapoints", [])}

        # Set unique ID
        self._attr_unique_id = mapped_entity.get("unique_id")

        # Set name
        self._attr_name = mapped_entity.get("name")

        # Determine if this is a blind (has tilt) or shutter
        dp_roles = {dp["role"] for dp in mapped_entity.get("datapoints", [])}
        has_tilt = "Lamelle%" in dp_roles or "StatusLamelle%" in dp_roles

        # Set device class
        if has_tilt:
            self._attr_device_class = CoverDeviceClass.BLIND
        else:
            self._attr_device_class = CoverDeviceClass.SHUTTER

        # Set supported features
        features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
        )

        if "Höhe%" in dp_roles or "StatusHöhe%" in dp_roles:
            features |= CoverEntityFeature.SET_POSITION

        if has_tilt:
            features |= CoverEntityFeature.OPEN_TILT
            features |= CoverEntityFeature.CLOSE_TILT
            features |= CoverEntityFeature.STOP_TILT
            if "Lamelle%" in dp_roles or "StatusLamelle%" in dp_roles:
                features |= CoverEntityFeature.SET_TILT_POSITION

        self._attr_supported_features = features

        # Set device info
        device_id = mapped_entity.get("device_id")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": mapped_entity.get("device_name"),
            "manufacturer": "Theben",
            "model": mapped_entity.get("device_model"),
            "sw_version": mapped_entity.get("device_model"),
        }

        # Initialize state
        self._attr_current_cover_position = None
        self._attr_current_cover_tilt_position = None
        self._attr_is_closed = None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.knx_gateway.connected

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        # Subscribe to position updates
        await self._update_position()

    async def _update_position(self) -> None:
        """Update current position and tilt from KNX."""
        try:
            # Read current position (StatusHöhe% or Höhe%)
            position_dp = "StatusHöhe%" if "StatusHöhe%" in self._datapoints else "Höhe%"
            if position_dp in self._datapoints:
                position_raw = await self.knx_gateway.read_group_address(
                    self._datapoints[position_dp]
                )
                if position_raw is not None:
                    # KNX position: 0 = closed, 100 = open
                    # HA expects: 0 = closed, 100 = open
                    self._attr_current_cover_position = position_raw
                    self._attr_is_closed = position_raw == 0

            # Read current tilt position if available
            dp_roles = {dp["role"] for dp in self._mapped_entity.get("datapoints", [])}
            has_tilt = "Lamelle%" in dp_roles or "StatusLamelle%" in dp_roles
            
            if has_tilt:
                tilt_dp = "StatusLamelle%" if "StatusLamelle%" in self._datapoints else "Lamelle%"
                if tilt_dp in self._datapoints:
                    tilt_raw = await self.knx_gateway.read_group_address(
                        self._datapoints[tilt_dp]
                    )
                    if tilt_raw is not None:
                        self._attr_current_cover_tilt_position = tilt_raw

            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error updating position for %s: %s", self.name, e)

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        try:
            # Send UP command (value 0 = UP)
            if "UpDown" in self._datapoints:
                await self.knx_gateway.write_group_address(
                    self._datapoints["UpDown"], 0
                )
                _LOGGER.info("Opening cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error opening cover %s: %s", self.name, e)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        try:
            # Send DOWN command (value 1 = DOWN)
            if "UpDown" in self._datapoints:
                await self.knx_gateway.write_group_address(
                    self._datapoints["UpDown"], 1
                )
                _LOGGER.info("Closing cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error closing cover %s: %s", self.name, e)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        try:
            # Send STOP command
            if "StepStop" in self._datapoints:
                await self.knx_gateway.write_group_address(
                    self._datapoints["StepStop"], 0
                )
                _LOGGER.info("Stopping cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error stopping cover %s: %s", self.name, e)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        if position is None:
            return

        try:
            # Write to Höhe% address
            if "Höhe%" in self._datapoints:
                await self.knx_gateway.write_group_address(
                    self._datapoints["Höhe%"], int(position)
                )
                self._attr_current_cover_position = position
                self._attr_is_closed = position == 0
                self.async_write_ha_state()
                _LOGGER.info("Set cover position for %s to %d%%", self.name, position)
        except Exception as e:
            _LOGGER.error("Error setting cover position for %s: %s", self.name, e)

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt."""
        dp_roles = {dp["role"] for dp in self._mapped_entity.get("datapoints", [])}
        has_tilt = "Lamelle%" in dp_roles or "StatusLamelle%" in dp_roles
        
        if not has_tilt:
            return

        try:
            if "Lamelle%" in self._datapoints:
                await self.knx_gateway.write_group_address(
                    self._datapoints["Lamelle%"], 100
                )
                _LOGGER.info("Opening tilt for cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error opening tilt for %s: %s", self.name, e)

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt."""
        dp_roles = {dp["role"] for dp in self._mapped_entity.get("datapoints", [])}
        has_tilt = "Lamelle%" in dp_roles or "StatusLamelle%" in dp_roles
        
        if not has_tilt:
            return

        try:
            if "Lamelle%" in self._datapoints:
                await self.knx_gateway.write_group_address(
                    self._datapoints["Lamelle%"], 0
                )
                _LOGGER.info("Closing tilt for cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error closing tilt for %s: %s", self.name, e)

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop the cover tilt."""
        dp_roles = {dp["role"] for dp in self._mapped_entity.get("datapoints", [])}
        has_tilt = "Lamelle%" in dp_roles or "StatusLamelle%" in dp_roles
        
        if not has_tilt:
            return

        try:
            if "StepStop" in self._datapoints:
                await self.knx_gateway.write_group_address(
                    self._datapoints["StepStop"], 0
                )
                _LOGGER.info("Stopping tilt for cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error stopping tilt for %s: %s", self.name, e)

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        dp_roles = {dp["role"] for dp in self._mapped_entity.get("datapoints", [])}
        has_tilt = "Lamelle%" in dp_roles or "StatusLamelle%" in dp_roles
        
        if not has_tilt:
            return

        tilt_position = kwargs.get(ATTR_TILT_POSITION)
        if tilt_position is None:
            return

        try:
            if "Lamelle%" in self._datapoints:
                await self.knx_gateway.write_group_address(
                    self._datapoints["Lamelle%"], int(tilt_position)
                )
                self._attr_current_cover_tilt_position = tilt_position
                self.async_write_ha_state()
                _LOGGER.info("Set tilt position for %s to %d%%", self.name, tilt_position)
        except Exception as e:
            _LOGGER.error("Error setting tilt position for %s: %s", self.name, e)

    async def async_update(self) -> None:
        """Update the entity."""
        await self._update_position()
