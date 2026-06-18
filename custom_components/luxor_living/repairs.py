"""Repair flows for LUXORliving integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.ssl import SSLCipherList

from .const import DOMAIN
from .rest_client import AuthenticationError, BAOSRestClient

_LOGGER = logging.getLogger(__name__)


class LuxorLivingAuthenticationRepairFlow(RepairsFlow):
    """Handler for authentication failure repair flow."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the repair flow."""
        self.entry = entry
        self._username: str | None = None
        self._password: str | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the initial step."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the confirm step."""
        if user_input is not None:
            return await self.async_step_credentials()

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "host": self.entry.data.get(CONF_HOST, "unknown"),
                "username": self.entry.data.get(CONF_USERNAME, "admin"),
            },
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the credentials input step."""
        errors = {}

        if user_input is not None:
            # Test credentials
            host: str = self.entry.data[CONF_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                session = async_get_clientsession(
                    self.hass, verify_ssl=False, ssl_cipher=SSLCipherList.INSECURE
                )
                async with BAOSRestClient(host, use_https=True, session=session) as client:
                    await client.login(username, password)
                    _LOGGER.info("Authentication repair successful for %s", host)

                    # Update config entry with new credentials
                    new_data = {**self.entry.data}
                    new_data[CONF_USERNAME] = username
                    new_data[CONF_PASSWORD] = password

                    self.hass.config_entries.async_update_entry(
                        self.entry,
                        data=new_data,
                    )

                    # Reload the config entry to apply new credentials
                    await self.hass.config_entries.async_reload(self.entry.entry_id)

                    return self.async_create_entry(data={})

            except AuthenticationError as err:
                _LOGGER.warning("Authentication repair failed: %s", err)
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.exception("Unexpected error during authentication repair: %s", err)
                errors["base"] = "unknown"

        # Show form with current credentials as defaults
        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=self.entry.data.get(CONF_USERNAME, "admin"),
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "host": self.entry.data.get(CONF_HOST, "unknown"),
            },
        )


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, Any] | None,
) -> RepairsFlow:
    """Create flow for specific issue."""
    # Issues are created with a per-entry suffix: "authentication_failed_<entry_id>"
    if issue_id.startswith("authentication_failed"):
        entry_id = data.get("entry_id") if data else None
        if entry_id:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry:
                return LuxorLivingAuthenticationRepairFlow(entry)

    # Fallback for unknown issues
    return ConfirmRepairFlow()


async def create_auth_repair_issue(
    hass: HomeAssistant, entry: ConfigEntry, error_message: str
) -> None:
    """Create a repair issue for authentication failure."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"authentication_failed_{entry.entry_id}",
        is_fixable=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="authentication_failed",
        translation_placeholders={
            "host": entry.data.get(CONF_HOST, "unknown"),
            "username": entry.data.get(CONF_USERNAME, "admin"),
            "error": error_message,
        },
        data={"entry_id": entry.entry_id},
    )
    _LOGGER.warning(
        "Created repair issue for authentication failure on %s",
        entry.data.get(CONF_HOST),
    )


async def dismiss_auth_repair_issue(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Dismiss authentication repair issue if it exists."""
    ir.async_delete_issue(hass, DOMAIN, f"authentication_failed_{entry.entry_id}")
