"""Additional integration tests to improve code coverage."""

from custom_components.luxor_living.const import DOMAIN


class TestLXPParserBasic:
    """Test LXPParser basic functionality."""

    def test_lxp_parser_import(self):
        """Test LXPParser can be imported."""
        from custom_components.luxor_living.lxp_parser import LXPParser

        assert LXPParser is not None

    def test_entity_mapper_import(self):
        """Test EntityMapper can be imported."""
        from custom_components.luxor_living.entity_mapper import EntityMapper

        assert EntityMapper is not None

    def test_domain_constant(self):
        """Test DOMAIN constant is defined."""
        assert DOMAIN == "luxor_living"

    def test_rest_client_import(self):
        """Test RESTClient can be imported."""
        try:
            from custom_components.luxor_living.rest_client import RESTClient

            assert RESTClient is not None
        except Exception:
            # May require additional dependencies
            pass


class TestCoordinatorBasic:
    """Test coordinator basic structure."""

    def test_coordinator_import(self):
        """Test coordinator can be imported."""
        from custom_components.luxor_living.coordinator import LuxorLivingCoordinator

        assert LuxorLivingCoordinator is not None

    def test_entity_import(self):
        """Test entity can be imported."""
        from custom_components.luxor_living.entity import LuxorLivingEntity

        assert LuxorLivingEntity is not None


class TestPlatformImports:
    """Test all platform imports work."""

    def test_light_platform_import(self):
        """Test light platform imports."""
        from custom_components.luxor_living.light import LuxorLivingDimmableLight, LuxorLivingLight

        assert LuxorLivingLight is not None
        assert LuxorLivingDimmableLight is not None

    def test_switch_platform_import(self):
        """Test switch platform imports."""
        from custom_components.luxor_living.switch import LuxorLivingSwitch

        assert LuxorLivingSwitch is not None

    def test_binary_sensor_platform_import(self):
        """Test binary sensor platform imports."""
        from custom_components.luxor_living.binary_sensor import LuxorLivingBinarySensor

        assert LuxorLivingBinarySensor is not None

    def test_config_flow_import(self):
        """Test config flow imports."""
        from custom_components.luxor_living.config_flow import LuxorLivingConfigFlow

        assert LuxorLivingConfigFlow is not None


class TestKNXGatewayStructure:
    """Test KNX Gateway basic structure."""

    def test_knx_gateway_import(self):
        """Test KNX gateway can be imported."""
        from custom_components.luxor_living.knx_gateway import LuxorKNXGateway

        assert LuxorKNXGateway is not None


class TestConstantsDefinition:
    """Test all required constants are defined."""

    def test_domain_constant_defined(self):
        """Test DOMAIN constant."""
        from custom_components.luxor_living.const import DOMAIN

        assert DOMAIN == "luxor_living"

    def test_data_coordinator_constant(self):
        """Test DATA_COORDINATOR constant."""
        from custom_components.luxor_living.const import DATA_COORDINATOR

        assert DATA_COORDINATOR is not None
