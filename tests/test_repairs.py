"""Tests for repairs.py — authentication repair flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from custom_components.luxor_living.repairs import (
    LuxorLivingAuthenticationRepairFlow,
    async_create_fix_flow,
    create_auth_repair_issue,
    dismiss_auth_repair_issue,
)
from custom_components.luxor_living.rest_client import AuthenticationError


def _make_entry(host="192.168.1.100", username="admin", password="secret", entry_id="test_id"):
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = {CONF_HOST: host, CONF_USERNAME: username, CONF_PASSWORD: password}
    return entry


class TestLuxorLivingAuthenticationRepairFlow:
    """Tests for the repair flow class."""

    def test_init(self):
        entry = _make_entry()
        flow = LuxorLivingAuthenticationRepairFlow(entry)
        assert flow.entry is entry
        assert flow._username is None
        assert flow._password is None

    @pytest.mark.asyncio
    async def test_async_step_init_delegates_to_confirm(self):
        entry = _make_entry()
        flow = LuxorLivingAuthenticationRepairFlow(entry)
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "confirm"})
        result = await flow.async_step_init(None)
        flow.async_show_form.assert_called_once()
        assert result["step_id"] == "confirm"

    @pytest.mark.asyncio
    async def test_async_step_confirm_shows_form_without_input(self):
        entry = _make_entry()
        flow = LuxorLivingAuthenticationRepairFlow(entry)
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "confirm"})
        await flow.async_step_confirm(None)
        flow.async_show_form.assert_called_once_with(
            step_id="confirm",
            description_placeholders={
                "host": "192.168.1.100",
                "username": "admin",
            },
        )

    @pytest.mark.asyncio
    async def test_async_step_confirm_with_input_goes_to_credentials(self):
        entry = _make_entry()
        flow = LuxorLivingAuthenticationRepairFlow(entry)
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "credentials"})
        result = await flow.async_step_confirm(user_input={})
        flow.async_show_form.assert_called_once()
        assert result["step_id"] == "credentials"

    @pytest.mark.asyncio
    async def test_async_step_credentials_shows_form_without_input(self):
        entry = _make_entry()
        flow = LuxorLivingAuthenticationRepairFlow(entry)
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "credentials"})
        await flow.async_step_credentials(None)
        flow.async_show_form.assert_called_once()
        call_kwargs = flow.async_show_form.call_args[1]
        assert call_kwargs["step_id"] == "credentials"
        assert call_kwargs["errors"] == {}
        assert "host" in call_kwargs["description_placeholders"]

    @pytest.mark.asyncio
    async def test_async_step_credentials_success(self):
        entry = _make_entry()
        flow = LuxorLivingAuthenticationRepairFlow(entry)
        flow.hass = MagicMock()
        flow.hass.config_entries.async_update_entry = MagicMock()
        flow.hass.config_entries.async_reload = AsyncMock()
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "custom_components.luxor_living.repairs.BAOSRestClient",
            return_value=mock_client,
        ):
            await flow.async_step_credentials({CONF_USERNAME: "admin", CONF_PASSWORD: "newpass"})

        flow.hass.config_entries.async_update_entry.assert_called_once()
        flow.hass.config_entries.async_reload.assert_awaited_once_with(entry.entry_id)
        flow.async_create_entry.assert_called_once_with(data={})

    @pytest.mark.asyncio
    async def test_async_step_credentials_invalid_auth(self):
        entry = _make_entry()
        flow = LuxorLivingAuthenticationRepairFlow(entry)
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "credentials"})

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.login = AsyncMock(side_effect=AuthenticationError("Bad credentials"))

        with patch(
            "custom_components.luxor_living.repairs.BAOSRestClient",
            return_value=mock_client,
        ):
            await flow.async_step_credentials({CONF_USERNAME: "admin", CONF_PASSWORD: "wrong"})

        call_kwargs = flow.async_show_form.call_args[1]
        assert call_kwargs["errors"]["base"] == "invalid_auth"

    @pytest.mark.asyncio
    async def test_async_step_credentials_unexpected_error(self):
        entry = _make_entry()
        flow = LuxorLivingAuthenticationRepairFlow(entry)
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "credentials"})

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.login = AsyncMock(side_effect=RuntimeError("Boom"))

        with patch(
            "custom_components.luxor_living.repairs.BAOSRestClient",
            return_value=mock_client,
        ):
            await flow.async_step_credentials({CONF_USERNAME: "admin", CONF_PASSWORD: "pass"})

        call_kwargs = flow.async_show_form.call_args[1]
        assert call_kwargs["errors"]["base"] == "unknown"

    @pytest.mark.asyncio
    async def test_confirm_uses_unknown_defaults_when_keys_missing(self):
        """Entry data without host/username should fall back gracefully."""
        entry = MagicMock()
        entry.entry_id = "x"
        entry.data = {}
        flow = LuxorLivingAuthenticationRepairFlow(entry)
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        await flow.async_step_confirm(None)
        placeholders = flow.async_show_form.call_args[1]["description_placeholders"]
        assert placeholders["host"] == "unknown"
        assert placeholders["username"] == "admin"


class TestAsyncCreateFixFlow:
    """Tests for async_create_fix_flow factory."""

    @pytest.mark.asyncio
    async def test_authentication_failed_issue_with_valid_entry(self):
        hass = MagicMock()
        entry = _make_entry()
        hass.config_entries.async_get_entry = MagicMock(return_value=entry)
        result = await async_create_fix_flow(hass, "authentication_failed", {"entry_id": "test_id"})
        assert isinstance(result, LuxorLivingAuthenticationRepairFlow)
        assert result.entry is entry

    @pytest.mark.asyncio
    async def test_suffixed_issue_id_matches_repair_flow(self):
        """Real issue IDs are 'authentication_failed_<entry_id>' — must still match."""
        hass = MagicMock()
        entry = _make_entry()
        hass.config_entries.async_get_entry = MagicMock(return_value=entry)
        result = await async_create_fix_flow(
            hass, "authentication_failed_test_id", {"entry_id": "test_id"}
        )
        assert isinstance(result, LuxorLivingAuthenticationRepairFlow)
        assert result.entry is entry

    @pytest.mark.asyncio
    async def test_authentication_failed_issue_without_entry_id(self):
        from homeassistant.components.repairs import ConfirmRepairFlow

        hass = MagicMock()
        result = await async_create_fix_flow(hass, "authentication_failed", {})
        assert isinstance(result, ConfirmRepairFlow)

    @pytest.mark.asyncio
    async def test_authentication_failed_issue_entry_not_found(self):
        from homeassistant.components.repairs import ConfirmRepairFlow

        hass = MagicMock()
        hass.config_entries.async_get_entry = MagicMock(return_value=None)
        result = await async_create_fix_flow(hass, "authentication_failed", {"entry_id": "missing"})
        assert isinstance(result, ConfirmRepairFlow)

    @pytest.mark.asyncio
    async def test_unknown_issue_returns_confirm_flow(self):
        from homeassistant.components.repairs import ConfirmRepairFlow

        hass = MagicMock()
        result = await async_create_fix_flow(hass, "some_other_issue", None)
        assert isinstance(result, ConfirmRepairFlow)

    @pytest.mark.asyncio
    async def test_none_data_returns_confirm_flow(self):
        from homeassistant.components.repairs import ConfirmRepairFlow

        hass = MagicMock()
        result = await async_create_fix_flow(hass, "authentication_failed", None)
        assert isinstance(result, ConfirmRepairFlow)


class TestCreateAuthRepairIssue:
    """Tests for issue creation / dismissal helpers."""

    @pytest.mark.asyncio
    async def test_create_auth_repair_issue(self):
        hass = MagicMock()
        entry = _make_entry()

        with patch("custom_components.luxor_living.repairs.ir.async_create_issue") as mock_create:
            await create_auth_repair_issue(hass, entry, "auth failed")

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["translation_key"] == "authentication_failed"
        assert "host" in call_kwargs["translation_placeholders"]
        assert call_kwargs["translation_placeholders"]["error"] == "auth failed"
        assert call_kwargs["is_fixable"] is True

    @pytest.mark.asyncio
    async def test_dismiss_auth_repair_issue(self):
        hass = MagicMock()
        entry = _make_entry()

        with patch("custom_components.luxor_living.repairs.ir.async_delete_issue") as mock_delete:
            await dismiss_auth_repair_issue(hass, entry)

        mock_delete.assert_called_once()
        args = mock_delete.call_args[0]
        assert args[0] is hass
        assert "authentication_failed" in args[2]

    @pytest.mark.asyncio
    async def test_create_issue_entry_without_data_keys(self):
        """Entry with missing keys falls back to defaults."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "x"
        entry.data = {}

        with patch("custom_components.luxor_living.repairs.ir.async_create_issue") as mock_create:
            await create_auth_repair_issue(hass, entry, "err")

        placeholders = mock_create.call_args[1]["translation_placeholders"]
        assert placeholders["host"] == "unknown"
        assert placeholders["username"] == "admin"
