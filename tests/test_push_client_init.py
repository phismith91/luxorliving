"""Tests for PushClient initialization."""

from unittest.mock import MagicMock

import pytest


class TestPushClientInit:
    """Test PushClient initialization."""

    def test_init_sets_attributes(self):
        """Test __init__ sets attributes correctly."""
        from custom_components.luxor_living.push_client import PushClient

        hass = MagicMock()
        client = PushClient(hass, "entry123", "ws://example.com:8000", ws_token="token_value")

        assert client.hass is hass
        assert client.entry_id == "entry123"
        assert client._ws_url == "ws://example.com:8000"
        assert client._ws_token == "token_value"
        assert client._task is None
        assert client._stopped is False

    def test_init_without_token(self):
        """Test __init__ without auth token."""
        from custom_components.luxor_living.push_client import PushClient

        hass = MagicMock()
        client = PushClient(hass, "entry123", "ws://example.com")

        assert client._ws_token is None
