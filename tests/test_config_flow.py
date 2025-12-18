"""Tests for config flow."""
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

import pytest

from custom_components.luxor_living.const import (
    DOMAIN,
    CONF_LXP_FILE,
    CONF_CONNECTION_TYPE,
    CONF_SIMULATION_MODE,
    CONNECTION_TYPE_TUNNELING,
    CONNECTION_TYPE_ROUTING,
)
from custom_components.luxor_living.config_flow import LuxorLivingConfigFlow


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
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.config.path = MagicMock(return_value="/config")
    return hass


class TestLuxorLivingConfigFlow:
    """Test LuxorLiving config flow."""

    @pytest.mark.asyncio
    async def test_user_step_show_form(self, mock_hass):
        """Test showing user form with file selector."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        
        result = await flow.async_step_user()
        
        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert CONF_LXP_FILE in result["data_schema"].schema
        # FileSelector sollte vorhanden sein
        schema_key = list(result["data_schema"].schema.keys())[0]
        assert str(schema_key) == CONF_LXP_FILE

    @pytest.mark.asyncio
    async def test_user_step_file_not_found(self, mock_hass):
        """Test user step with non-existent file."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        
        with patch("pathlib.Path.exists", return_value=False):
            result = await flow.async_step_user({CONF_LXP_FILE: "/nonexistent.lxp"})
        
        assert result["type"] == "form"
        assert result["errors"]["base"] == "file_not_found"

    @pytest.mark.asyncio
    async def test_user_step_valid_file(self, mock_hass, mock_lxp_parser):
        """Test user step with valid LXP file."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                result = await flow.async_step_user({CONF_LXP_FILE: "/config/test.lxp"})
        
        assert result["type"] == "form"
        assert result["step_id"] == "gateway"
        assert flow._lxp_file == "/config/test.lxp"
        assert flow._project_name == "Test Project"

    @pytest.mark.asyncio
    async def test_user_step_invalid_lxp(self, mock_hass, mock_lxp_parser):
        """Test user step with invalid LXP file."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        
        # Make parser raise exception
        mock_lxp_parser.return_value.parse.side_effect = Exception("Invalid XML")
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                result = await flow.async_step_user({CONF_LXP_FILE: "/test.lxp"})
        
        assert result["type"] == "form"
        assert result["errors"]["base"] == "invalid_lxp"

    @pytest.mark.asyncio
    async def test_gateway_step_show_form(self, mock_hass, mock_lxp_parser):
        """Test showing gateway form."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        flow._lxp_file = "/test.lxp"
        flow._project_name = "Test Project"
        
        result = await flow.async_step_gateway()
        
        assert result["type"] == "form"
        assert result["step_id"] == "gateway"
        assert "host" in result["data_schema"].schema

    @pytest.mark.asyncio
    async def test_gateway_step_create_entry_tunneling(self, mock_hass, mock_lxp_parser):
        """Test creating entry with tunneling mode."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        flow._lxp_file = "/test.lxp"
        flow._project_name = "Test Project"
        
        result = await flow.async_step_gateway({
            "host": "192.168.1.3",
            "port": 3671,
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_TUNNELING,
            CONF_SIMULATION_MODE: False,
        })
        
        assert result["type"] == "create_entry"
        assert result["title"] == "LUXORliving (Test Project)"
        assert result["data"]["host"] == "192.168.1.3"
        assert result["data"][CONF_CONNECTION_TYPE] == CONNECTION_TYPE_TUNNELING

    @pytest.mark.asyncio
    async def test_gateway_step_create_entry_routing(self, mock_hass, mock_lxp_parser):
        """Test creating entry with routing mode."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        flow._lxp_file = "/test.lxp"
        flow._project_name = "Test Project"
        
        result = await flow.async_step_gateway({
            "host": "224.0.23.12",
            "port": 3671,
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_ROUTING,
            CONF_SIMULATION_MODE: False,
        })
        
        assert result["type"] == "create_entry"
        assert result["data"][CONF_CONNECTION_TYPE] == CONNECTION_TYPE_ROUTING

    @pytest.mark.asyncio
    async def test_gateway_step_simulation_mode(self, mock_hass, mock_lxp_parser):
        """Test creating entry with simulation mode."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        flow._lxp_file = "/test.lxp"
        flow._project_name = "Test Project"
        
        result = await flow.async_step_gateway({
            "host": "localhost",
            "port": 3671,
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_TUNNELING,
            CONF_SIMULATION_MODE: True,
        })
        
        assert result["type"] == "create_entry"
        assert result["data"][CONF_SIMULATION_MODE] is True

    @pytest.mark.asyncio
    async def test_full_flow_with_file_selector(self, mock_hass, mock_lxp_parser):
        """Test complete flow from file selection to entry creation."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        
        # Step 1: Show user form
        result = await flow.async_step_user()
        assert result["type"] == "form"
        assert result["step_id"] == "user"
        
        # Step 2: Submit file selection
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                result = await flow.async_step_user({
                    CONF_LXP_FILE: "/config/luxor_living/project.lxp"
                })
        
        assert result["type"] == "form"
        assert result["step_id"] == "gateway"
        
        # Step 3: Submit gateway config
        result = await flow.async_step_gateway({
            "host": "192.168.1.3",
            "port": 3671,
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_TUNNELING,
            CONF_SIMULATION_MODE: False,
        })
        
        assert result["type"] == "create_entry"
        assert result["title"] == "LUXORliving (Test Project)"
        assert result["data"][CONF_LXP_FILE] == "/config/luxor_living/project.lxp"
