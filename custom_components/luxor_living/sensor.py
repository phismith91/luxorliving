"""Sensor platform for LUXORliving integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from xknx.dpt import DPT2ByteFloat, DPTArray

from .coordinator import LuxorLivingCoordinator
from .entity import LuxorLivingEntity
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving sensors from a config entry."""
    _LOGGER.info("Setting up LUXORliving sensors")

    state = entry.runtime_data
    coordinator = state.coordinator
    mapper = state.mapper
    knx_gateway = state.knx_gateway

    if not mapper:
        _LOGGER.warning("No mapper found, skipping sensor setup")
        return

    if not coordinator:
        _LOGGER.error("No coordinator found, skipping sensor setup")
        return

    # Get all sensor entities from LXP
    sensor_entities = mapper.get_entities_by_platform(Platform.SENSOR)
    _LOGGER.info("Creating %d LXP sensor entities", len(sensor_entities))

    # Create LXP entities asynchronously
    lxp_entities = await asyncio.gather(
        *[
            _create_lxp_sensor_entity(coordinator, entry, mapped_entity, knx_gateway)
            for mapped_entity in sensor_entities
        ]
    )

    # Add auto-discovered sensors
    discovered_sensors = knx_gateway.get_discovered_sensors()
    _LOGGER.info("Creating %d auto-discovered sensor entities", len(discovered_sensors))

    # Create discovered entities asynchronously
    discovered_entities = await asyncio.gather(
        *[
            _create_discovered_sensor_entity(coordinator, entry, sensor_info, knx_gateway)
            for address, sensor_info in discovered_sensors.items()
        ]
    )

    async_add_entities([*lxp_entities, *discovered_entities])


async def _create_lxp_sensor_entity(
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
    knx_gateway: LuxorKNXGateway,
) -> LuxorLivingSensor:
    """Create a LXP sensor entity asynchronously."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, lambda: LuxorLivingSensor(coordinator, entry, mapped_entity, knx_gateway)
    )


async def _create_discovered_sensor_entity(
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    sensor_info: Any,
    knx_gateway: LuxorKNXGateway,
) -> LuxorLivingDiscoveredSensor:
    """Create a discovered sensor entity asynchronously."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, lambda: LuxorLivingDiscoveredSensor(coordinator, entry, sensor_info, knx_gateway)
    )


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
        self._attr_native_unit_of_measurement = mapped_entity.attributes.get("unit_of_measurement")
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
            self._knx_gateway.register_listener(self._datapoint_address, self._on_telegram)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from Home Assistant."""
        # Unregister from KNX telegram updates
        if self._knx_gateway and self._datapoint_address is not None:
            self._knx_gateway.unregister_listener(self._datapoint_address, self._on_telegram)
        await super().async_will_remove_from_hass()

    async def _async_read_state(self) -> None:
        """Read current state from KNX device."""
        if not self._datapoint_address:
            return

        try:
            # Send read request - value will arrive via telegram callback
            await self._knx_gateway.async_read_group_address(
                self._datapoint_address, is_initial=True
            )
            _LOGGER.debug(
                "Sent read request for sensor '%s' to address %s",
                self.name,
                self._datapoint_address,
            )
        except Exception as err:
            _LOGGER.error("Error reading state for sensor '%s': %s", self.name, err)

    def _on_telegram(self, group_address: str, value: Any) -> None:
        """Handle incoming KNX telegram for this sensor.

        Args:
            group_address: KNX group address that was updated
            value: New value from KNX telegram
        """
        # Normalize common raw payloads (e.g., tuple-of-bytes from Wetterstation)
        normalized = self._normalize_value(value)

        _LOGGER.debug(
            "Received telegram for sensor '%s' from %s: %s → %s %s",
            self.name,
            group_address,
            value,
            normalized,
            self._attr_native_unit_of_measurement or "",
        )

        if normalized is None:
            _LOGGER.debug("Skipping state update for %s - normalized value is None", self.name)
            return

        self._attr_native_value = normalized
        self.async_write_ha_state()

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """Convert raw KNX payloads into HA-friendly numeric values."""
        # Handle tuple/list of two bytes (common for DPT 2-byte float)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            try:
                return DPT2ByteFloat().from_knx(DPTArray(value))
            except Exception as err:
                _LOGGER.debug("DPT2ByteFloat decode failed for %r: %s", value, err)
                return value

        # For all other values, return as-is
        return value


class LuxorLivingDiscoveredSensor(SensorEntity):
    """Representation of an auto-discovered LUXORliving sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        entry: ConfigEntry,
        sensor_info: dict[str, Any],
        knx_gateway: LuxorKNXGateway,
    ) -> None:
        """Initialize the auto-discovered sensor."""
        self._coordinator = coordinator
        self._entry = entry
        self._sensor_info = sensor_info
        self._knx_gateway = knx_gateway
        self._address = sensor_info["address"]

        # Generate unique ID from address
        address_clean = self._address.replace("/", "_")
        self._attr_unique_id = f"{entry.entry_id}_auto_{address_clean}"

        # Set name based on type and address
        sensor_type = sensor_info.get("type", "sensor")
        self._attr_name = f"Auto {sensor_type.title()} {self._address}"

        # Set device class and unit based on sensor type
        self._setup_sensor_attributes(sensor_type)

        # Initial value
        self._attr_native_value = sensor_info.get("last_value")

    def _setup_sensor_attributes(self, sensor_type: str) -> None:
        """Configure sensor attributes based on detected type."""
        from homeassistant.components.sensor import SensorDeviceClass
        from homeassistant.const import (
            LIGHT_LUX,
            PERCENTAGE,
            UnitOfPressure,
            UnitOfTemperature,
        )

        type_config: dict[str, dict[str, Any]] = {
            "temperature": {
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "icon": "mdi:thermometer",
            },
            "humidity": {
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit": PERCENTAGE,
                "icon": "mdi:water-percent",
            },
            "illuminance": {
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit": LIGHT_LUX,
                "icon": "mdi:brightness-5",
            },
            "pressure": {
                "device_class": SensorDeviceClass.PRESSURE,
                "unit": UnitOfPressure.PA,
                "icon": "mdi:gauge",
            },
            "generic_sensor": {
                "device_class": None,
                "unit": None,
                "icon": "mdi:gauge",
            },
        }

        config = type_config.get(sensor_type, type_config["generic_sensor"])
        self._attr_device_class = config["device_class"]
        self._attr_native_unit_of_measurement = config["unit"]
        self._attr_icon = config["icon"]

    async def async_added_to_hass(self) -> None:
        """Register KNX listener when added to Home Assistant."""

        def on_telegram_update(address: str, value: Any) -> None:
            """Handle KNX telegram updates."""
            if isinstance(value, float):
                self._attr_native_value = value
                self.async_write_ha_state()

        self._knx_gateway.register_listener(self._address, on_telegram_update)
        _LOGGER.info("Registered auto-discovered sensor: %s (%s)", self._attr_name, self._address)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister KNX listener when removed."""

        def dummy_callback(address: str, value: Any) -> None:
            pass

        self._knx_gateway.unregister_listener(self._address, dummy_callback)
