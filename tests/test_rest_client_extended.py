"""Extended tests for BAOSRestClient covering uncovered branches."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from custom_components.luxor_living.rest_client import (
    AuthenticationError,
    BAOSRestClient,
    TunnelingError,
    _make_ssl_context,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _authenticated_client(host="192.168.1.1"):
    """Return a client already marked as authenticated."""
    client = BAOSRestClient(host, use_https=False)
    client.session_token = "fake_token"
    client.session_expires = datetime.now() + timedelta(hours=1)
    client._session = MagicMock()
    return client


# ── Server handlers ───────────────────────────────────────────────────────────


async def login_ok(request):
    data = await request.json()
    if data.get("username") == "admin" and data.get("password") == "pass":
        return web.Response(text="valid_token_abc")
    return web.Response(status=401)


async def login_server_error(request):
    return web.Response(status=500)


async def login_empty_token(request):
    return web.Response(text="")


async def logout_200(request):
    return web.Response(status=200)


async def logout_error(request):
    return web.Response(status=500)


async def tunneling_401(request):
    return web.Response(status=401)


async def tunneling_403(request):
    return web.Response(text="Forbidden", status=403)


async def tunneling_500(request):
    return web.Response(text="Internal Error", status=500)


async def tunneling_200_json(request):
    return web.json_response({"enabled": True})


async def tunneling_disable_fail(request):
    return web.Response(text="Internal Error", status=500)


@pytest_asyncio.fixture
async def extended_server():
    app = web.Application()
    app.router.add_post("/rest/login", login_ok)
    app.router.add_post("/rest/logout", logout_200)
    app.router.add_put("/rest/device/authtunneling", tunneling_200_json)
    app.router.add_get("/rest/device/authtunneling", tunneling_200_json)

    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    yield client
    await client.close()


# ── Unit tests (no socket) ────────────────────────────────────────────────────


class TestBAOSRestClientUnit:
    """Pure unit tests — no HTTP server needed."""

    def test_init_defaults(self):
        c = BAOSRestClient("10.0.0.1")
        assert c.host == "10.0.0.1"
        assert c.port == 443
        assert c.use_https is True
        assert "https" in c.base_url
        assert c.session_token is None
        assert c.tunneling_enabled is False

    def test_init_http(self):
        c = BAOSRestClient("10.0.0.1", port=80, use_https=False)
        assert "http://" in c.base_url
        assert c.port == 80

    def test_get_auth_headers_no_token(self):
        c = BAOSRestClient("10.0.0.1")
        assert c._get_auth_headers() == {}

    def test_get_auth_headers_with_token(self):
        c = _authenticated_client()
        headers = c._get_auth_headers()
        assert "Cookie" in headers
        assert "Authorization" in headers
        assert "fake_token" in headers["Authorization"]

    def test_ensure_authenticated_no_token(self):
        c = BAOSRestClient("10.0.0.1")
        with pytest.raises(AuthenticationError, match="Not logged in"):
            c._ensure_authenticated()

    def test_ensure_authenticated_expired(self):
        c = BAOSRestClient("10.0.0.1")
        c.session_token = "tok"
        c.session_expires = datetime.now() - timedelta(seconds=1)
        with pytest.raises(AuthenticationError, match="expired"):
            c._ensure_authenticated()

    def test_ensure_authenticated_ok(self):
        c = _authenticated_client()
        c._ensure_authenticated()  # must not raise

    def test_is_authenticated_no_token(self):
        c = BAOSRestClient("10.0.0.1")
        assert c.is_authenticated is False

    def test_is_authenticated_expired(self):
        c = BAOSRestClient("10.0.0.1")
        c.session_token = "tok"
        c.session_expires = datetime.now() - timedelta(seconds=1)
        assert c.is_authenticated is False

    def test_is_authenticated_valid(self):
        c = _authenticated_client()
        assert c.is_authenticated is True

    def test_get_diagnostics_unauthenticated(self):
        c = BAOSRestClient("10.0.0.1")
        d = c.get_diagnostics()
        assert d["host"] == "10.0.0.1"
        assert d["authenticated"] is False
        assert d["session_token"] is False
        assert d["session_expires"] is None
        assert d["tunneling_enabled"] is False

    def test_get_diagnostics_authenticated(self):
        c = _authenticated_client()
        d = c.get_diagnostics()
        assert d["authenticated"] is True
        assert d["session_token"] is True
        assert d["session_expires"] is not None

    @pytest.mark.asyncio
    async def test_logout_no_token_is_noop(self):
        c = BAOSRestClient("10.0.0.1")
        await c.logout()  # must not raise, no session to clear

    @pytest.mark.asyncio
    async def test_get_tunneling_status_not_authenticated(self):
        c = BAOSRestClient("10.0.0.1")
        with pytest.raises(AuthenticationError):
            await c.get_tunneling_status()

    @pytest.mark.asyncio
    async def test_login_debug_log_omits_password(self):
        """Ensure the login debug log never contains the password (CodeQL S2068)."""
        c = BAOSRestClient("10.0.0.1", use_https=False)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="test_token_abc")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        c._session = mock_session

        with patch("custom_components.luxor_living.rest_client._LOGGER") as mock_logger:
            await c.login("admin", "s3cr3t")

        logged_messages = " ".join(str(call) for call in mock_logger.debug.call_args_list)
        assert "s3cr3t" not in logged_messages
        assert "admin" in logged_messages


class TestSslContextAndSessionCreation:
    """Cover the TLS helper and the login() lazy-session-creation path."""

    def test_make_ssl_context_disables_verification_no_seclevel(self):
        import ssl as _ssl

        ctx = _make_ssl_context()

        assert ctx.check_hostname is False
        assert ctx.verify_mode == _ssl.CERT_NONE
        assert ctx.minimum_version == _ssl.TLSVersion.TLSv1_2

    @pytest.mark.asyncio
    async def test_login_creates_session_when_missing(self):
        """login() with no existing session must build one via _make_ssl_context."""
        c = BAOSRestClient("10.0.0.9", use_https=True)
        assert c._session is None

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="tok123")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        created_session = MagicMock()
        created_session.post = MagicMock(return_value=mock_response)

        with (
            patch("custom_components.luxor_living.rest_client.aiohttp.TCPConnector") as mock_conn,
            patch(
                "custom_components.luxor_living.rest_client.aiohttp.ClientSession",
                return_value=created_session,
            ),
        ):
            token = await c.login("admin", "pw")

        assert token == "tok123"
        assert c._session is created_session
        mock_conn.assert_called_once()


# ── Integration tests with mock HTTP server ───────────────────────────────────


@pytest.mark.enable_socket
class TestBAOSRestClientIntegration:
    """Tests using aiohttp TestServer to cover HTTP response branches."""

    @pytest.mark.asyncio
    async def test_login_success_sets_token(self, extended_server):
        host = extended_server.server.host
        port = extended_server.server.port
        client = BAOSRestClient(host, port=port, use_https=False)
        client._session = extended_server.session
        token = await client.login("admin", "pass")
        assert token == "valid_token_abc"
        assert client.session_token == "valid_token_abc"
        assert client.session_expires is not None

    @pytest.mark.asyncio
    async def test_login_401_raises_auth_error(self, extended_server):
        host = extended_server.server.host
        port = extended_server.server.port
        client = BAOSRestClient(host, port=port, use_https=False)

        # Override login handler for this test
        app = web.Application()

        async def bad_login(req):
            return web.Response(status=401, text="Unauthorized")

        app.router.add_post("/rest/login", bad_login)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        client._session = tc.session
        client.base_url = f"http://{tc.server.host}:{tc.server.port}"
        with pytest.raises(AuthenticationError):
            await client.login("bad", "creds")
        await tc.close()

    @pytest.mark.asyncio
    async def test_login_empty_token_raises(self):
        app = web.Application()
        app.router.add_post("/rest/login", login_empty_token)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        client = BAOSRestClient(tc.server.host, port=tc.server.port, use_https=False)
        client._session = tc.session
        with pytest.raises(AuthenticationError, match="No session cookie"):
            await client.login("admin", "pass")
        await tc.close()

    @pytest.mark.asyncio
    async def test_login_server_error_raises(self):
        app = web.Application()
        app.router.add_post("/rest/login", login_server_error)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        client = BAOSRestClient(tc.server.host, port=tc.server.port, use_https=False)
        client._session = tc.session
        with pytest.raises(AuthenticationError, match="status 500"):
            await client.login("admin", "pass")
        await tc.close()

    @pytest.mark.asyncio
    async def test_enable_tunneling_200_json(self, extended_server):
        host = extended_server.server.host
        port = extended_server.server.port
        client = _authenticated_client(host)
        client._session = extended_server.session
        client.base_url = f"http://{host}:{port}"
        result = await client.enable_tunneling()
        assert result is True
        assert client.tunneling_enabled is True

    @pytest.mark.asyncio
    async def test_enable_tunneling_401_raises(self):
        app = web.Application()
        app.router.add_put("/rest/device/authtunneling", tunneling_401)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        client = _authenticated_client(tc.server.host)
        client._session = tc.session
        client.base_url = f"http://{tc.server.host}:{tc.server.port}"
        with pytest.raises(AuthenticationError):
            await client.enable_tunneling()
        await tc.close()

    @pytest.mark.asyncio
    async def test_enable_tunneling_403_raises_tunneling_error(self):
        app = web.Application()
        app.router.add_put("/rest/device/authtunneling", tunneling_403)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        client = _authenticated_client(tc.server.host)
        client._session = tc.session
        client.base_url = f"http://{tc.server.host}:{tc.server.port}"
        with pytest.raises(TunnelingError, match="Forbidden"):
            await client.enable_tunneling()
        await tc.close()

    @pytest.mark.asyncio
    async def test_enable_tunneling_500_raises_tunneling_error(self):
        app = web.Application()
        app.router.add_put("/rest/device/authtunneling", tunneling_500)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        client = _authenticated_client(tc.server.host)
        client._session = tc.session
        client.base_url = f"http://{tc.server.host}:{tc.server.port}"
        with pytest.raises(TunnelingError):
            await client.enable_tunneling()
        await tc.close()

    @pytest.mark.asyncio
    async def test_disable_tunneling_failure_returns_false(self):
        app = web.Application()
        app.router.add_put("/rest/device/authtunneling", tunneling_disable_fail)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        client = _authenticated_client(tc.server.host)
        client._session = tc.session
        client.base_url = f"http://{tc.server.host}:{tc.server.port}"
        result = await client.disable_tunneling()
        assert result is False
        await tc.close()

    @pytest.mark.asyncio
    async def test_logout_200_clears_state(self):
        app = web.Application()
        app.router.add_post("/rest/logout", logout_200)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        client = _authenticated_client(tc.server.host)
        client._session = tc.session
        client.base_url = f"http://{tc.server.host}:{tc.server.port}"
        client.tunneling_enabled = True
        await client.logout()
        assert client.session_token is None
        assert client.tunneling_enabled is False
        await tc.close()

    @pytest.mark.asyncio
    async def test_logout_error_still_clears_state(self):
        app = web.Application()
        app.router.add_post("/rest/logout", logout_error)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        client = _authenticated_client(tc.server.host)
        client._session = tc.session
        client.base_url = f"http://{tc.server.host}:{tc.server.port}"
        await client.logout()
        assert client.session_token is None
        await tc.close()

    @pytest.mark.asyncio
    async def test_context_manager_creates_and_closes_session(self):
        app = web.Application()
        app.router.add_post("/rest/login", login_ok)
        app.router.add_post("/rest/logout", logout_200)
        server = TestServer(app)
        tc = TestClient(server)
        await tc.start_server()
        async with BAOSRestClient(tc.server.host, port=tc.server.port, use_https=False) as client:
            assert client._session is not None
        await tc.close()


# ── Mock-based tests (no socket) ─────────────────────────────────────────────


class TestBAOSRestClientMockedHTTP:
    """Cover HTTP response branches using MagicMock — no socket required."""

    @staticmethod
    def _make_response(status=200, text="", json_data=None):
        resp = MagicMock()
        resp.status = status
        resp.text = AsyncMock(return_value=text)
        resp.json = AsyncMock(return_value=json_data)
        resp.headers = {}
        return resp

    @staticmethod
    def _wire_cm(session_mock, response, method="post"):
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=response)
        cm.__aexit__ = AsyncMock(return_value=False)
        getattr(session_mock, method).return_value = cm

    def _authenticated_client(self):
        client = BAOSRestClient("10.0.0.1", use_https=False)
        client.session_token = "fake_token"
        client.session_expires = datetime.now() + timedelta(hours=1)
        client._session = MagicMock()
        return client

    # ── login() ──────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_login_success_with_existing_session(self):
        client = BAOSRestClient("10.0.0.1", use_https=False)
        client._session = MagicMock()
        resp = self._make_response(200, text="my_token")
        self._wire_cm(client._session, resp, "post")
        token = await client.login("admin", "pass")
        assert token == "my_token"
        assert client.session_token == "my_token"
        assert client.session_expires is not None

    @pytest.mark.asyncio
    async def test_login_401_raises(self):
        client = BAOSRestClient("10.0.0.1", use_https=False)
        client._session = MagicMock()
        resp = self._make_response(401, text="Unauthorized")
        self._wire_cm(client._session, resp, "post")
        with pytest.raises(AuthenticationError, match="Invalid username"):
            await client.login("bad", "creds")

    @pytest.mark.asyncio
    async def test_login_500_raises(self):
        client = BAOSRestClient("10.0.0.1", use_https=False)
        client._session = MagicMock()
        resp = self._make_response(500)
        self._wire_cm(client._session, resp, "post")
        with pytest.raises(AuthenticationError, match="status 500"):
            await client.login("admin", "pass")

    @pytest.mark.asyncio
    async def test_login_empty_token_raises(self):
        client = BAOSRestClient("10.0.0.1", use_https=False)
        client._session = MagicMock()
        resp = self._make_response(200, text="   ")
        self._wire_cm(client._session, resp, "post")
        with pytest.raises(AuthenticationError, match="No session cookie"):
            await client.login("admin", "pass")

    @pytest.mark.asyncio
    async def test_login_client_error_raises(self):
        import aiohttp

        client = BAOSRestClient("10.0.0.1", use_https=False)
        client._session = MagicMock()
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("net"))
        cm.__aexit__ = AsyncMock(return_value=False)
        client._session.post.return_value = cm
        with pytest.raises(AuthenticationError, match="Network error"):
            await client.login("admin", "pass")

    @pytest.mark.asyncio
    async def test_login_creates_session_when_none(self):
        """When _session is None, login() creates a ClientSession."""
        client = BAOSRestClient("10.0.0.1", use_https=False)
        assert client._session is None

        mock_session = MagicMock()
        resp = self._make_response(200, text="token_new")
        self._wire_cm(mock_session, resp, "post")

        with (
            patch("aiohttp.ClientSession", return_value=mock_session),
            patch("aiohttp.TCPConnector"),
        ):
            token = await client.login("admin", "pass")

        assert token == "token_new"
        assert client._session is not None

    # ── logout() ─────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_logout_200_clears_state(self):
        client = self._authenticated_client()
        client.tunneling_enabled = True
        resp = self._make_response(200)
        self._wire_cm(client._session, resp, "post")
        await client.logout()
        assert client.session_token is None
        assert client.tunneling_enabled is False

    @pytest.mark.asyncio
    async def test_logout_204_clears_state(self):
        client = self._authenticated_client()
        resp = self._make_response(204)
        self._wire_cm(client._session, resp, "post")
        await client.logout()
        assert client.session_token is None

    @pytest.mark.asyncio
    async def test_logout_error_status_still_clears(self):
        client = self._authenticated_client()
        resp = self._make_response(500)
        self._wire_cm(client._session, resp, "post")
        await client.logout()
        assert client.session_token is None

    @pytest.mark.asyncio
    async def test_logout_client_error_still_clears(self):
        import aiohttp

        client = self._authenticated_client()
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("net"))
        cm.__aexit__ = AsyncMock(return_value=False)
        client._session.post.return_value = cm
        await client.logout()
        assert client.session_token is None

    # ── enable_tunneling() ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_enable_tunneling_204_success(self):
        client = self._authenticated_client()
        resp = self._make_response(204)
        self._wire_cm(client._session, resp, "put")
        with patch(
            "custom_components.luxor_living.rest_client.get_rest_api_circuit_breaker"
        ) as mock_cb:
            cb = MagicMock()

            async def relay_et(fn):
                return await fn()  # noqa: E704

            cb.call = relay_et
            mock_cb.return_value = cb
            result = await client.enable_tunneling()
        assert result is True
        assert client.tunneling_enabled is True

    @pytest.mark.asyncio
    async def test_enable_tunneling_200_json_success(self):
        client = self._authenticated_client()
        resp = self._make_response(200, json_data={"enabled": True})
        self._wire_cm(client._session, resp, "put")
        with patch(
            "custom_components.luxor_living.rest_client.get_rest_api_circuit_breaker"
        ) as mock_cb:
            cb = MagicMock()

            async def relay_et200(fn):
                return await fn()  # noqa: E704

            cb.call = relay_et200
            mock_cb.return_value = cb
            result = await client.enable_tunneling()
        assert result is True

    @pytest.mark.asyncio
    async def test_enable_tunneling_401_raises_auth_error(self):
        client = self._authenticated_client()
        resp = self._make_response(401)
        self._wire_cm(client._session, resp, "put")
        with patch(
            "custom_components.luxor_living.rest_client.get_rest_api_circuit_breaker"
        ) as mock_cb:
            cb = MagicMock()

            async def relay_et401(fn):
                return await fn()  # noqa: E704

            cb.call = relay_et401
            mock_cb.return_value = cb
            with pytest.raises(AuthenticationError):
                await client.enable_tunneling()

    @pytest.mark.asyncio
    async def test_enable_tunneling_403_raises_tunneling_error(self):
        client = self._authenticated_client()
        resp = self._make_response(403, text="Forbidden")
        self._wire_cm(client._session, resp, "put")
        with patch(
            "custom_components.luxor_living.rest_client.get_rest_api_circuit_breaker"
        ) as mock_cb:
            cb = MagicMock()

            async def relay_et403(fn):
                return await fn()  # noqa: E704

            cb.call = relay_et403
            mock_cb.return_value = cb
            with pytest.raises(TunnelingError, match="Forbidden"):
                await client.enable_tunneling()

    @pytest.mark.asyncio
    async def test_enable_tunneling_500_raises_tunneling_error(self):
        client = self._authenticated_client()
        resp = self._make_response(500, text="Internal Error")
        self._wire_cm(client._session, resp, "put")
        with patch(
            "custom_components.luxor_living.rest_client.get_rest_api_circuit_breaker"
        ) as mock_cb:
            cb = MagicMock()

            async def relay_et500(fn):
                return await fn()  # noqa: E704

            cb.call = relay_et500
            mock_cb.return_value = cb
            with pytest.raises(TunnelingError):
                await client.enable_tunneling()

    # ── disable_tunneling() ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_disable_tunneling_200_success(self):
        client = self._authenticated_client()
        client.tunneling_enabled = True
        resp = self._make_response(200)
        self._wire_cm(client._session, resp, "put")
        with patch(
            "custom_components.luxor_living.rest_client.get_rest_api_circuit_breaker"
        ) as mock_cb:
            cb = MagicMock()

            async def relay_dt200(fn):
                return await fn()  # noqa: E704

            cb.call = relay_dt200
            mock_cb.return_value = cb
            result = await client.disable_tunneling()
        assert result is True
        assert client.tunneling_enabled is False

    @pytest.mark.asyncio
    async def test_disable_tunneling_204_success(self):
        client = self._authenticated_client()
        resp = self._make_response(204)
        self._wire_cm(client._session, resp, "put")
        with patch(
            "custom_components.luxor_living.rest_client.get_rest_api_circuit_breaker"
        ) as mock_cb:
            cb = MagicMock()

            async def relay_dt204(fn):
                return await fn()  # noqa: E704

            cb.call = relay_dt204
            mock_cb.return_value = cb
            result = await client.disable_tunneling()
        assert result is True

    @pytest.mark.asyncio
    async def test_disable_tunneling_500_returns_false(self):
        client = self._authenticated_client()
        resp = self._make_response(500, text="err")
        self._wire_cm(client._session, resp, "put")
        with patch(
            "custom_components.luxor_living.rest_client.get_rest_api_circuit_breaker"
        ) as mock_cb:
            cb = MagicMock()

            async def relay_dt500(fn):
                return await fn()  # noqa: E704

            cb.call = relay_dt500
            mock_cb.return_value = cb
            result = await client.disable_tunneling()
        assert result is False

    @pytest.mark.asyncio
    async def test_disable_tunneling_exception_returns_false(self):
        client = self._authenticated_client()
        with patch(
            "custom_components.luxor_living.rest_client.get_rest_api_circuit_breaker"
        ) as mock_cb:
            cb = MagicMock()
            cb.call = AsyncMock(side_effect=RuntimeError("CB open"))
            mock_cb.return_value = cb
            result = await client.disable_tunneling()
        assert result is False

    # ── get_tunneling_status() ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_tunneling_status_200(self):
        client = self._authenticated_client()
        resp = self._make_response(
            200, json_data={"enabled": True, "connectedClients": 1, "maxSlots": 4}
        )
        self._wire_cm(client._session, resp, "get")
        result = await client.get_tunneling_status()
        assert result["enabled"] is True

    @pytest.mark.asyncio
    async def test_get_tunneling_status_non_200_returns_default(self):
        client = self._authenticated_client()
        resp = self._make_response(500)
        self._wire_cm(client._session, resp, "get")
        result = await client.get_tunneling_status()
        assert result == {"enabled": False, "connectedClients": 0, "maxSlots": 1}

    # ── __aenter__ / __aexit__ ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_aenter_creates_session(self):
        with patch("aiohttp.ClientSession") as mock_cls, patch("aiohttp.TCPConnector"):
            mock_cls.return_value = MagicMock()
            client = BAOSRestClient("10.0.0.1", use_https=False)
            result = await client.__aenter__()
            assert result is client
            assert client._session is not None

    @pytest.mark.asyncio
    async def test_aexit_closes_session(self):
        client = BAOSRestClient("10.0.0.1", use_https=False)
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        client._session = mock_session
        await client.__aexit__(None, None, None)
        mock_session.close.assert_awaited_once()
