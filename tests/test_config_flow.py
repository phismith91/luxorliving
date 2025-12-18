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


class TestLuxorLivingConfigFlow:
    """Test LuxorLiving config flow."""

    @pytest.mark.asyncio
    async def test_user_step_show_form(self):
        """Test showing user form."""
        flow = LuxorLivingConfigFlow()
        flow.hass = MagicMock()
        
        result = await flow.async_step_user()
        
        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert CONF_LXP_FILE in result["data_schema"].schema

    @pytest.mark.asyncio
    async def test_user_step_file_not_found(self):
        """Test user step with non-existent file."""
        flow = LuxorLivingConfigFlow()
        flow.hass = MagicMock()
        
        with patch("pathlib.Path.exists", return_value=False):
            result = await flow.async_step_user({CONF_LXP_FILE: "/nonexistent.lxp"})
        
        assert result["type"] == "form"
        assert result["errors"]["base"] == "file_not_found"

    @pytest.mark.asyncio
    async def test_user_step_invalid_lxp(self, mock_lxp_parser):
        """Test user step with invalid LXP file."""
        flow = LuxorLivingConfigFlow()
        flow.hass = MagicMock()
        
        # Make parser raise exception
        mock_lxp_parser.return_value.parse.side_effect = Exception("Invalid XML")
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                result = await flow.async_step_user({CONF_LXP_FILE: "/test.lxp"})
        
        assert result["type"] == "form"
        assert result["errors"]["base"] == "invalid_lxp"

    @pytest.mark.asyncio
    async def test_gateway_step_show_form(self, mock_lxp_parser):
        """Test showing gateway form."""
        flow = LuxorLivingConfigFlow()
        flow.hass = MagicMock()
        flow._lxp_file = "/test.lxp"
        flow._project_name = "Test Project"
        
        result = await flow.async_step_gateway()
        
        assert result["type"] == "form"
        assert result["step_id"] == "gateway"
        assert "host" in result["data_schema"].schema

    @pytest.mark.asyncio
    async def test_gateway_step_create_entry_tunneling(self, mock_lxp_parser):
        """Test creating entry with tunneling mode."""
        flow = LuxorLivingConfigFlow()
        flow.hass = MagicMock()
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
    async def test_gateway_step_create_entry_routing(self, mock_lxp_parser):
        """Test creating entry with routing mode."""
        flow = LuxorLivingConfigFlow()
        flow.hass = MagicMock()
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
    async def test_gateway_step_simulation_mode(self, mock_lxp_parser):
        """Test creating entry with simulation mode."""
        flow = LuxorLivingConfigFlow()
        flow.hass = MagicMock()
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
