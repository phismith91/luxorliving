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
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LuxorLivingCoordinator
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving covers from a config entry."""
    _LOGGER.info("Setting up LUXORliving covers")

    state = entry.runtime_data
    coordinator = state.coordinator
    mapper = state.mapper
    knx_gateway = state.knx_gateway

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
    loop = asyncio.get_running_loop()
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
        self._entry_id = entry_id

        # Map datapoint addresses by role (MappedEntity.datapoints is already dict[str, int])
        self._datapoints = mapped_entity.datapoints

        # Set unique ID
        self._attr_unique_id = mapped_entity.unique_id

        # Set name
        self._attr_name = mapped_entity.name

        # Determine if this is a blind (has tilt) or shutter
        dp_roles = set(mapped_entity.datapoints.keys())
        has_tilt = "Lamelle%" in dp_roles or "StatusLamelle%" in dp_roles

        # Set device class
        if has_tilt:
            self._attr_device_class = CoverDeviceClass.BLIND
        else:
            self._attr_device_class = CoverDeviceClass.SHUTTER

        # Set supported features
        features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP

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
        device_id = mapped_entity.device_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": mapped_entity.device_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }

        # Initialize state
        self._attr_current_cover_position = None
        self._attr_current_cover_tilt_position = None
        self._attr_is_closed = None

        # Listener refs stored for cleanup in async_will_remove_from_hass
        self._knx_listener_refs: list[tuple[int, Any]] = []

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.knx_gateway.connected

    def _raise_if_unavailable(self) -> None:
        """Raise HomeAssistantError if the gateway is not available."""
        if not self.available:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="entity_unavailable",
            )

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Register KNX listeners — must run here, not in __init__, so that
        # async_write_ha_state() is safe and __init__ stays thread-safe
        # (it runs in an executor via run_in_executor).
        position_dp = "StatusHöhe%" if "StatusHöhe%" in self._datapoints else "Höhe%"
        if position_dp in self._datapoints:
            addr = self._datapoints[position_dp]
            self.knx_gateway.register_listener(addr, self._handle_position_update)
            self._knx_listener_refs.append((addr, self._handle_position_update))

        tilt_dp_key = "StatusLamelle%" if "StatusLamelle%" in self._datapoints else "Lamelle%"
        if tilt_dp_key in self._datapoints:
            addr = self._datapoints[tilt_dp_key]
            self.knx_gateway.register_listener(addr, self._handle_tilt_update)
            self._knx_listener_refs.append((addr, self._handle_tilt_update))

        # Request initial position state — wait up to 5s for KNX connection
        if self.knx_gateway.connected:
            await self._update_position()

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity is removed from hass."""
        for addr, cb in self._knx_listener_refs:
            self.knx_gateway.unregister_listener(addr, cb)
        self._knx_listener_refs.clear()

    def _handle_position_update(self, group_address: str, value: Any) -> None:
        """Handle cover position update received via KNX telegram."""
        if isinstance(value, (int, float)):
            # KNX Höhe% convention: 0 = fully up (open), 100 = fully down (closed)
            # HA position convention: 0 = closed, 100 = open → invert
            ha_position = 100 - int(value)
            self._attr_current_cover_position = ha_position
            self._attr_is_closed = ha_position == 0
            self.async_write_ha_state()

    def _handle_tilt_update(self, group_address: str, value: Any) -> None:
        """Handle tilt position update received via KNX telegram."""
        if isinstance(value, (int, float)):
            # KNX Lamelle% convention: 0 = open, 100 = closed → invert (#197)
            self._attr_current_cover_tilt_position = 100 - int(value)
            self.async_write_ha_state()

    async def _update_position(self) -> None:
        """Request current position and tilt from KNX bus."""
        # Read current position (StatusHöhe% preferred, fallback to Höhe%)
        position_dp = "StatusHöhe%" if "StatusHöhe%" in self._datapoints else "Höhe%"
        if position_dp in self._datapoints:
            await self.knx_gateway.async_read_group_address(self._datapoints[position_dp])

        # Read current tilt position if available
        has_tilt = "Lamelle%" in self._datapoints or "StatusLamelle%" in self._datapoints
        if has_tilt:
            tilt_dp = "StatusLamelle%" if "StatusLamelle%" in self._datapoints else "Lamelle%"
            if tilt_dp in self._datapoints:
                await self.knx_gateway.async_read_group_address(self._datapoints[tilt_dp])

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        self._raise_if_unavailable()
        try:
            # Send UP command (value 0 = UP)
            if "UpDown" in self._datapoints:
                await self.knx_gateway.async_send_telegram(self._datapoints["UpDown"], 0, "binary")
                _LOGGER.info("Opening cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error opening cover %s: %s", self.name, e)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        self._raise_if_unavailable()
        try:
            # Send DOWN command (value 1 = DOWN)
            if "UpDown" in self._datapoints:
                await self.knx_gateway.async_send_telegram(self._datapoints["UpDown"], 1, "binary")
                _LOGGER.info("Closing cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error closing cover %s: %s", self.name, e)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        self._raise_if_unavailable()
        try:
            # Send STOP command
            if "StepStop" in self._datapoints:
                await self.knx_gateway.async_send_telegram(
                    self._datapoints["StepStop"], 0, "binary"
                )
                _LOGGER.info("Stopping cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error stopping cover %s: %s", self.name, e)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        self._raise_if_unavailable()
        position = kwargs.get(ATTR_POSITION)
        if position is None:
            return

        try:
            # Write to Höhe% address — invert HA position to KNX Höhe% convention
            if "Höhe%" in self._datapoints:
                knx_position = 100 - int(position)
                success = await self.knx_gateway.async_send_telegram(
                    self._datapoints["Höhe%"], knx_position, "percent"
                )
                if success:
                    self._attr_current_cover_position = int(position)
                    self._attr_is_closed = int(position) == 0
                    self.async_write_ha_state()
                    _LOGGER.info("Set cover position for %s to %d%%", self.name, position)
        except Exception as e:
            _LOGGER.error("Error setting cover position for %s: %s", self.name, e)

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt."""
        self._raise_if_unavailable()
        has_tilt = "Lamelle%" in self._datapoints or "StatusLamelle%" in self._datapoints

        if not has_tilt:
            return

        try:
            if "Lamelle%" in self._datapoints:
                # KNX Lamelle% convention: 0 = open, 100 = closed (#197)
                await self.knx_gateway.async_send_telegram(
                    self._datapoints["Lamelle%"], 0, "percent"
                )
                _LOGGER.info("Opening tilt for cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error opening tilt for %s: %s", self.name, e)

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt."""
        self._raise_if_unavailable()
        has_tilt = "Lamelle%" in self._datapoints or "StatusLamelle%" in self._datapoints

        if not has_tilt:
            return

        try:
            if "Lamelle%" in self._datapoints:
                # KNX Lamelle% convention: 0 = open, 100 = closed (#197)
                await self.knx_gateway.async_send_telegram(
                    self._datapoints["Lamelle%"], 100, "percent"
                )
                _LOGGER.info("Closing tilt for cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error closing tilt for %s: %s", self.name, e)

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop the cover tilt."""
        self._raise_if_unavailable()
        has_tilt = "Lamelle%" in self._datapoints or "StatusLamelle%" in self._datapoints

        if not has_tilt:
            return

        try:
            if "StepStop" in self._datapoints:
                await self.knx_gateway.async_send_telegram(
                    self._datapoints["StepStop"], 0, "binary"
                )
                _LOGGER.info("Stopping tilt for cover: %s", self.name)
        except Exception as e:
            _LOGGER.error("Error stopping tilt for %s: %s", self.name, e)

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        self._raise_if_unavailable()
        has_tilt = "Lamelle%" in self._datapoints or "StatusLamelle%" in self._datapoints

        if not has_tilt:
            return

        tilt_position = kwargs.get(ATTR_TILT_POSITION)
        if tilt_position is None:
            return

        try:
            if "Lamelle%" in self._datapoints:
                # Invert HA tilt position to KNX Lamelle% convention (#197)
                knx_tilt = 100 - int(tilt_position)
                success = await self.knx_gateway.async_send_telegram(
                    self._datapoints["Lamelle%"], knx_tilt, "percent"
                )
                if success:
                    self._attr_current_cover_tilt_position = int(tilt_position)
                    self.async_write_ha_state()
                    _LOGGER.info("Set tilt position for %s to %d%%", self.name, tilt_position)
        except Exception as e:
            _LOGGER.error("Error setting tilt position for %s: %s", self.name, e)

    async def async_update(self) -> None:
        """Refresh coordinator state without actively polling KNX again."""
        await self.coordinator.async_request_refresh()
