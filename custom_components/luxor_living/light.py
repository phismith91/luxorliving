"""Light platform for LUXORliving integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from xknx.telegram.address import GroupAddress

from .coordinator import LuxorLivingCoordinator
from .entity import LuxorLivingEntity
from .integration_state import get_integration_state
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving lights from a config entry."""
    _LOGGER.info("Setting up LUXORliving lights")

    # Get type-safe integration state
    try:
        state = get_integration_state(entry.entry_id)
        coordinator = state.coordinator
        mapper = state.mapper
        knx_gateway = state.knx_gateway
    except (KeyError, AttributeError) as err:
        _LOGGER.error("Failed to get integration state: %s", err)
        return

    if not mapper:
        _LOGGER.warning("No mapper found, skipping light setup")
        return

    if not coordinator:
        _LOGGER.error("No coordinator found, skipping light setup")
        return

    # Get all light entities
    light_entities = mapper.get_entities_by_platform(Platform.LIGHT)
    _LOGGER.info("Creating %d light entities", len(light_entities))

    # Create light entities asynchronously
    entities = await asyncio.gather(
        *[
            _create_light_entity(coordinator, entry, mapped_entity, knx_gateway)
            for mapped_entity in light_entities
        ]
    )

    async_add_entities(entities)


async def _create_light_entity(
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
    knx_gateway: LuxorKNXGateway,
) -> LightEntity:
    """Create a light entity asynchronously."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, lambda: _create_light_entity_sync(coordinator, entry, mapped_entity, knx_gateway)
    )


def _create_light_entity_sync(
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
    knx_gateway: LuxorKNXGateway,
) -> LightEntity:
    """Create a light entity synchronously."""
    if mapped_entity.entity_type == "dimmable_light":
        return LuxorLivingDimmableLight(coordinator, entry, mapped_entity, knx_gateway)
    else:
        return LuxorLivingLight(coordinator, entry, mapped_entity, knx_gateway)


class LuxorLivingLight(LuxorLivingEntity, LightEntity):
    """Representation of a LUXORliving light."""

    _attr_color_mode: ColorMode = ColorMode.ONOFF
    _attr_supported_color_modes: set[ColorMode] = {ColorMode.ONOFF}

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        entry: ConfigEntry,
        mapped_entity: Any,
        knx_gateway: LuxorKNXGateway,
    ) -> None:
        """Initialize the light.

        Args:
            coordinator: Data coordinator instance
            entry: Config entry for this integration
            mapped_entity: Mapped entity data from LXP file
            knx_gateway: KNX gateway instance
        """
        super().__init__(coordinator, entry, mapped_entity)

        self._knx_gateway = knx_gateway
        self._attr_is_on = False
        self._command_times: list[float] = []  # Track command timestamps for rate limiting

        # Store datapoint addresses
        self._address_on: str | None = mapped_entity.datapoints.get(
            "OnOff"
        ) or mapped_entity.datapoints.get("SchaltenOnOff")
        self._address_status: str | None = mapped_entity.datapoints.get(
            "StatusOnOff"
        ) or mapped_entity.datapoints.get("status@OnOff")

        # Debug: Log extracted addresses
        _LOGGER.debug(
            "💡 Light '%s' addresses: ON=%s, STATUS=%s",
            self.name,
            (
                f"{self._address_on} ({GroupAddress(self._address_on)})"
                if self._address_on
                else "None"
            ),
            (
                f"{self._address_status} ({GroupAddress(self._address_status)})"
                if self._address_status
                else "None"
            ),
        )

        # Register listeners for BOTH status AND control addresses
        # GroupValueResponse can come on either address!
        # STATUS address: for state updates from other devices
        # CONTROL address: for GroupValueResponse to our GroupValueRead
        self._listen_addresses: list[str] = []

        if self._address_status:
            self._knx_gateway.register_listener(
                self._address_status,
                self._handle_knx_update,
            )
            self._listen_addresses.append(self._address_status)

        if self._address_on and self._address_on != self._address_status:
            self._knx_gateway.register_listener(
                self._address_on,
                self._handle_knx_update,
            )
            self._listen_addresses.append(self._address_on)

    def _is_rate_limited(self) -> bool:
        """Check if command should be rate limited to prevent 'light show' loops.

        Returns True if too many commands in short time (5+ in 1 second).
        """
        import time

        now = time.time()

        # Remove old timestamps (>1 second ago)
        self._command_times = [t for t in self._command_times if now - t <= 1.0]

        # Check if we have 5+ commands in the last second
        if len(self._command_times) >= 5:
            _LOGGER.warning(
                "Rate limiting light %s: %d commands in 1 second, blocking further commands",
                self.name,
                len(self._command_times),
            )
            return True

        # Add current timestamp
        self._command_times.append(now)
        return False

    async def async_added_to_hass(self) -> None:
        """Entity added to hass - request current state from KNX."""
        await super().async_added_to_hass()

        # Wait for KNX connection to be ready (max 5 seconds)
        if not self._knx_gateway._connected:
            _LOGGER.debug("⏳ Waiting for KNX connection for light '%s'...", self.name)
            for i in range(50):
                if self._knx_gateway._connected:
                    _LOGGER.debug("✅ KNX connected after %.1fs for '%s'", i * 0.1, self.name)
                    break
                await asyncio.sleep(0.1)

            if not self._knx_gateway._connected:
                _LOGGER.error(
                    "KNX not connected after 5s for light '%s', skipping initial read!",
                    self.name,
                )
                return

        # BETA 7.7: Use KNX GroupValueRead for initial state
        # REST API mapping removed (BAOS Datapoints ≠ GroupAddresses)
        # Request current state from KNX bus via GroupValueRead
        # Read BOTH addresses to work around stale BAOS StatusOnOff values
        # StatusOnOff may be stale if light was ON at BAOS startup or switched manually
        # OnOff reflects actual actuator state more reliably
        addresses_to_read: list[tuple[str, str]] = []

        if self._address_status:
            addresses_to_read.append((self._address_status, "STATUS"))
        if self._address_on and self._address_on != self._address_status:
            addresses_to_read.append((self._address_on, "CONTROL"))

        if addresses_to_read:
            _LOGGER.info(
                "💡 Light '%s' requesting initial state from %d address(es): %s",
                self.name,
                len(addresses_to_read),
                ", ".join([f"{GroupAddress(addr)} ({typ})" for addr, typ in addresses_to_read]),
            )
            for address, address_type in addresses_to_read:
                await self._knx_gateway.async_read_group_address(address, is_initial=True)
        else:
            _LOGGER.warning(
                "⚠️ Light '%s' has NO read address! Cannot request initial state.",
                self.name,
            )

    def _handle_knx_update(self, group_address: str, value: Any) -> None:
        """Handle KNX status update.

        Args:
            group_address: KNX group address that was updated
            value: New value from KNX bus
        """
        # Accept updates from both status and control addresses
        # Convert integer addresses to strings for comparison
        valid_addresses: list[str] = []
        if self._address_on is not None:
            valid_addresses.append(str(GroupAddress(self._address_on)))
        if self._address_status is not None:
            valid_addresses.append(str(GroupAddress(self._address_status)))

        if group_address in valid_addresses:
            self._attr_is_on = bool(value)
            self.async_write_ha_state()
            _LOGGER.debug("Updated %s state: %s (from %s)", self.name, value, group_address)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on.

        Args:
            **kwargs: Additional keyword arguments (brightness, etc.)
        """
        if self._is_rate_limited():
            return

        if self._address_on:
            success = await self._knx_gateway.async_send_telegram(
                self._address_on,
                True,
                "binary",
            )
            if success:
                self._attr_is_on = True
                self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off.

        Args:
            **kwargs: Additional keyword arguments
        """
        if self._is_rate_limited():
            return

        if self._address_on:
            success = await self._knx_gateway.async_send_telegram(
                self._address_on,
                False,
                "binary",
            )
            if success:
                self._attr_is_on = False
                self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listener when entity is removed."""
        if hasattr(self, "_listen_addresses") and self._listen_addresses:
            for addr in list(self._listen_addresses):
                self._knx_gateway.unregister_listener(
                    addr,
                    self._handle_knx_update,
                )
        await super().async_will_remove_from_hass()


class LuxorLivingDimmableLight(LuxorLivingLight):
    """Representation of a dimmable LUXORliving light."""

    _attr_color_mode: ColorMode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes: set[ColorMode] = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        entry: ConfigEntry,
        mapped_entity: Any,
        knx_gateway: LuxorKNXGateway,
    ) -> None:
        """Initialize the dimmable light.

        Args:
            coordinator: Data coordinator instance
            entry: Config entry for this integration
            mapped_entity: Mapped entity data from LXP file
            knx_gateway: KNX gateway instance
        """
        super().__init__(coordinator, entry, mapped_entity, knx_gateway)
        self._attr_brightness = 255

        # Additional datapoints for dimming
        self._address_dim: str | None = mapped_entity.datapoints.get("Dimmen%")
        self._address_dim_rel: str | None = mapped_entity.datapoints.get("DimmenRel")
        self._address_dim_status: str | None = mapped_entity.datapoints.get("Status%")

        # Register listeners for brightness updates (status and control)
        if self._address_dim:
            self._knx_gateway.register_listener(
                self._address_dim,
                self._handle_brightness_update,
            )
        if self._address_dim_status:
            self._knx_gateway.register_listener(
                self._address_dim_status,
                self._handle_brightness_update,
            )

    async def async_added_to_hass(self) -> None:
        """Entity added to hass - request current state from KNX."""
        await super().async_added_to_hass()

        # Request current brightness from KNX bus
        # Prefer reading Status% (current brightness), also read Dimmen% for completeness
        if self._address_dim_status:
            _LOGGER.debug(
                "Requesting initial brightness for %s from %s",
                self.name,
                self._address_dim_status,
            )
            await self._knx_gateway.async_read_group_address(
                self._address_dim_status,
                is_initial=True,
            )
        if self._address_dim:
            _LOGGER.debug(
                "Requesting initial brightness for %s from %s",
                self.name,
                self._address_dim,
            )
            await self._knx_gateway.async_read_group_address(
                self._address_dim,
                is_initial=True,
            )

    def _handle_brightness_update(self, group_address: str, value: Any) -> None:
        """Handle KNX brightness update.

        Args:
            group_address: KNX group address that was updated
            value: New brightness value (0-100)
        """
        valid_brightness_addresses: list[str] = []
        if self._address_dim is not None:
            valid_brightness_addresses.append(str(GroupAddress(self._address_dim)))
        if self._address_dim_status is not None:
            valid_brightness_addresses.append(str(GroupAddress(self._address_dim_status)))
        if group_address in valid_brightness_addresses:
            # Convert percentage (0-100) to brightness (0-255)
            if isinstance(value, (int, float)):
                self._attr_brightness = int(value * 255 / 100)
                self._attr_is_on = self._attr_brightness > 0
                self.async_write_ha_state()
                _LOGGER.debug(
                    "Updated %s brightness: %d%%",
                    self.name,
                    value,
                )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on.

        Args:
            **kwargs: Additional keyword arguments (brightness, etc.)
        """
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)

        # Send brightness value if dimming address exists
        if self._address_dim:
            # Convert brightness (0-255) to percentage (0-100)
            percent = int(brightness * 100 / 255)
            success = await self._knx_gateway.async_send_telegram(
                self._address_dim,
                percent,
                "percent",
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
        """Return extra attributes.

        Returns:
            Dictionary of extra state attributes
        """
        attrs: dict[str, Any] = {}

        # Convert integer KNX addresses to group address strings
        if self._address_on is not None:
            attrs["knx_address_on"] = str(GroupAddress(self._address_on))

        if self._address_status is not None:
            attrs["knx_address_status"] = str(GroupAddress(self._address_status))

        if self._address_dim is not None:
            attrs["knx_address_dim"] = str(GroupAddress(self._address_dim))
        if self._address_dim_status is not None:
            attrs["knx_address_dim_status"] = str(GroupAddress(self._address_dim_status))

        # Add LXP parameter attributes
        attrs.update(self._get_parameter_attributes())

        return attrs

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners when entity is removed."""
        if self._address_dim:
            self._knx_gateway.unregister_listener(
                self._address_dim,
                self._handle_brightness_update,
            )
        if self._address_dim_status:
            self._knx_gateway.unregister_listener(
                self._address_dim_status,
                self._handle_brightness_update,
            )
        await super().async_will_remove_from_hass()
