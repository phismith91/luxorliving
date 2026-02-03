"""Tests for BAOS REST API Client."""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from custom_components.luxor_living.rest_client import BAOSRestClient
from custom_components.luxor_living.rest_exceptions import AuthenticationError


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
