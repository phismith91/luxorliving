"""Config flow for LUXORliving integration."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_LXP_FILE,
    CONF_CONNECTION_TYPE,
    CONF_SIMULATION_MODE,
    DEFAULT_PORT,
    DEFAULT_CONNECTION_TYPE,
    CONNECTION_TYPE_TUNNELING,
    CONNECTION_TYPE_ROUTING,
)
from .lxp_parser import LXPParser

_LOGGER = logging.getLogger(__name__)

# Step 1: LXP file selection from config/luxor_living/
STEP_LXP_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_LXP_FILE, description="Filename in /config/luxor_living/"): str,
})

# Step 2: Gateway configuration
STEP_GATEWAY_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST, default="192.168.1.3"): str,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
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
    ) -> FlowResult:
        """Handle the initial step - LXP file selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            filename = user_input[CONF_LXP_FILE]
            
            # Build path to file in config/luxor_living/
            luxor_dir = self.hass.config.path("luxor_living")
            lxp_file = os.path.join(luxor_dir, filename)
            
            # Validate LXP file
            try:
                if not os.path.exists(lxp_file):
                    # Try to list available files for better error message
                    if os.path.exists(luxor_dir):
                        available = [f for f in os.listdir(luxor_dir) if f.endswith('.lxp')]
                        if available:
                            _LOGGER.error("File not found: %s. Available: %s", filename, available)
                        else:
                            _LOGGER.error("No .lxp files found in %s", luxor_dir)
                    raise FileNotFoundError(f"LXP file not found: {filename}")
                
                project_name = await self._validate_lxp_file(lxp_file)
                self._lxp_file = lxp_file
                self._project_name = project_name
                
                # Proceed to gateway configuration
                return await self.async_step_gateway()
                
            except FileNotFoundError:
                errors["base"] = "file_not_found"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Error parsing LXP file: %s", err)
                errors["base"] = "invalid_lxp"

        # Check for available LXP files
        luxor_dir = self.hass.config.path("luxor_living")
        available_files = []
        default_filename = "project.lxp"
        
        if os.path.exists(luxor_dir):
            available_files = [f for f in os.listdir(luxor_dir) if f.endswith('.lxp')]
            if available_files:
                default_filename = available_files[0]
        
        schema = vol.Schema({
            vol.Required(CONF_LXP_FILE, default=default_filename): str,
        })

        description = "Please copy your LXP file to /config/luxor_living/ first"
        if available_files:
            description = f"Available files: {', '.join(available_files)}"

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"info": description},
        )

    async def async_step_gateway(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle gateway configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Combine LXP file and gateway config
            data = {
                CONF_LXP_FILE: self._lxp_file,
                CONF_HOST: user_input[CONF_HOST],
                CONF_PORT: user_input[CONF_PORT],
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
        
        _LOGGER.info("✅ Valid LXP file: %s (Project: %s)", lxp_file, project.name)
        return project.name
