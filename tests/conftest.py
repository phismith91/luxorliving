"""Pytest fixtures for LUXORliving tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.luxor_living.const import (
    CONF_CONNECTION_TYPE,
    CONF_LOG_LEVEL,
    CONF_LXP_FILE,
    CONF_SCAN_INTERVAL,
    CONF_SIMULATION_MODE,
    CONNECTION_TYPE_TUNNELING,
    DEFAULT_LOG_LEVEL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def pytest_configure(config):
    """Disable pytest-socket to allow mock servers in tests.

    Patches pytest_socket.disable_socket to prevent socket blocking.
    This must happen before any test modules are imported.
    """
    try:
        import socket
        import pytest_socket

        # Get the original socket class before pytest_socket patches it
        original_socket = socket.socket

        # Replace pytest_socket's disable_socket function to be a no-op
        def no_op_disable(*args, **kwargs):
            """No-op disable function."""
            pass

        pytest_socket.disable_socket = no_op_disable
        pytest_socket.disable_socket_is_enabled = False

        # Restore the original socket class
        socket.socket = original_socket
    except (ImportError, AttributeError):
        pass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_entry_id",
        title="Test LUXORliving",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password123",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_TUNNELING,
            CONF_SIMULATION_MODE: False,
            CONF_LXP_FILE: "/config/.storage/test.lxp",
        },
        options={
            CONF_SIMULATION_MODE: False,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_LOG_LEVEL: DEFAULT_LOG_LEVEL,
        },
        version=1,
    )


@pytest.fixture
def mock_knx_gateway():
    """Create a mock KNX Gateway."""
    gateway = MagicMock()
    gateway.host = "192.168.1.100"
    gateway.port = 3671
    gateway.username = "admin"
    gateway.connection_type = CONNECTION_TYPE_TUNNELING
    gateway.simulation_mode = False
    gateway.is_connected = MagicMock(return_value=True)
    gateway.async_setup = AsyncMock(return_value=True)
    gateway.async_disconnect = AsyncMock()
    gateway.update_all_entities = AsyncMock()
    gateway.get_all_entities = MagicMock(return_value=[])
    gateway.entity_mapper = MagicMock()
    gateway.entity_mapper.get_entity_overrides = MagicMock(return_value={})
    gateway.entity_mapper.entities = []
    return gateway


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.name = "LUXORliving"
    coordinator.last_update_success = True
    coordinator.last_exception = None
    coordinator.data = []
    coordinator._scan_interval = DEFAULT_SCAN_INTERVAL
    coordinator.async_refresh = AsyncMock()
    return coordinator
