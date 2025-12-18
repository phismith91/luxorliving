"""Config flow for LUXORliving integration."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import media_source
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

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

# Step 1: LXP file browser
STEP_LXP_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_LXP_FILE): selector.FileSelector(
        selector.FileSelectorConfig(accept=".lxp")
    ),
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
        """Handle the initial step - LXP file selection via file browser."""
        errors: dict[str, str] = {}

        if user_input is not None:
            lxp_file_id = user_input[CONF_LXP_FILE]
            
            _LOGGER.debug("📁 Received file input: %s (type: %s)", lxp_file_id, type(lxp_file_id))
            
            # Convert FileSelector ID to actual file path
            try:
                # Resolve media source to local file path
                media = await media_source.async_resolve_media(
                    self.hass, lxp_file_id, None
                )
                lxp_file = media.url.removeprefix("/media/local/")
                lxp_file = os.path.join(self.hass.config.path("media"), lxp_file)
                
                _LOGGER.info("📂 Resolved file path: %s", lxp_file)
                
            except Exception as err:
                _LOGGER.error("❌ Failed to resolve file: %s", err)
                errors["base"] = "file_not_found"
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(
                        {
                            vol.Required(CONF_LXP_FILE): selector.FileSelector(
                                selector.FileSelectorConfig(accept=".lxp")
                            )
                        }
                    ),
                    errors=errors,
                )
            
            # Validate LXP file
            try:
                project_name = await self._validate_lxp_file(lxp_file)
                self._lxp_file = lxp_file
                self._project_name = project_name
                
                _LOGGER.info("✅ LXP file selected: %s (Project: %s)", lxp_file, project_name)
                
                # Proceed to gateway configuration
                return await self.async_step_gateway()
                
            except FileNotFoundError as err:
                _LOGGER.error("❌ File not found: %s", err)
                errors["base"] = "file_not_found"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Error parsing LXP file: %s", err)
                errors["base"] = "invalid_lxp"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_LXP_DATA_SCHEMA,
            errors=errors,
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
