"""Tests for H6 cooling mode support."""

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
