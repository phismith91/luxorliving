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
    """Set up LUXORliving climate devices from a config entry."""
    _LOGGER.info("Setting up LUXORliving climate devices")

    state = entry.runtime_data
    coordinator = state.coordinator
    mapper = state.mapper
    knx_gateway = state.knx_gateway

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
    loop = asyncio.get_running_loop()
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
        self._entry_id = entry_id

        # Map datapoint addresses by role (MappedEntity.datapoints is already dict[str, int])
        self._datapoints = mapped_entity.datapoints

        # Track cooling capability (based on UmschaltenHeitzenKühlen datapoint presence)
        self._cooling_capable = mapped_entity.cooling_capable
        self._attr_hvac_modes = (
            [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF]
            if self._cooling_capable
            else [HVACMode.HEAT, HVACMode.OFF]
        )

        # Set unique ID
        self._attr_unique_id = mapped_entity.unique_id

        # Set name
        self._attr_name = mapped_entity.name

        # Set device info
        device_id = mapped_entity.device_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": mapped_entity.device_name,
            "manufacturer": "Theben",
            "model": "LUXORliving",
        }

        # Initialize state
        self._attr_current_temperature = None
        self._attr_target_temperature = None
        self._attr_hvac_mode = HVACMode.HEAT
        self._window_contact_open = False

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

    @property
    def _target_dp_key(self) -> str:
        """Return the preferred setpoint datapoint key.

        Priority: StatusSollwert (actuator) > status@Sollwert (RTR sensor) > Sollwert.
        """
        if "StatusSollwert" in self._datapoints:
            return "StatusSollwert"
        if "status@Sollwert" in self._datapoints:
            return "status@Sollwert"
        return "Sollwert"

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Register KNX listeners — must run here, not in __init__, so that
        # async_write_ha_state() is safe and __init__ stays thread-safe
        # (it runs in an executor via run_in_executor).
        if "Istwert" in self._datapoints:
            addr = self._datapoints["Istwert"]
            self.knx_gateway.register_listener(addr, self._handle_temperature_update)
            self._knx_listener_refs.append((addr, self._handle_temperature_update))

        if self._target_dp_key in self._datapoints:
            addr = self._datapoints[self._target_dp_key]
            self.knx_gateway.register_listener(addr, self._handle_setpoint_update)
            self._knx_listener_refs.append((addr, self._handle_setpoint_update))

        if "WindowContact" in self._datapoints:
            addr = self._datapoints["WindowContact"]
            self.knx_gateway.register_listener(addr, self._handle_window_contact_update)
            self._knx_listener_refs.append((addr, self._handle_window_contact_update))

        if "UmschaltenHeitzenKühlen" in self._datapoints:
            addr = self._datapoints["UmschaltenHeitzenKühlen"]
            self.knx_gateway.register_listener(addr, self._handle_mode_switch_update)
            self._knx_listener_refs.append((addr, self._handle_mode_switch_update))

        # Request initial temperature state — wait up to 5s for KNX connection
        if self.knx_gateway.connected:
            await self._update_temperature()

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity is removed from hass."""
        for addr, cb in self._knx_listener_refs:
            self.knx_gateway.unregister_listener(addr, cb)
        self._knx_listener_refs.clear()

    def _handle_temperature_update(self, group_address: str, value: Any) -> None:
        """Handle actual temperature update received via KNX telegram (DPT 9.001 float)."""
        if isinstance(value, (int, float)):
            self._attr_current_temperature = float(value)
            self.async_write_ha_state()

    def _handle_setpoint_update(self, group_address: str, value: Any) -> None:
        """Handle target setpoint update received via KNX telegram (DPT 9.001 float)."""
        if isinstance(value, (int, float)):
            self._attr_target_temperature = float(value)
            self.async_write_ha_state()

    def _handle_window_contact_update(self, group_address: str, value: Any) -> None:
        """Handle window contact update received via KNX telegram."""
        if value is not None:
            self._window_contact_open = bool(value)
            self.async_write_ha_state()

    def _handle_mode_switch_update(self, group_address: str, value: Any) -> None:
        """Handle heating/cooling mode-switch telegram received via KNX.

        UmschaltenHeitzenKühlen is a shared GA — one physical switch drives all
        H6 devices on the bus at once, so every H6 entity must listen for it,
        not just the one that sent the command. OFF is a local-only pseudo
        state (not represented on the bus), so it's never overwritten here.
        """
        if value is None or self._attr_hvac_mode == HVACMode.OFF:
            return
        self._attr_hvac_mode = HVACMode.HEAT if value else HVACMode.COOL
        self.async_write_ha_state()

    async def _update_temperature(self) -> None:
        """Request current and target temperatures from KNX bus."""
        if "Istwert" in self._datapoints:
            await self.knx_gateway.async_read_group_address(self._datapoints["Istwert"])

        if self._target_dp_key in self._datapoints:
            await self.knx_gateway.async_read_group_address(self._datapoints[self._target_dp_key])

        if "WindowContact" in self._datapoints:
            await self.knx_gateway.async_read_group_address(self._datapoints["WindowContact"])

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        self._raise_if_unavailable()
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        try:
            # Write to Sollwert address using DPT 9.001 (2-byte float)
            if "Sollwert" in self._datapoints:
                await self.knx_gateway.async_send_telegram(
                    self._datapoints["Sollwert"], float(temperature), "temperature"
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
        self._raise_if_unavailable()
        if hvac_mode not in self._attr_hvac_modes:
            _LOGGER.warning("Unsupported HVAC mode: %s", hvac_mode)
            return

        self._attr_hvac_mode = hvac_mode

        # For H6 there is no explicit on/off control: OFF lowers the bus setpoint
        # to minimum. We remember the user's setpoint (without clobbering
        # _attr_target_temperature) so HEAT can restore it instead of min_temp.
        if hvac_mode == HVACMode.OFF:
            if self._attr_target_temperature is not None:
                self._setpoint_before_off = self._attr_target_temperature
            if "Sollwert" in self._datapoints:
                await self.knx_gateway.async_send_telegram(
                    self._datapoints["Sollwert"], float(self._attr_min_temp), "temperature"
                )
        elif hvac_mode == HVACMode.HEAT:
            temp = getattr(self, "_setpoint_before_off", None) or self._attr_target_temperature
            await self.async_set_temperature(temperature=temp or 20.0)
            if self._cooling_capable and "UmschaltenHeitzenKühlen" in self._datapoints:
                await self.knx_gateway.async_send_telegram(
                    self._datapoints["UmschaltenHeitzenKühlen"], 1, "binary"
                )
        elif hvac_mode == HVACMode.COOL:
            if self._cooling_capable and "UmschaltenHeitzenKühlen" in self._datapoints:
                await self.knx_gateway.async_send_telegram(
                    self._datapoints["UmschaltenHeitzenKühlen"], 0, "binary"
                )

        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the entity."""
        await self._update_temperature()
