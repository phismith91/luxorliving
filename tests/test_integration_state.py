"""Tests for IntegrationState type-safe state management."""

from unittest.mock import Mock

import pytest

from custom_components.luxor_living.integration_state import IntegrationState


@pytest.fixture
def mock_mapper():
    """Mock EntityMapper."""
    mapper = Mock()
    mapper.entities = [Mock(), Mock(), Mock()]  # 3 entities
    return mapper


@pytest.fixture
def mock_config():
    """Mock config dict."""
    return {"host": "192.168.1.3", "port": 3671}


@pytest.fixture
def mock_overrides():
    """Mock overrides dict."""
    return {"include_unaffected": False}


@pytest.fixture
def mock_knx_gateway():
    """Mock KNX Gateway."""
    return Mock()


@pytest.fixture
def mock_coordinator():
    """Mock Coordinator."""
    return Mock()


class TestIntegrationState:
    """Test IntegrationState dataclass."""

    def test_create_minimal_state(self, mock_mapper, mock_config, mock_overrides):
        """Test creating state with minimal required fields."""
        state = IntegrationState(
            mapper=mock_mapper,
            config=mock_config,
            overrides=mock_overrides,
        )

        assert state.mapper is mock_mapper
        assert state.config is mock_config
        assert state.overrides is mock_overrides
        assert state.knx_gateway is None
        assert state.coordinator is None
        assert state.entry is None

    def test_create_complete_state(
        self, mock_mapper, mock_config, mock_overrides, mock_knx_gateway, mock_coordinator
    ):
        """Test creating state with all fields."""
        mock_entry = Mock()
        state = IntegrationState(
            mapper=mock_mapper,
            config=mock_config,
            overrides=mock_overrides,
            knx_gateway=mock_knx_gateway,
            coordinator=mock_coordinator,
            entry=mock_entry,
        )

        assert state.mapper is mock_mapper
        assert state.config is mock_config
        assert state.overrides is mock_overrides
        assert state.knx_gateway is mock_knx_gateway
        assert state.coordinator is mock_coordinator
        assert state.entry is mock_entry

    def test_validation_missing_mapper(self, mock_config, mock_overrides):
        """Test validation fails when mapper is None."""
        with pytest.raises(ValueError, match="requires mapper"):
            IntegrationState(
                mapper=None,
                config=mock_config,
                overrides=mock_overrides,
            )

    def test_validation_missing_config(self, mock_mapper, mock_overrides):
        """Test validation fails when config is None."""
        with pytest.raises(ValueError, match="requires config"):
            IntegrationState(
                mapper=mock_mapper,
                config=None,
                overrides=mock_overrides,
            )

    def test_is_ready_false(self, mock_mapper, mock_config, mock_overrides):
        """Test is_ready returns False when not fully initialized."""
        state = IntegrationState(
            mapper=mock_mapper,
            config=mock_config,
            overrides=mock_overrides,
        )

        assert not state.is_ready

    def test_is_ready_true(
        self, mock_mapper, mock_config, mock_overrides, mock_knx_gateway, mock_coordinator
    ):
        """Test is_ready returns True when fully initialized."""
        state = IntegrationState(
            mapper=mock_mapper,
            config=mock_config,
            overrides=mock_overrides,
            knx_gateway=mock_knx_gateway,
            coordinator=mock_coordinator,
        )

        assert state.is_ready

    def test_get_entity_count(self, mock_mapper, mock_config, mock_overrides):
        """Test get_entity_count returns correct count."""
        state = IntegrationState(
            mapper=mock_mapper,
            config=mock_config,
            overrides=mock_overrides,
        )

        assert state.get_entity_count() == 3

    def test_get_gateway_or_raise_success(
        self, mock_mapper, mock_config, mock_overrides, mock_knx_gateway
    ):
        """Test get_gateway_or_raise returns gateway when initialized."""
        state = IntegrationState(
            mapper=mock_mapper,
            config=mock_config,
            overrides=mock_overrides,
            knx_gateway=mock_knx_gateway,
        )

        assert state.get_gateway_or_raise() is mock_knx_gateway

    def test_get_gateway_or_raise_fails(self, mock_mapper, mock_config, mock_overrides):
        """Test get_gateway_or_raise raises when gateway not initialized."""
        state = IntegrationState(
            mapper=mock_mapper,
            config=mock_config,
            overrides=mock_overrides,
        )

        with pytest.raises(RuntimeError, match="Gateway not initialized"):
            state.get_gateway_or_raise()

    def test_get_coordinator_or_raise_success(
        self, mock_mapper, mock_config, mock_overrides, mock_coordinator
    ):
        """Test get_coordinator_or_raise returns coordinator when initialized."""
        state = IntegrationState(
            mapper=mock_mapper,
            config=mock_config,
            overrides=mock_overrides,
            coordinator=mock_coordinator,
        )

        assert state.get_coordinator_or_raise() is mock_coordinator

    def test_get_coordinator_or_raise_fails(self, mock_mapper, mock_config, mock_overrides):
        """Test get_coordinator_or_raise raises when coordinator not initialized."""
        state = IntegrationState(
            mapper=mock_mapper,
            config=mock_config,
            overrides=mock_overrides,
        )

        with pytest.raises(RuntimeError, match="Coordinator not initialized"):
            state.get_coordinator_or_raise()
