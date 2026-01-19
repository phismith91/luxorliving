"""Pytest fixtures for LUXORliving tests."""

import pytest


# Register custom markers in pytest hook (alternative to pytest.ini)
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "smoke: quick smoke tests for PRs")
    config.addinivalue_line("markers", "integration: medium-length integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end style tests")
    config.addinivalue_line("markers", "enable_socket: marks tests that require socket access")


# Disable pytest-socket immediately to allow aiohttp mock servers
# Must be done before any test modules are imported
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Some CI setups install the `pytest-socket` plugin which blocks socket.socket by default.
# Attempt to import and disable it if it's available. Use a try/except so this works
# regardless of plugin import order.
try:
    import pytest_socket  # type: ignore

    # Prevent pytest-socket from blocking sockets used by aiohttp TestServer
    pytest_socket.disable_socket_is_enabled = False

    # Ensure localhost connections are allowed (different pytest-socket versions
    # expose different helper names; try common variants).
    try:
        pytest_socket.socket_allow_hosts("127.0.0.1")
    except Exception:
        try:
            pytest_socket.allow_hosts("127.0.0.1")
        except Exception:
            # Last-resort: call enable_socket() if available
            try:
                pytest_socket.enable_socket()
            except Exception:
                # If all fail, continue — disabling the flag above may suffice
                pass
except Exception:
    # Plugin not available or import failed — nothing to do
    pass

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
from custom_components.luxor_living.integration_state import _integration_states


@pytest.fixture(autouse=True)
def cleanup_integration_state():
    """Clean up global integration state registry between tests."""
    _integration_states.clear()
    yield
    _integration_states.clear()


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
