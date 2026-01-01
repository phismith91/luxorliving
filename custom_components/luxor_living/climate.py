"""Climate platform for LUXORliving integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DATA_KNX_GATEWAY
from .coordinator import LuxorLivingCoordinator
from .knx_gateway import LuxorKNXGateway

_LOGGER = logging.getLogger(__name__)

# H6 Heating Actuator App IDs
HEATING_APP_IDS = ["18502"]  # H6 6-channel heating actuator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LUXORliving climate devices from a config entry."""
    _LOGGER.info("Setting up LUXORliving climate devices")

    coordinator: LuxorLivingCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    knx_gateway: LuxorKNXGateway = hass.data[DOMAIN][entry.entry_id][DATA_KNX_GATEWAY]
    project = coordinator.project

    entities: list[LuxorClimate] = []

    # Find all H6 heating actuators
    for device in project.devices:
        if device.app_id not in HEATING_APP_IDS:
            continue

        _LOGGER.debug(
            "Found heating device: %s (App ID: %s) with %d actuators",
            device.name,
            device.app_id,
            len(device.actuators),
        )

        # Each actuator channel is a separate climate entity (e.g., FBH room)
        for actuator in device.actuators:
            # Check if actuator has required datapoints for climate control
            dp_roles = {dp.role for dp in actuator.datapoints}

            if "Istwert" in dp_roles and "Sollwert" in dp_roles:
                entities.append(
                    LuxorClimate(
                        coordinator=coordinator,
                        knx_gateway=knx_gateway,
                        device=device,
                        actuator=actuator,
                        entry_id=entry.entry_id,
                    )
                )
                _LOGGER.info(
                    "Created climate entity for %s - %s",
                    device.name,
                    actuator.name,
                )

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d climate entities", len(entities))
    else:
        _LOGGER.warning("No climate entities found in LXP file")


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
        device,
        actuator,
        entry_id: str,
    ) -> None:
        """Initialize the climate entity."""
        self.coordinator = coordinator
        self.knx_gateway = knx_gateway
        self._device = device
        self._actuator = actuator
        self._entry_id = entry_id

        # Map datapoint roles to addresses
        self._datapoints = {dp.role: dp.address for dp in actuator.datapoints}

        # Set unique ID
        self._attr_unique_id = f"luxor_{device.serial_number}_{actuator.channel}_climate"

        # Set name
        self._attr_name = actuator.name

        # Set device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.serial_number)},
            "name": device.name,
            "manufacturer": "Theben",
            "model": f"H6 Heating Actuator (App ID {device.app_id})",
            "sw_version": device.app_id,
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
                await self.knx_gateway.write_group_address(
                    self._datapoints["Sollwert"], temp_raw
                )
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
