"""Tests for BAOS REST API Client."""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from custom_components.luxor_living.rest_client import (
    AuthenticationError,
    BAOSRestClient,
)


async def login_handler(request):
    """Mock login endpoint - returns plain text cookie token."""
    data = await request.json()
    if data.get("username") == "admin" and data.get("password") == "admin":
        # API returns plain text cookie token (not JSON)
        return web.Response(text="3c8b531737cbd849bccf15bb9ef09d9c")
    return web.Response(status=401)


async def logout_handler(request):
    """Mock logout endpoint."""
    return web.Response(status=204)


async def tunneling_handler(request):
    """Mock tunneling endpoint - returns 204 on success."""
    if request.method == "PUT":
        # PUT returns 204 (No Content) on success
        return web.Response(status=204)
    else:  # GET
        return web.json_response({"enabled": True})


@pytest_asyncio.fixture
async def mock_baos_server():
    """Create mock BAOS REST API server."""
    app = web.Application()
    app.router.add_post("/rest/login", login_handler)  # Correct endpoint
    app.router.add_post("/rest/logout", logout_handler)
    app.router.add_put("/rest/device/authtunneling", tunneling_handler)
    app.router.add_get("/rest/device/authtunneling", tunneling_handler)

    server = TestServer(app)
    client = TestClient(server)

    await client.start_server()
    yield client
    await client.close()


@pytest.mark.enable_socket
class TestBAOSRestClient:
    """Test REST API Client."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_baos_server):
        """Test successful login."""
        # Use real server URL
        base_url = str(mock_baos_server.server.make_url(""))
        host = base_url.replace("http://", "").split(":")[0]
        port = int(base_url.split(":")[-1].rstrip("/"))

        # Test server uses HTTP, so disable HTTPS
        client = BAOSRestClient(host, port=port, use_https=False)

        async with client:
            token = await client.login("admin", "admin")

            # API returns plain text cookie token from mock
            assert token == "3c8b531737cbd849bccf15bb9ef09d9c"
            assert client.session_token == "3c8b531737cbd849bccf15bb9ef09d9c"
            assert client.is_authenticated is True
            assert client.session_expires > datetime.now()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_baos_server):
        """Test login with invalid credentials."""
        base_url = str(mock_baos_server.server.make_url(""))
        host = base_url.replace("http://", "").split(":")[0]
        port = int(base_url.split(":")[-1].rstrip("/"))

        # Test server uses HTTP, so disable HTTPS
        client = BAOSRestClient(host, port=port, use_https=False)

        async with client:
            with pytest.raises(AuthenticationError, match="Invalid username or password"):
                await client.login("admin", "wrong")

    @pytest.mark.asyncio
    async def test_enable_tunneling_success(self, mock_baos_server):
        """Test enabling tunneling."""
        base_url = str(mock_baos_server.server.make_url(""))
        host = base_url.replace("http://", "").split(":")[0]
        port = int(base_url.split(":")[-1].rstrip("/"))

        # Test server uses HTTP, so disable HTTPS
        client = BAOSRestClient(host, port=port, use_https=False)

        async with client:
            await client.login("admin", "admin")
            result = await client.enable_tunneling()

            assert result is True
            assert client.tunneling_enabled is True

    @pytest.mark.asyncio
    async def test_enable_tunneling_not_authenticated(self):
        """Test enabling tunneling without login."""
        client = BAOSRestClient("192.168.1.3")

        with pytest.raises(AuthenticationError, match="Not logged in"):
            await client.enable_tunneling()

    @pytest.mark.asyncio
    async def test_enable_tunneling_session_expired(self):
        """Test enabling tunneling with expired session."""
        client = BAOSRestClient("192.168.1.3")
        client.session_token = "expired_token"
        client.session_expires = datetime.now() - timedelta(minutes=1)  # Expired

        with pytest.raises(AuthenticationError, match="Session expired"):
            await client.enable_tunneling()

    @pytest.mark.asyncio
    async def test_disable_tunneling(self, mock_baos_server):
        """Test disabling tunneling."""
        base_url = str(mock_baos_server.server.make_url(""))
        host = base_url.replace("http://", "").split(":")[0]
        port = int(base_url.split(":")[-1].rstrip("/"))

        # Test server uses HTTP, so disable HTTPS
        client = BAOSRestClient(host, port=port, use_https=False)

        async with client:
            await client.login("admin", "admin")
            await client.enable_tunneling()
            result = await client.disable_tunneling()

            assert result is True
            assert client.tunneling_enabled is False

    @pytest.mark.asyncio
    async def test_logout(self, mock_baos_server):
        """Test logout."""
        base_url = str(mock_baos_server.server.make_url(""))
        host = base_url.replace("http://", "").split(":")[0]
        port = int(base_url.split(":")[-1].rstrip("/"))

        # Test server uses HTTP, so disable HTTPS
        client = BAOSRestClient(host, port=port, use_https=False)

        async with client:
            await client.login("admin", "admin")
            await client.logout()

            assert client.session_token is None
            assert client.session_expires is None
            assert client.tunneling_enabled is False

    @pytest.mark.asyncio
    async def test_get_tunneling_status(self, mock_baos_server):
        """Test getting tunneling status."""
        base_url = str(mock_baos_server.server.make_url(""))
        host = base_url.replace("http://", "").split(":")[0]
        port = int(base_url.split(":")[-1].rstrip("/"))

        # Test server uses HTTP, so disable HTTPS
        client = BAOSRestClient(host, port=port, use_https=False)

        async with client:
            await client.login("admin", "admin")
            status = await client.get_tunneling_status()

            # Mock returns simplified response
            assert status["enabled"] is True

    def test_diagnostics(self):
        """Test diagnostics output."""
        client = BAOSRestClient("192.168.1.3", port=80, use_https=False)
        client.session_token = "test_token"
        client.session_expires = datetime.now() + timedelta(hours=1)
        client.tunneling_enabled = True

        diag = client.get_diagnostics()

        assert diag["host"] == "192.168.1.3"
        assert diag["port"] == 80
        assert diag["use_https"] is False
        assert diag["authenticated"] is True
        assert diag["tunneling_enabled"] is True
        assert "session_expires" in diag

    def test_https_by_default(self):
        """Test that HTTPS is used by default."""
        client = BAOSRestClient("192.168.1.3")
        assert client.use_https is True
        assert client.port == 443
        assert client.base_url == "https://192.168.1.3:443"

    def test_http_fallback(self):
        """Test HTTP fallback when explicitly disabled."""
        client = BAOSRestClient("192.168.1.3", port=80, use_https=False)
        assert client.use_https is False
        assert client.port == 80
        assert client.base_url == "http://192.168.1.3:80"

    def test_is_authenticated_no_token(self):
        """Test authentication check without token."""
        client = BAOSRestClient("192.168.1.3")
        assert client.is_authenticated is False

    def test_is_authenticated_expired(self):
        """Test authentication check with expired session."""
        client = BAOSRestClient("192.168.1.3")
        client.session_token = "test_token"
        client.session_expires = datetime.now() - timedelta(minutes=1)

        assert client.is_authenticated is False

    def test_is_authenticated_valid(self):
        """Test authentication check with valid session."""
        client = BAOSRestClient("192.168.1.3")
        client.session_token = "test_token"
        client.session_expires = datetime.now() + timedelta(hours=1)

        assert client.is_authenticated is True


@pytest.mark.smoke
class TestLogoutAuditFix:
    """Test for audit-fix: logout null-session guard."""

    @pytest.mark.asyncio
    async def test_logout_skips_when_session_is_none(self):
        """logout() must return early when _session is None, even if session_token is set."""
        from custom_components.luxor_living.rest_client import BAOSRestClient

        client = BAOSRestClient("192.168.1.3")
        client.session_token = "orphaned_token"
        client._session = None  # session never initialized

        # Must not raise AttributeError
        await client.logout()

        assert client.session_token is None  # still cleaned up


class TestRestClientMutationTargets:
    """Smoke tests targeting surviving mutants in BAOSRestClient."""

    # ── __init__: default values and attribute mutations ──────────────────

    @pytest.mark.smoke
    def test_default_port_is_443(self):
        """Kill mutmut_1: default port 443 → 444."""
        import inspect

        from custom_components.luxor_living.rest_client import BAOSRestClient

        sig = inspect.signature(BAOSRestClient.__init__)
        assert sig.parameters["port"].default == 443

    @pytest.mark.smoke
    def test_default_use_https_is_true(self):
        """Kill mutmut_2: use_https=True → False."""
        import inspect

        from custom_components.luxor_living.rest_client import BAOSRestClient

        sig = inspect.signature(BAOSRestClient.__init__)
        assert sig.parameters["use_https"].default is True

    @pytest.mark.smoke
    def test_host_stored(self):
        """Kill mutmut_3: self.host = None."""
        from custom_components.luxor_living.rest_client import BAOSRestClient

        c = BAOSRestClient("192.168.1.3")
        assert c.host == "192.168.1.3"

    @pytest.mark.smoke
    def test_port_stored(self):
        """Kill mutmut_4: self.port = None."""
        from custom_components.luxor_living.rest_client import BAOSRestClient

        c = BAOSRestClient("192.168.1.3", port=8080)
        assert c.port == 8080

    @pytest.mark.smoke
    def test_base_url_uses_https_when_true(self):
        """Kill mutmut_2 (use_https): base_url must start with https."""
        from custom_components.luxor_living.rest_client import BAOSRestClient

        c = BAOSRestClient("192.168.1.3", use_https=True)
        assert c.base_url.startswith("https://")

    @pytest.mark.smoke
    def test_base_url_uses_http_when_false(self):
        """Complementary: http when use_https=False (boundary check)."""
        from custom_components.luxor_living.rest_client import BAOSRestClient

        c = BAOSRestClient("192.168.1.3", use_https=False)
        assert c.base_url.startswith("http://")

    # ── logout: guard mutations ───────────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_logout_with_token_but_no_session_clears_token(self):
        """Kill mutmut_1: 'or not _session' → 'and not _session'.

        With 'and': if session_token is set AND _session is None, the guard
        is False (both must be falsy for early return) → crashes on _session.post.
        """
        from custom_components.luxor_living.rest_client import BAOSRestClient

        c = BAOSRestClient("192.168.1.3")
        c.session_token = "tok"
        c._session = None
        await c.logout()
        assert c.session_token is None  # must be cleared

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_logout_clears_tunneling_enabled(self):
        """Kill mutmut_10: tunneling_enabled = False → None."""
        from custom_components.luxor_living.rest_client import BAOSRestClient

        c = BAOSRestClient("192.168.1.3")
        c.session_token = None  # no session → early return path
        c.tunneling_enabled = True
        await c.logout()
        assert c.tunneling_enabled is False  # not None
