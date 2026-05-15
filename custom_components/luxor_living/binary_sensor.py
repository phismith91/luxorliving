"""Binary sensor platform for LUXORliving integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LuxorLivingCoordinator
from .entity import LuxorLivingEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving binary sensors from a config entry."""
    _LOGGER.info("Setting up LUXORliving binary sensors")

    state = entry.runtime_data
    coordinator = state.coordinator
    mapper = state.mapper

    if not mapper:
        _LOGGER.warning("No mapper found, skipping binary sensor setup")
        return

    if not coordinator:
        _LOGGER.error("No coordinator found, skipping binary sensor setup")
        return

    # Get all binary sensor entities
    sensor_entities = mapper.get_entities_by_platform(Platform.BINARY_SENSOR)
    _LOGGER.info("Creating %d binary sensor entities", len(sensor_entities))

    # Create binary sensor entities asynchronously
    entities = await asyncio.gather(
        *[
            _create_binary_sensor_entity(coordinator, entry, mapped_entity)
            for mapped_entity in sensor_entities
        ]
    )

    async_add_entities(entities)


async def _create_binary_sensor_entity(
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
) -> LuxorLivingBinarySensor:
    """Create a binary sensor entity asynchronously."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, lambda: LuxorLivingBinarySensor(coordinator, entry, mapped_entity)
    )


class LuxorLivingBinarySensor(LuxorLivingEntity, BinarySensorEntity):
    """Representation of a LUXORliving binary sensor."""

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        entry: ConfigEntry,
        mapped_entity: Any,
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: Data coordinator instance
            entry: Config entry for this integration
            mapped_entity: Mapped entity data from LXP file
        """
        super().__init__(coordinator, entry, mapped_entity)

        self._attr_is_on = False

        # Determine device class based on entity type and name
        self._attr_device_class = self._detect_device_class(mapped_entity)

        # Mark health/connectivity sensors as diagnostic and disabled by default
        if getattr(mapped_entity, "entity_type", "") == "health":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = False

        # Store datapoint addresses
        self._address_status: str | None = (
            mapped_entity.datapoints.get("status@OnOff")
            or mapped_entity.datapoints.get("OnOff")
            or mapped_entity.datapoints.get("SchaltenOnOff")
        )

        # KNX listener ref for cleanup (populated in async_added_to_hass)
        self._knx_listener_addr: int | None = None

        _LOGGER.debug(
            "📊 Binary Sensor '%s' (class: %s) status address: %s",
            self.name,
            self._attr_device_class,
            self._address_status,
        )

    async def async_added_to_hass(self) -> None:
        """Register KNX listener for real-time state updates."""
        await super().async_added_to_hass()
        if self._address_status is None:
            return
        runtime_data = getattr(self._config_entry, "runtime_data", None)
        knx_gateway = getattr(runtime_data, "knx_gateway", None)
        if knx_gateway:
            self._knx_listener_addr = self._address_status
            knx_gateway.register_listener(self._address_status, self._handle_knx_state)
            await knx_gateway.async_read_group_address(self._address_status)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister KNX listener on removal."""
        if self._knx_listener_addr is None:
            return
        runtime_data = getattr(self._config_entry, "runtime_data", None)
        knx_gateway = getattr(runtime_data, "knx_gateway", None)
        if knx_gateway:
            knx_gateway.unregister_listener(self._knx_listener_addr, self._handle_knx_state)
        self._knx_listener_addr = None

    def _handle_knx_state(self, address: Any, value: Any) -> None:
        """Handle KNX telegram for this binary sensor's status address."""
        self.coordinator.set_state(self._address_status, bool(value))

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self._mapped_entity.entity_type == "health":
            # Health sensor: check if all gateways are connected or in simulation mode
            for config_entry in self.hass.config_entries.async_entries(DOMAIN):
                knx_gateway = getattr(config_entry.runtime_data, "knx_gateway", None)
                if knx_gateway and not knx_gateway.connected and not knx_gateway.simulation_mode:
                    return False
            return True
        else:
            # Default: use coordinator data
            return self.coordinator.get_state(self._address_status)

    def _detect_device_class(self, mapped_entity: Any) -> BinarySensorDeviceClass | None:
        """Detect the device class based on entity type and name.

        Args:
            mapped_entity: Mapped entity data

        Returns:
            BinarySensorDeviceClass or None
        """
        entity_type = (
            mapped_entity.entity_type.lower() if hasattr(mapped_entity, "entity_type") else ""
        )
        entity_name = mapped_entity.name.lower() if hasattr(mapped_entity, "name") else ""

        # Check entity type first
        if entity_type == "motion":
            return BinarySensorDeviceClass.MOTION
        if entity_type == "health":
            return BinarySensorDeviceClass.CONNECTIVITY

        # Check name for keywords
        if "rauchmelder" in entity_name or "smoke" in entity_name:
            return BinarySensorDeviceClass.SMOKE
        if "fenster" in entity_name or "window" in entity_name:
            return BinarySensorDeviceClass.OPENING
        if "tür" in entity_name or "door" in entity_name:
            return BinarySensorDeviceClass.OPENING
        if "motion" in entity_name or "bewegung" in entity_name:
            return BinarySensorDeviceClass.MOTION
        if "vibration" in entity_name:
            return BinarySensorDeviceClass.VIBRATION

        # Default: no specific class
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes.

        Returns:
            Dictionary of extra state attributes
        """
        attrs: dict[str, Any] = {}

        if self._address_status:
            attrs["knx_address"] = str(self._address_status)

        if hasattr(self._mapped_entity, "attributes"):
            sensor_type = self._mapped_entity.attributes.get("sensor_type")
            if sensor_type:
                attrs["sensor_type"] = sensor_type

        # Add LXP parameter attributes
        attrs.update(self._get_parameter_attributes())

        return attrs
