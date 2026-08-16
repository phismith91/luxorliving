"""Tests for H6 cooling mode support."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.const import Platform
from homeassistant.exceptions import HomeAssistantError

from custom_components.luxor_living.entity_mapper import EntityMapper
from custom_components.luxor_living.lxp_parser import (
    LXPActuator,
    LXPDatapoint,
    LXPDevice,
    LXPProject,
)


class TestH6CoolingModeDetection:
    """Test cooling mode detection in entity mapper."""

    def test_h6_with_cooling_datapoint_detected(self):
        """H6 actuator with UmschaltenHeitzenKühlen datapoint should be marked cooling_capable."""
        project = LXPProject(
            name="Test",
            gateway_address="127.0.0.1",
            gateway_port=3671,
            devices=[
                LXPDevice(
                    name="511 H6",
                    serial_number="test_h6",
                    address="9.0.28",
                    app_id="18502",
                    id="test_h6_id",
                    actuators=[
                        LXPActuator(
                            name="Heating Actuator",
                            channel=0,
                            id="test_actuator_1",
                            on_icon="Default_ON",
                            off_icon="Default_OFF",
                            use_case=1,
                            parameters={"heizungsart": "102"},
                            datapoints=[
                                LXPDatapoint(address=100, role="Sollwert", id="dp1"),
                                LXPDatapoint(address=101, role="Istwert", id="dp2"),
                                LXPDatapoint(address=102, role="UmschaltenHeitzenKühlen", id="dp3"),
                            ],
                        ),
                    ],
                    sensors=[],
                ),
            ],
        )

        mapper = EntityMapper(project)
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)

        assert len(climate_entities) == 1
        entity = climate_entities[0]
        assert entity.cooling_capable is True
        assert "UmschaltenHeitzenKühlen" in entity.datapoints

    def test_h6_without_cooling_datapoint(self):
        """H6 actuator without UmschaltenHeitzenKühlen should not be cooling_capable."""
        project = LXPProject(
            name="Test",
            gateway_address="127.0.0.1",
            gateway_port=3671,
            devices=[
                LXPDevice(
                    name="511 H6",
                    serial_number="test_h6",
                    address="9.0.28",
                    app_id="18502",
                    id="test_h6_id",
                    actuators=[
                        LXPActuator(
                            name="Heating Actuator",
                            channel=0,
                            id="test_actuator_1",
                            on_icon="Default_ON",
                            off_icon="Default_OFF",
                            use_case=1,
                            parameters={"heizungsart": "102"},
                            datapoints=[
                                LXPDatapoint(address=100, role="Sollwert", id="dp1"),
                                LXPDatapoint(address=101, role="Istwert", id="dp2"),
                            ],
                        ),
                    ],
                    sensors=[],
                ),
            ],
        )

        mapper = EntityMapper(project)
        climate_entities = mapper.get_entities_by_platform(Platform.CLIMATE)

        assert len(climate_entities) == 1
        entity = climate_entities[0]
        assert entity.cooling_capable is False


class TestClimateHVACModes:
    """Test climate entity HVAC modes based on cooling capability."""

    @pytest.mark.asyncio
    async def test_climate_hvac_modes_with_cooling(self, hass, mock_coordinator, mock_knx_gateway):
        """Climate entity should have HEAT, COOL, OFF modes when cooling_capable=True."""
        from custom_components.luxor_living.climate import LuxorClimate
        from custom_components.luxor_living.mapped_entity import MappedEntity

        # Create a cooling-capable mapped entity
        mapped_entity = MappedEntity(
            platform=Platform.CLIMATE,
            unique_id="test_climate_1",
            name="Test Climate",
            device_name="511 H6",
            device_id="test_h6_id",
            entity_type="climate",
            datapoints={
                "Sollwert": 100,
                "Istwert": 101,
                "UmschaltenHeitzenKühlen": 102,
            },
            attributes={},
            parameters={"heizungsart": "102"},
            cooling_capable=True,
        )

        climate = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=mapped_entity,
            entry_id="test_entry",
        )

        assert HVACMode.HEAT in climate._attr_hvac_modes
        assert HVACMode.COOL in climate._attr_hvac_modes
        assert HVACMode.OFF in climate._attr_hvac_modes

    @pytest.mark.asyncio
    async def test_climate_hvac_modes_without_cooling(
        self, hass, mock_coordinator, mock_knx_gateway
    ):
        """Climate entity should have only HEAT, OFF modes when cooling_capable=False."""
        from custom_components.luxor_living.climate import LuxorClimate
        from custom_components.luxor_living.mapped_entity import MappedEntity

        # Create a non-cooling mapped entity
        mapped_entity = MappedEntity(
            platform=Platform.CLIMATE,
            unique_id="test_climate_2",
            name="Test Climate",
            device_name="511 H6",
            device_id="test_h6_id",
            entity_type="climate",
            datapoints={
                "Sollwert": 100,
                "Istwert": 101,
            },
            attributes={},
            parameters={"heizungsart": "102"},
            cooling_capable=False,
        )

        climate = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=mapped_entity,
            entry_id="test_entry",
        )

        assert HVACMode.HEAT in climate._attr_hvac_modes
        assert HVACMode.COOL not in climate._attr_hvac_modes
        assert HVACMode.OFF in climate._attr_hvac_modes

    @pytest.mark.asyncio
    async def test_set_hvac_mode_cool(self, hass, mock_coordinator, mock_knx_gateway):
        """Setting HVAC mode to COOL should send binary telegram to mode-switch."""
        from unittest.mock import AsyncMock

        from custom_components.luxor_living.climate import LuxorClimate
        from custom_components.luxor_living.mapped_entity import MappedEntity

        mock_knx_gateway.async_send_telegram = AsyncMock()

        mapped_entity = MappedEntity(
            platform=Platform.CLIMATE,
            unique_id="test_climate_3",
            name="Test Climate",
            device_name="511 H6",
            device_id="test_h6_id",
            entity_type="climate",
            datapoints={
                "Sollwert": 100,
                "Istwert": 101,
                "UmschaltenHeitzenKühlen": 102,
            },
            attributes={},
            parameters={"heizungsart": "102"},
            cooling_capable=True,
        )

        climate = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=mapped_entity,
            entry_id="test_entry",
        )
        climate.async_write_ha_state = lambda: None  # Mock write_ha_state

        await climate.async_set_hvac_mode(HVACMode.COOL)

        # Verify binary telegram sent to mode-switch with 0 (cooling)
        mock_knx_gateway.async_send_telegram.assert_called_with(102, 0, "binary")

    @pytest.mark.asyncio
    async def test_set_hvac_mode_heat_with_cooling_capable(
        self, hass, mock_coordinator, mock_knx_gateway
    ):
        """Setting HVAC mode to HEAT should send binary telegram to mode-switch."""
        from unittest.mock import AsyncMock

        from custom_components.luxor_living.climate import LuxorClimate
        from custom_components.luxor_living.mapped_entity import MappedEntity

        mock_knx_gateway.async_send_telegram = AsyncMock()

        mapped_entity = MappedEntity(
            platform=Platform.CLIMATE,
            unique_id="test_climate_4",
            name="Test Climate",
            device_name="511 H6",
            device_id="test_h6_id",
            entity_type="climate",
            datapoints={
                "Sollwert": 100,
                "Istwert": 101,
                "UmschaltenHeitzenKühlen": 102,
            },
            attributes={},
            parameters={"heizungsart": "102"},
            cooling_capable=True,
        )

        climate = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=mapped_entity,
            entry_id="test_entry",
        )
        climate.async_write_ha_state = lambda: None
        climate._attr_target_temperature = 20.0

        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Verify binary telegram sent to mode-switch with 1 (heating)
        mock_knx_gateway.async_send_telegram.assert_called_with(102, 1, "binary")


class TestModeSwitchListenerSync:
    """Test that H6 entities stay in sync via the shared mode-switch GA.

    UmschaltenHeitzenKühlen is one physical switch driving all H6 devices at
    once — every H6 entity must listen for it, not just the one commanded
    from HA, otherwise other entities show stale heat/cool state (#141).
    """

    def _make_cooling_entity(self, mock_coordinator, mock_knx_gateway, unique_id="test_climate"):
        from custom_components.luxor_living.climate import LuxorClimate
        from custom_components.luxor_living.mapped_entity import MappedEntity

        mapped_entity = MappedEntity(
            platform=Platform.CLIMATE,
            unique_id=unique_id,
            name="Test Climate",
            device_name="511 H6",
            device_id="test_h6_id",
            entity_type="climate",
            datapoints={"Sollwert": 100, "Istwert": 101, "UmschaltenHeitzenKühlen": 102},
            attributes={},
            parameters={"heizungsart": "102"},
            cooling_capable=True,
        )
        entity = LuxorClimate(
            coordinator=mock_coordinator,
            knx_gateway=mock_knx_gateway,
            mapped_entity=mapped_entity,
            entry_id="test_entry",
        )
        entity.async_write_ha_state = lambda: None
        return entity

    @pytest.mark.asyncio
    async def test_mode_switch_listener_registered(self, hass, mock_coordinator, mock_knx_gateway):
        """async_added_to_hass must register a listener on the mode-switch GA."""
        mock_knx_gateway.connected = False  # skip initial bus read, only check registration
        entity = self._make_cooling_entity(mock_coordinator, mock_knx_gateway)

        await entity.async_added_to_hass()

        registered = [c[0][0] for c in mock_knx_gateway.register_listener.call_args_list]
        assert 102 in registered

    def test_incoming_telegram_cool_updates_other_entity(self, mock_coordinator, mock_knx_gateway):
        """A mode-switch telegram from another device's command must flip this entity to COOL."""
        entity = self._make_cooling_entity(mock_coordinator, mock_knx_gateway)
        entity._attr_hvac_mode = HVACMode.HEAT

        entity._handle_mode_switch_update(102, 0)

        assert entity.hvac_mode == HVACMode.COOL

    def test_incoming_telegram_heat_updates_other_entity(self, mock_coordinator, mock_knx_gateway):
        """A mode-switch telegram value 1 must flip this entity to HEAT."""
        entity = self._make_cooling_entity(mock_coordinator, mock_knx_gateway)
        entity._attr_hvac_mode = HVACMode.COOL

        entity._handle_mode_switch_update(102, 1)

        assert entity.hvac_mode == HVACMode.HEAT

    def test_incoming_telegram_does_not_override_off(self, mock_coordinator, mock_knx_gateway):
        """OFF is a local-only pseudo state and must not be clobbered by bus telegrams."""
        entity = self._make_cooling_entity(mock_coordinator, mock_knx_gateway)
        entity._attr_hvac_mode = HVACMode.OFF

        entity._handle_mode_switch_update(102, 0)

        assert entity.hvac_mode == HVACMode.OFF

    @pytest.mark.asyncio
    async def test_hvac_mode_from_ha_syncs_sibling_entity(self, hass, mock_coordinator):
        """Commanding one H6 from HA must update sibling H6 entities too (#141).

        Regression test for the gap that let PR #190 ship broken: prior tests
        called _handle_mode_switch_update() directly, which only proves the
        listener callback works — never that async_set_hvac_mode() (the real
        HA-triggered path) actually reaches it. A real xknx outgoing telegram
        is never redelivered as incoming, so the fan-out must happen via
        knx_gateway.process_incoming_value(), exercised here against a real
        LuxorKNXGateway instance (not a MagicMock) so the listener registry
        and dispatch are genuinely under test, not stubbed away.
        """
        from custom_components.luxor_living.knx_gateway import LuxorKNXGateway

        gateway = LuxorKNXGateway(
            hass=hass,
            host="192.168.1.100",
            port=3671,
            username="admin",
            password="secret",
            simulation_mode=False,
        )
        gateway.async_send_telegram = AsyncMock(return_value=True)
        gateway._connected = True

        salon = self._make_cooling_entity(mock_coordinator, gateway, unique_id="salon")
        bathroom = self._make_cooling_entity(mock_coordinator, gateway, unique_id="bathroom")
        salon._attr_hvac_mode = HVACMode.COOL
        bathroom._attr_hvac_mode = HVACMode.COOL
        await salon.async_added_to_hass()
        await bathroom.async_added_to_hass()

        await salon.async_set_hvac_mode(HVACMode.HEAT)
        await asyncio.sleep(0)  # let the call_soon_threadsafe-scheduled listener fire

        assert bathroom.hvac_mode == HVACMode.HEAT
