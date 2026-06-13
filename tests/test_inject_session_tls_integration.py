"""End-to-end TLS integration test for the injected (shared) session path.

The Platinum websession-injection change means that in production
``BAOSRestClient`` no longer builds its own ``ssl_context``; it receives Home
Assistant's shared session from ``async_get_clientsession(hass, verify_ssl=False)``
through the ``session=`` constructor argument. No existing ``enable_socket`` test
exercised that constructor path over a *real* self-signed-TLS socket — the older
integration tests use plain HTTP and assign ``client._session`` directly,
bypassing the ``_owns_session`` ownership logic.

This test closes that gap without any hardware:

* a local aiohttp server speaks HTTPS with a throwaway self-signed certificate
  (mirroring the IP1 gateway),
* the client is given a session built like ``async_get_clientsession(..., verify_ssl=False)``
  (``TCPConnector(ssl=False)`` → no certificate verification), injected via
  ``session=``,
* the full ``login`` → ``async_get_datapoints`` flow runs over TLS, proving the
  handshake, the auth headers and the per-request timeout all work on the shared
  session, and
* ``__aexit__`` must NOT close the injected (HA-owned) session.

Marked ``enable_socket`` because it opens real TLS sockets (same reason as the
other REST integration tests); excluded from the gated CI suite.
"""

import datetime
import ipaddress
import ssl
import tempfile
from pathlib import Path

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from custom_components.luxor_living.rest_client import BAOSRestClient

TOKEN = "tls_session_token_xyz"


def _write_self_signed_cert(tmp: Path) -> tuple[Path, Path]:
    """Create a throwaway self-signed cert/key for 127.0.0.1 (server side only)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path = tmp / "cert.pem"
    key_path = tmp / "key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path


def _build_app() -> web.Application:
    """Minimal BAOS-like server: login returns a cookie token, datapoints needs auth."""

    async def login(request: web.Request) -> web.Response:
        body = await request.json()
        if body.get("username") != "admin" or body.get("password") != "secret":
            return web.Response(status=401, text="Unauthorized")
        # IP1 returns the session token as a plain-text cookie string.
        return web.Response(status=200, text=TOKEN)

    async def datapoints(request: web.Request) -> web.Response:
        # The client must forward the auth header it built from the login token.
        auth = request.headers.get("Authorization", "")
        if f"Token token={TOKEN}" not in auth:
            return web.Response(status=401, text="missing/!bad auth")
        return web.json_response({"datapoints": [{"id": 1, "url": "/rest/datapoints/1"}]})

    app = web.Application()
    app.router.add_post("/rest/login", login)
    app.router.add_get("/rest/datapoints", datapoints)
    return app


@pytest.mark.enable_socket
@pytest.mark.asyncio
async def test_injected_session_full_tls_flow(socket_enabled):
    """login + get_datapoints succeed over self-signed TLS via an injected session."""
    with tempfile.TemporaryDirectory() as td:
        cert_path, key_path = _write_self_signed_cert(Path(td))
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))

        server = TestServer(_build_app(), scheme="https", host="127.0.0.1")
        await server.start_server(ssl=ssl_ctx)
        try:
            # Mirror async_get_clientsession(hass, verify_ssl=False): a session whose
            # connector performs NO certificate verification (ssl=False).
            shared = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
            try:
                client = BAOSRestClient(
                    server.host, port=server.port, use_https=True, session=shared
                )
                assert client._owns_session is False

                token = await client.login("admin", "secret")
                assert token == TOKEN
                assert client.session_token == TOKEN

                datapoints = await client.async_get_datapoints()
                assert datapoints == [{"id": 1, "url": "/rest/datapoints/1"}]
            finally:
                await shared.close()
        finally:
            await server.close()


@pytest.mark.enable_socket
@pytest.mark.asyncio
async def test_injected_session_not_closed_on_context_exit():
    """Exiting the client must leave the HA-owned shared session open and usable."""
    shared = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
    try:
        async with BAOSRestClient("127.0.0.1", session=shared) as client:
            assert client._session is shared
        # __aexit__ ran; the injected session must still be open.
        assert shared.closed is False
    finally:
        await shared.close()
