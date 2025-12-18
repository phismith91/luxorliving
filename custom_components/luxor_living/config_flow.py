"""Config flow for LUXORliving integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_LXP_FILE, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
})


class LuxorLivingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LUXORliving."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate connection
            try:
                # TODO: Implement connection test
                await self._test_connection(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT]
                )
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "cannot_connect"
            else:
                # Create entry
                return self.async_create_entry(
                    title=f"LUXORliving {user_input[CONF_HOST]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_import_lxp(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle LXP file import step."""
        # TODO: Implement LXP file upload and parsing
        return self.async_abort(reason="not_implemented")

    async def _test_connection(self, host: str, port: int) -> bool:
        """Test connection to KNX/IP gateway."""
        # TODO: Implement actual connection test
        _LOGGER.info("Testing connection to %s:%s", host, port)
        return True
