"""Tests for config flow."""

import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.luxor_living.config_flow import LuxorLivingConfigFlow
from custom_components.luxor_living.const import (
    CONF_CONNECTION_TYPE,
    CONF_LXP_FILE,
    CONF_SIMULATION_MODE,
    CONNECTION_TYPE_ROUTING,
    CONNECTION_TYPE_TUNNELING,
)


@pytest.fixture
def mock_lxp_parser():
    """Mock LXP Parser."""
    with patch("custom_components.luxor_living.config_flow.LXPParser") as mock:
        # Mock the parse_cached classmethod
        mock.parse_cached = AsyncMock()

        # Mock project
        mock_project = MagicMock()
        mock_project.name = "Test Project"
        mock.parse_cached.return_value = mock_project

        yield mock


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.config.path = MagicMock(return_value="/config/.storage/luxor_living.test.lxp")
    hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))
    return hass


@pytest.fixture
def mock_file_upload():
    """Mock file upload context manager."""

    @contextmanager
    def mock_process_uploaded_file(hass, file_id):
        # Create a temporary file to simulate the uploaded file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lxp", delete=False) as f:
            f.write('<?xml version="1.0"?><Project name="Test"><Functions/></Project>')
            temp_path = f.name
        try:
            yield Path(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    with patch(
        "custom_components.luxor_living.config_flow.process_uploaded_file",
        mock_process_uploaded_file,
    ):
        yield


class TestLuxorLivingConfigFlow:
    """Test LuxorLiving config flow."""

    @pytest.fixture(autouse=True)
    def patch_unique_id_methods(self):
        """Patch async_set_unique_id and _abort_if_unique_id_configured for all tests."""
        with patch(
            "custom_components.luxor_living.config_flow.LuxorLivingConfigFlow.async_set_unique_id",
            new_callable=AsyncMock,
        ):
            with patch(
                "custom_components.luxor_living.config_flow.LuxorLivingConfigFlow._abort_if_unique_id_configured",
            ):
                yield

    @pytest.mark.asyncio
    @pytest.mark.smoke
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
    async def test_user_step_file_not_found(self, mock_hass, mock_file_upload):
        """Test user step with file upload error."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass

        # Mock process_uploaded_file to raise OSError (more specific exception)
        with patch(
            "custom_components.luxor_living.config_flow.process_uploaded_file"
        ) as mock_upload:
            mock_upload.side_effect = OSError("File not found")

            result = await flow.async_step_user({CONF_LXP_FILE: "019b336bd0ef4a4b"})

        assert result["type"] == "form"
        assert result["errors"]["base"] == "file_not_found"

    @pytest.mark.asyncio
    async def test_user_step_valid_file(self, mock_hass, mock_lxp_parser, mock_file_upload):
        """Test user step with valid LXP file upload."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass

        with patch("custom_components.luxor_living.config_flow.shutil.copy"):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    result = await flow.async_step_user({CONF_LXP_FILE: "019b336bd0ef4a4b"})

        assert result["type"] == "form"
        assert result["step_id"] == "gateway"
        assert flow._project_name == "Test Project"

    @pytest.mark.asyncio
    async def test_user_step_invalid_lxp(self, mock_hass, mock_lxp_parser, mock_file_upload):
        """Test user step with invalid LXP file content."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass

        # Make parser raise ValueError (more specific exception)
        mock_lxp_parser.parse_cached.side_effect = ValueError("Invalid XML")

        with patch("custom_components.luxor_living.config_flow.shutil.copy"):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    result = await flow.async_step_user({CONF_LXP_FILE: "019b336bd0ef4a4b"})

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

        with patch.object(flow, "_validate_credentials", return_value=True):
            result = await flow.async_step_gateway(
                {
                    "host": "192.168.1.3",
                    "port": 3671,
                    "username": "admin",
                    "password": "admin",
                    CONF_CONNECTION_TYPE: CONNECTION_TYPE_TUNNELING,
                    CONF_SIMULATION_MODE: False,
                }
            )

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

        with patch("socket.create_connection"):
            result = await flow.async_step_gateway(
                {
                    "host": "224.0.23.12",
                    "port": 3671,
                    "username": "admin",
                    "password": "admin",
                    CONF_CONNECTION_TYPE: CONNECTION_TYPE_ROUTING,
                    CONF_SIMULATION_MODE: False,
                }
            )

        assert result["type"] == "create_entry"
        assert result["data"][CONF_CONNECTION_TYPE] == CONNECTION_TYPE_ROUTING

    @pytest.mark.asyncio
    async def test_gateway_step_simulation_mode(self, mock_hass, mock_lxp_parser):
        """Test creating entry with simulation mode."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass
        flow._lxp_file = "/test.lxp"
        flow._project_name = "Test Project"

        result = await flow.async_step_gateway(
            {
                "host": "localhost",
                "port": 3671,
                "username": "admin",
                "password": "admin",
                CONF_CONNECTION_TYPE: CONNECTION_TYPE_TUNNELING,
                CONF_SIMULATION_MODE: True,
            }
        )

        assert result["type"] == "create_entry"
        assert result["data"][CONF_SIMULATION_MODE] is True

    @pytest.mark.asyncio
    async def test_full_flow_with_file_selector(self, mock_hass, mock_lxp_parser, mock_file_upload):
        """Test complete flow from file upload to entry creation."""
        flow = LuxorLivingConfigFlow()
        flow.hass = mock_hass

        # Step 1: Show user form
        result = await flow.async_step_user()
        assert result["type"] == "form"
        assert result["step_id"] == "user"

        # Step 2: Submit file upload (with file ID from FileSelector)
        with patch("custom_components.luxor_living.config_flow.shutil.copy"):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    result = await flow.async_step_user(
                        {CONF_LXP_FILE: "019b336bd0ef4a4b4b3318d08a60e437"}
                    )

        assert result["type"] == "form"
        assert result["step_id"] == "gateway"

        # Step 3: Submit gateway config
        with patch.object(flow, "_validate_credentials", return_value=True):
            result = await flow.async_step_gateway(
                {
                    "host": "192.168.1.3",
                    "port": 3671,
                    "username": "admin",
                    "password": "admin",
                    CONF_CONNECTION_TYPE: CONNECTION_TYPE_TUNNELING,
                    CONF_SIMULATION_MODE: False,
                }
            )

        assert result["type"] == "create_entry"
        assert result["title"] == "LUXORliving (Test Project)"
