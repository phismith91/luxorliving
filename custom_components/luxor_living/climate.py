"""Climate platform for LUXORliving integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_KNX_GATEWAY, DOMAIN
from .coordinator import LuxorLivingCoordinator
from .entity_mapper import EntityMapper
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving climate devices from a config entry."""
    _LOGGER.info("Setting up LUXORliving climate devices")

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
        _LOGGER.warning("No mapper found, skipping climate setup")
        return

    if not coordinator:
        _LOGGER.error("No coordinator found, skipping climate setup")
        return

    # Get all climate entities from mapper
    climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)
    _LOGGER.info("Creating %d climate entities", len(climate_entities))

    # Create climate entities asynchronously
    entities = await asyncio.gather(
        *[
            _create_climate_entity(coordinator, entry, mapped_entity, knx_gateway)
            for mapped_entity in climate_entities
        ]
    )

    async_add_entities(entities)


async def _create_climate_entity(
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
    knx_gateway: LuxorKNXGateway,
) -> ClimateEntity:
    """Create a climate entity asynchronously."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, lambda: _create_climate_entity_sync(coordinator, entry, mapped_entity, knx_gateway)
    )


def _create_climate_entity_sync(
    coordinator: LuxorLivingCoordinator,
    entry: ConfigEntry,
    mapped_entity: Any,
    knx_gateway: LuxorKNXGateway,
) -> LuxorClimate:
    """Create a climate entity synchronously."""
    return LuxorClimate(
        coordinator=coordinator,
        knx_gateway=knx_gateway,
        mapped_entity=mapped_entity,
        entry_id=entry.entry_id,
    )


class LuxorClimate(ClimateEntity):
    """Representation of a LUXORliving climate device (H6 heating actuator)."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_target_temperature_step = 0.5
    _attr_min_temp = 5.0
    _attr_max_temp = 35.0

    def __init__(
        self,
        coordinator: LuxorLivingCoordinator,
        knx_gateway: LuxorKNXGateway,
        mapped_entity: Any,
        entry_id: str,
    ) -> None:
        """Initialize the climate entity."""
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
        self._attr_current_temperature = None
        self._attr_target_temperature = None
        self._attr_hvac_mode = HVACMode.HEAT
        self._window_contact_open = False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.knx_gateway.connected

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        # Subscribe to temperature updates
        await self._update_temperature()

    async def _update_temperature(self) -> None:
        """Update current and target temperature from KNX."""
        try:
            # Read current temperature (Istwert)
            if "Istwert" in self._datapoints:
                current_temp_raw = await self.knx_gateway.read_group_address(
                    self._datapoints["Istwert"]
                )
                if current_temp_raw is not None:
                    # KNX DPT 9.001 temperature value (16-bit float)
                    self._attr_current_temperature = current_temp_raw / 100.0

            # Read target temperature (Sollwert or StatusSollwert)
            target_dp = "StatusSollwert" if "StatusSollwert" in self._datapoints else "Sollwert"
            if target_dp in self._datapoints:
                target_temp_raw = await self.knx_gateway.read_group_address(
                    self._datapoints[target_dp]
                )
                if target_temp_raw is not None:
                    self._attr_target_temperature = target_temp_raw / 100.0

            # Check window contact if available
            if "WindowContact" in self._datapoints:
                window_raw = await self.knx_gateway.read_group_address(
                    self._datapoints["WindowContact"]
                )
                self._window_contact_open = bool(window_raw) if window_raw is not None else False

            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error updating temperature for %s: %s", self.name, e)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        try:
            # Convert to KNX DPT 9.001 format (multiply by 100)
            temp_raw = int(temperature * 100)

            # Write to Sollwert address
            if "Sollwert" in self._datapoints:
                await self.knx_gateway.write_group_address(self._datapoints["Sollwert"], temp_raw)
                self._attr_target_temperature = temperature
                self.async_write_ha_state()
                _LOGGER.info("Set temperature for %s to %.1f°C", self.name, temperature)
            else:
                _LOGGER.error("No Sollwert datapoint for %s", self.name)

        except Exception as e:
            _LOGGER.error("Error setting temperature for %s: %s", self.name, e)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode not in self._attr_hvac_modes:
            _LOGGER.warning("Unsupported HVAC mode: %s", hvac_mode)
            return

        self._attr_hvac_mode = hvac_mode

        # For H6, we don't have explicit on/off control
        # Setting to OFF means setting temperature to minimum
        if hvac_mode == HVACMode.OFF:
            await self.async_set_temperature(temperature=self._attr_min_temp)
        elif hvac_mode == HVACMode.HEAT and self._attr_target_temperature:
            # Restore previous temperature or set to default
            temp = self._attr_target_temperature or 20.0
            await self.async_set_temperature(temperature=temp)

        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the entity."""
        await self._update_temperature()
