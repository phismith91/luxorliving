"""Sensor platform for LUXORliving integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from xknx.telegram.address import GroupAddress

from .const import DOMAIN
from .coordinator import LuxorLivingCoordinator
from .entity import LuxorLivingEntity
from .entity_mapper import EntityMapper
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving sensors from a config entry."""
    _LOGGER.info("Setting up LUXORliving sensors")

    # Get coordinator, mapper and KNX gateway from integration data
    try:
        integration_data = hass.data[DOMAIN][entry.entry_id]
        if not isinstance(integration_data, dict):
            _LOGGER.error("Integration data is not a dictionary: %s", type(integration_data))
            return
        coordinator: LuxorLivingCoordinator = integration_data.get("coordinator")
        mapper: EntityMapper = integration_data.get("mapper")
        knx_gateway: LuxorKNXGateway = integration_data.get("knx_gateway")
    except (KeyError, AttributeError) as err:
        _LOGGER.error("Failed to get integration data: %s", err)
        return

    if not mapper:
        _LOGGER.warning("No mapper found, skipping sensor setup")
        return

    if not coordinator:
        _LOGGER.error("No coordinator found, skipping sensor setup")
        return

    # Get all sensor entities
    sensor_entities = mapper.get_entities_by_platform(Platform.SENSOR)
    _LOGGER.info("Creating %d sensor entities", len(sensor_entities))

    entities: list[SensorEntity] = []
    for mapped_entity in sensor_entities:
        entity = LuxorLivingSensor(coordinator, entry, mapped_entity, knx_gateway)
        entities.append(entity)

    async_add_entities(entities)


class LuxorLivingSensor(LuxorLivingEntity, SensorEntity):
    """Representation of a LUXORliving sensor."""

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        entry: ConfigEntry,
        mapped_entity: Any,
        knx_gateway: LuxorKNXGateway,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Data coordinator instance
            entry: Config entry for this integration
            mapped_entity: Mapped entity data from LXP file
            knx_gateway: KNX gateway instance
        """
        super().__init__(coordinator, entry, mapped_entity)

        self._knx_gateway = knx_gateway
        self._attr_native_value = None

        # Get sensor-specific attributes from mapped entity
        self._attr_native_unit_of_measurement = mapped_entity.attributes.get(
            "unit_of_measurement"
        )
        device_class = mapped_entity.attributes.get("device_class")
        if device_class:
            self._attr_device_class = device_class

        # Store datapoint address for state reading
        datapoints = mapped_entity.datapoints
        self._datapoint_address: str | None = None

        # Get the primary datapoint address based on entity type
        entity_type = mapped_entity.entity_type.lower()
        if entity_type == "temperature":
            self._datapoint_address = datapoints.get("Temperature")
        elif entity_type == "humidity":
            self._datapoint_address = datapoints.get("Humidity")
        elif entity_type == "pressure":
            self._datapoint_address = datapoints.get("Pressure")
        elif entity_type == "co2":
            self._datapoint_address = datapoints.get("CO2")
        elif entity_type == "brightness":
            self._datapoint_address = datapoints.get("Brightness")
        elif entity_type == "windspeed":
            self._datapoint_address = datapoints.get("WindSpeed")
        elif entity_type == "rainvolume":
            self._datapoint_address = datapoints.get("RainVolume")
        elif entity_type == "airquality":
            self._datapoint_address = datapoints.get("AirQuality")
        else:
            # Fallback: use first datapoint address
            if datapoints:
                self._datapoint_address = list(datapoints.values())[0]

        _LOGGER.debug(
            "Initialized sensor '%s' (type=%s, address=%s, unit=%s)",
            mapped_entity.name,
            entity_type,
            self._datapoint_address,
            self._attr_native_unit_of_measurement,
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to Home Assistant."""
        await super().async_added_to_hass()

        # Read initial state from KNX
        if self._datapoint_address is not None:
            _LOGGER.debug(
                "Reading initial state for sensor '%s' from address %s",
                self.name,
                self._datapoint_address,
            )
            await self._async_read_state()

        # Register for KNX telegram updates
        if self._knx_gateway and self._datapoint_address is not None:
            self._knx_gateway.register_telegram_listener(
                self._datapoint_address, self._on_telegram
            )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from Home Assistant."""
        # Unregister from KNX telegram updates
        if self._knx_gateway and self._datapoint_address is not None:
            self._knx_gateway.unregister_telegram_listener(
                self._datapoint_address, self._on_telegram
            )
        await super().async_will_remove_from_hass()

    async def _async_read_state(self) -> None:
        """Read current state from KNX device."""
        if not self._datapoint_address:
            return

        try:
            value = await self._knx_gateway.async_read_group_value(self._datapoint_address)
            if value is not None:
                self._attr_native_value = value
                _LOGGER.debug(
                    "Read state for sensor '%s': %s %s",
                    self.name,
                    value,
                    self._attr_native_unit_of_measurement or "",
                )
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Error reading state for sensor '%s': %s", self.name, err)

    def _on_telegram(self, value: Any) -> None:
        """Handle incoming KNX telegram for this sensor."""
        _LOGGER.debug(
            "Received telegram for sensor '%s': %s %s",
            self.name,
            value,
            self._attr_native_unit_of_measurement or "",
        )

        self._attr_native_value = value
        self.async_write_ha_state()

