"""Config flow for Theben LUXORliving integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LuxorLivingApi, LuxorLivingConnectionError
from .const import (
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.
    
    Args:
        hass: Home Assistant instance
        data: User input data
        
    Returns:
        Dictionary with 'title' key
        
    Raises:
        LuxorLivingConnectionError: If cannot connect
    """
    session = async_get_clientsession(hass)
    api = LuxorLivingApi(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        session=session,
    )
    
    # Test the connection
    await api.test_connection()
    
    # Return info to store in the config entry
    return {"title": f"LUXORliving ({data[CONF_HOST]})"}


class LuxorLivingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LUXORliving."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step.
        
        Args:
            user_input: User input data
            
        Returns:
            Flow result
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except LuxorLivingConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
