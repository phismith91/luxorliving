"""Tests for config flow."""
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.luxor_living.const import (
    DOMAIN,
    CONF_LXP_FILE,
    CONF_CONNECTION_TYPE,
    CONF_SIMULATION_MODE,
    CONNECTION_TYPE_TUNNELING,
)


@pytest.fixture
def mock_lxp_parser():
    """Mock LXP Parser."""
    with patch("custom_components.luxor_living.config_flow.LXPParser") as mock:
        parser_instance = MagicMock()
        parser_instance.parse = AsyncMock()
        
        # Mock project
        mock_project = MagicMock()
        mock_project.name = "Test Project"
        parser_instance.parse.return_value = mock_project
        
        mock.return_value = parser_instance
        yield mock


@pytest.fixture
def mock_setup_entry():
    """Mock setup entry."""
    with patch(
        "custom_components.luxor_living.async_setup_entry", return_value=True
    ) as mock:
        yield mock


async def test_user_flow_success(hass: HomeAssistant, mock_lxp_parser, mock_setup_entry):
    """Test successful user flow."""
    # Start user flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    
    # Submit LXP file path
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.is_file", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_LXP_FILE: "/config/test.lxp"},
            )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "gateway"
    
    # Submit gateway config
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "192.168.1.3",
            "port": 3671,
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_TUNNELING,
            CONF_SIMULATION_MODE: False,
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "LUXORliving (Test Project)"
    assert result["data"][CONF_LXP_FILE] == "/config/test.lxp"
    assert result["data"]["host"] == "192.168.1.3"
    assert result["data"]["port"] == 3671


async def test_user_flow_file_not_found(hass: HomeAssistant):
    """Test user flow with file not found error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Submit non-existent file
    with patch("pathlib.Path.exists", return_value=False):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_LXP_FILE: "/config/nonexistent.lxp"},
        )
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "file_not_found"


async def test_user_flow_invalid_lxp(hass: HomeAssistant, mock_lxp_parser):
    """Test user flow with invalid LXP file."""
    # Make parser raise exception
    mock_lxp_parser.return_value.parse.side_effect = Exception("Invalid XML")
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.is_file", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_LXP_FILE: "/config/invalid.lxp"},
            )
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_lxp"


async def test_gateway_step_with_routing(hass: HomeAssistant, mock_lxp_parser, mock_setup_entry):
    """Test gateway step with routing mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Submit LXP file
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.is_file", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_LXP_FILE: "/config/test.lxp"},
            )
    
    # Submit gateway with routing mode
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "224.0.23.12",
            "port": 3671,
            CONF_CONNECTION_TYPE: "routing",
            CONF_SIMULATION_MODE: False,
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_CONNECTION_TYPE] == "routing"


async def test_gateway_step_with_simulation(hass: HomeAssistant, mock_lxp_parser, mock_setup_entry):
    """Test gateway step with simulation mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Submit LXP file
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.is_file", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_LXP_FILE: "/config/test.lxp"},
            )
    
    # Submit gateway with simulation mode
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "localhost",
            "port": 3671,
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_TUNNELING,
            CONF_SIMULATION_MODE: True,
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SIMULATION_MODE] is True
