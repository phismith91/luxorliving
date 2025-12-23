"""Config flow for LUXORliving integration."""
from __future__ import annotations

import logging
from pathlib import Path
import shutil
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_LXP_FILE,
    CONF_CONNECTION_TYPE,
    CONF_SIMULATION_MODE,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_HTTP_PORT,
    DEFAULT_CONNECTION_TYPE,
    DEFAULT_USERNAME,
    DEFAULT_PASSWORD,
    CONNECTION_TYPE_TUNNELING,
    CONNECTION_TYPE_ROUTING,
)
from .lxp_parser import LXPParser
from .rest_client import BAOSRestClient, AuthenticationError

_LOGGER = logging.getLogger(__name__)

STORAGE_PATH = ".storage/luxor_living.{key}.lxp"


def save_uploaded_lxp_file(hass: HomeAssistant, uploaded_file_id: str) -> str:
    """Save uploaded LXP file and return the storage path."""
    storage_path = hass.config.path(STORAGE_PATH.format(key=uploaded_file_id[:8]))
    
    with process_uploaded_file(hass, uploaded_file_id) as file_path:
        # Copy uploaded file to permanent storage
        shutil.copy(file_path, storage_path)
    
    _LOGGER.debug("Saved uploaded file to: %s", storage_path)
    return storage_path


# Step 1: LXP file browser
STEP_LXP_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_LXP_FILE): selector.FileSelector(
        selector.FileSelectorConfig(accept=".lxp")
    ),
})

# Step 2: Gateway configuration with authentication
STEP_GATEWAY_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST, default="192.168.1.3"): str,
    vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
    vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
    vol.Required(CONF_CONNECTION_TYPE, default=DEFAULT_CONNECTION_TYPE): vol.In([
        CONNECTION_TYPE_TUNNELING,
        CONNECTION_TYPE_ROUTING,
    ]),
    vol.Optional(CONF_SIMULATION_MODE, default=False): bool,
})


class LuxorLivingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LUXORliving."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._lxp_file: str | None = None
        self._project_name: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - LXP file selection via file browser."""
        errors: dict[str, str] = {}

        if user_input is not None:
            lxp_file_id = user_input[CONF_LXP_FILE]
            
            _LOGGER.debug("📁 Received file input: %s (type: %s)", lxp_file_id, type(lxp_file_id))
            
            # Save uploaded file using Home Assistant's file_upload component
            try:
                lxp_file = await self.hass.async_add_executor_job(
                    save_uploaded_lxp_file, self.hass, lxp_file_id
                )
                
                _LOGGER.info("Resolved file path: %s", lxp_file)
                
            except (OSError, PermissionError) as err:
                _LOGGER.error("Failed to save uploaded file: %s", err)
                errors["base"] = "file_not_found"
                return self.async_show_form(
                    step_id="user",
                    data_schema=STEP_LXP_DATA_SCHEMA,
                    errors=errors,
                )
            
            # Validate LXP file
            try:
                project_name = await self._validate_lxp_file(lxp_file)
                self._lxp_file = lxp_file
                self._project_name = project_name
                
                _LOGGER.info("LXP file selected: %s (Project: %s)", lxp_file, project_name)
                
                # Proceed to gateway configuration
                return await self.async_step_gateway()
                
            except FileNotFoundError as err:
                _LOGGER.error("File not found: %s", err)
                errors["base"] = "file_not_found"
            except ValueError as err:
                _LOGGER.error("Invalid LXP file: %s", err)
                errors["base"] = "invalid_lxp"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_LXP_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_gateway(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle gateway configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate credentials if not in simulation mode
            if not user_input.get(CONF_SIMULATION_MODE, False):
                connection_type = user_input.get(CONF_CONNECTION_TYPE, DEFAULT_CONNECTION_TYPE)
                
                # For Tunneling: validate REST API credentials
                if connection_type == CONNECTION_TYPE_TUNNELING:
                    try:
                        await self._validate_credentials(
                            user_input[CONF_HOST],
                            user_input[CONF_USERNAME],
                            user_input[CONF_PASSWORD],
                        )
                    except AuthenticationError as err:
                        _LOGGER.error("Authentication failed: %s", err)
                        errors["base"] = "invalid_auth"
                        return self.async_show_form(
                            step_id="gateway",
                            data_schema=STEP_GATEWAY_DATA_SCHEMA,
                            errors=errors,
                        )
                    except (ConnectionError, TimeoutError) as err:
                        _LOGGER.error("Connection error: %s", err)
                        errors["base"] = "cannot_connect"
                        return self.async_show_form(
                            step_id="gateway",
                            data_schema=STEP_GATEWAY_DATA_SCHEMA,
                            errors=errors,
                        )
                else:
                    # For Routing: validate gateway is reachable (ping check)
                    try:
                        import socket
                        socket.create_connection((user_input[CONF_HOST], 3671), timeout=2)
                    except (ConnectionRefusedError, TimeoutError, OSError) as err:
                        _LOGGER.error("Cannot reach KNX/IP gateway at %s:%s - %s", 
                                    user_input[CONF_HOST], 3671, err)
                        errors["base"] = "cannot_connect"
                        return self.async_show_form(
                            step_id="gateway",
                            data_schema=STEP_GATEWAY_DATA_SCHEMA,
                            errors=errors,
                        )
            
            # Combine LXP file and gateway config
            data = {
                CONF_LXP_FILE: self._lxp_file,
                CONF_HOST: user_input[CONF_HOST],
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_CONNECTION_TYPE: user_input[CONF_CONNECTION_TYPE],
                CONF_SIMULATION_MODE: user_input.get(CONF_SIMULATION_MODE, False),
            }

            # Create entry
            return self.async_create_entry(
                title=f"LUXORliving ({self._project_name})",
                data=data,
            )

        return self.async_show_form(
            step_id="gateway",
            data_schema=STEP_GATEWAY_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "project_name": self._project_name or "Unknown",
            },
        )

    async def _validate_lxp_file(self, lxp_file: str) -> str:
        """Validate LXP file and return project name."""
        file_path = Path(lxp_file).expanduser()
        
        if not file_path.exists():
            raise FileNotFoundError(f"LXP file not found: {lxp_file}")
        
        if not file_path.is_file():
            raise ValueError(f"Not a file: {lxp_file}")
        
        # Try to parse the file
        parser = LXPParser(str(file_path))
        project = await parser.parse()
        
        _LOGGER.debug("Valid LXP file: %s (Project: %s)", lxp_file, project.name)
        return project.name
    
    async def _validate_credentials(self, host: str, username: str, password: str) -> None:
        """
        Validate credentials by attempting REST API login.
        
        Raises:
            AuthenticationError: If credentials are invalid
            Exception: If connection fails
        """
        _LOGGER.debug("🔐 Validating credentials for %s@%s", username, host)
        
        async with BAOSRestClient(host, port=DEFAULT_HTTP_PORT) as client:
            # Attempt login - will raise AuthenticationError if invalid
            await client.login(username, password)
            _LOGGER.debug("Credentials validated successfully")

