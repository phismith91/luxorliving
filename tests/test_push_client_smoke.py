"""Smoke tests for PushClient — pure unit tests, no WebSocket server required."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.luxor_living.push_client import PushClient


def _make_client(entry_id="test_entry", ws_url="ws://localhost/ws", ws_token=None):
    hass = MagicMock()
    hass.async_create_task = MagicMock(return_value=MagicMock())
    client = PushClient(hass, entry_id, ws_url, ws_token)
    return client


@pytest.mark.smoke
class TestPushClientInit:
    """Kill mutations in PushClient.__init__."""

    def test_stopped_false_on_init(self):
        """Kill: _stopped = False → True."""
        client = _make_client()
        assert client._stopped is False

    def test_session_none_on_init(self):
        """Kill: _session = None → some default."""
        client = _make_client()
        assert client._session is None

    def test_task_none_on_init(self):
        """Kill: _task = None → some default."""
        client = _make_client()
        assert client._task is None

    def test_entry_id_stored(self):
        """Kill: entry_id assignment mutation."""
        client = _make_client(entry_id="my_entry")
        assert client.entry_id == "my_entry"

    def test_ws_url_stored(self):
        """Kill: _ws_url assignment mutation."""
        client = _make_client(ws_url="ws://192.168.1.1/push")
        assert client._ws_url == "ws://192.168.1.1/push"

    def test_ws_token_stored(self):
        """Kill: _ws_token assignment mutation."""
        client = _make_client(ws_token="secret")
        assert client._ws_token == "secret"


@pytest.mark.smoke
class TestPushClientStop:
    """Kill mutations in PushClient.stop."""

    @pytest.mark.asyncio
    async def test_stop_sets_stopped_true(self):
        """Kill: self._stopped = True → False."""
        client = _make_client()
        await client.stop()
        assert client._stopped is True

    @pytest.mark.asyncio
    async def test_stop_cancels_running_task(self):
        """Kill: task cancel guard removed."""
        client = _make_client()

        async def _long_running():
            await asyncio.sleep(100)

        task = asyncio.create_task(_long_running())
        client._task = task
        await client.stop()
        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_stop_does_not_cancel_done_task(self):
        """Kill: task.done() check removed."""
        client = _make_client()
        mock_task = MagicMock()
        mock_task.done.return_value = True
        mock_task.cancel = MagicMock()
        client._task = mock_task
        await client.stop()
        mock_task.cancel.assert_not_called()


@pytest.mark.smoke
class TestPushClientStart:
    """Kill mutations in PushClient.start."""

    def test_start_creates_task(self):
        """Kill: task creation removed."""
        client = _make_client()
        client.start()
        client.hass.async_create_task.assert_called_once()

    def test_start_idempotent_when_task_running(self):
        """Kill: 'not self._task.done()' guard removed."""
        client = _make_client()
        mock_task = MagicMock()
        mock_task.done.return_value = False
        client._task = mock_task
        client.start()
        client.hass.async_create_task.assert_not_called()

    def test_start_restarts_when_task_done(self):
        """Kill: done() check inverted."""
        client = _make_client()
        mock_task = MagicMock()
        mock_task.done.return_value = True
        client._task = mock_task
        client.start()
        client.hass.async_create_task.assert_called_once()


@pytest.mark.smoke
class TestPushClientBackoff:
    """Kill mutations in PushClient._run backoff logic."""

    @pytest.mark.asyncio
    async def test_backoff_doubles_on_reconnect(self):
        """Kill: backoff * 2 → backoff * 1 (no growth)."""
        client = _make_client()
        client._stopped = False
        delays = []

        async def fake_ws_connect(*args, **kwargs):
            raise ConnectionRefusedError("refused")

        async def fake_sleep(delay):
            delays.append(delay)
            if len(delays) >= 2:
                client._stopped = True

        with (
            patch(
                "custom_components.luxor_living.push_client.async_get_clientsession"
            ) as mock_get_session,
            patch("asyncio.sleep", side_effect=fake_sleep),
        ):
            mock_session = MagicMock()
            mock_session.ws_connect = MagicMock(side_effect=fake_ws_connect)
            mock_get_session.return_value = mock_session
            mock_session.close = AsyncMock()

            await client._run()

        assert delays[0] == 1.0
        assert delays[1] == 2.0

    @pytest.mark.asyncio
    async def test_backoff_capped_at_60(self):
        """Kill: min(backoff * 2, 60.0) cap mutation."""
        client = _make_client()
        client._stopped = False
        delays = []

        async def fake_ws_connect(*args, **kwargs):
            raise ConnectionRefusedError("refused")

        async def fake_sleep(delay):
            delays.append(delay)
            if len(delays) >= 8:
                client._stopped = True

        with (
            patch(
                "custom_components.luxor_living.push_client.async_get_clientsession"
            ) as mock_get_session,
            patch("asyncio.sleep", side_effect=fake_sleep),
        ):
            mock_session = MagicMock()
            mock_session.ws_connect = MagicMock(side_effect=fake_ws_connect)
            mock_get_session.return_value = mock_session
            mock_session.close = AsyncMock()

            await client._run()

        assert max(delays) <= 60.0
