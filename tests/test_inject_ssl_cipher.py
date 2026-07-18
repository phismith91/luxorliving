"""Regression guards for the IP1 legacy-TLS requirement.

The IP1 gateway negotiates a legacy cipher that modern OpenSSL refuses at its
default security level. Two independent regressions have shipped from forgetting
this:

* v1.2.0-rc.1 injected Home Assistant's shared session with only
  ``verify_ssl=False`` (no ``ssl_cipher``) → ``SSLV3_ALERT_HANDSHAKE_FAILURE``.
* v1.1.15-rc.1 / v1.2.0-rc.2 dropped ``set_ciphers("DEFAULT:@SECLEVEL=0")`` from
  the owned-session fallback context, with an (untested) comment claiming it was
  unnecessary — the same handshake failure, latent.

Both are guarded here so neither can silently come back. The required posture is:

* owned-session fallback: :func:`_make_ssl_context` must set
  ``DEFAULT:@SECLEVEL=0`` and ``CERT_NONE``;
* every injected-session call site must pass
  ``verify_ssl=False, ssl_cipher=SSLCipherList.INSECURE`` (HA's
  ``SSLCipherList.INSECURE`` == ``"DEFAULT:@SECLEVEL=0"``).

These are deterministic (no sockets), so they run in the gated CI suite — the
exact place the previous regressions slipped through. A live end-to-end TLS check
against real legacy-cipher hardware remains a manual pre-release step (the IP1's
specific cipher cannot be reproduced in CI's modern OpenSSL build).
"""

import ssl
from pathlib import Path

import pytest
from homeassistant.util.ssl import SSL_CIPHER_LISTS, SSLCipherList

import custom_components.luxor_living.rest_client as rest_client_mod
from custom_components.luxor_living.rest_client import _make_ssl_context

COMPONENT_DIR = Path(rest_client_mod.__file__).parent


def test_make_ssl_context_sets_seclevel0(monkeypatch):
    """Owned-session fallback context must enable legacy ciphers (@SECLEVEL=0)."""
    captured: dict[str, str] = {}
    real_create = ssl.create_default_context

    def spy_create(*args, **kwargs):
        ctx = real_create(*args, **kwargs)
        real_set = ctx.set_ciphers

        def spy_set(cipher_string: str):
            captured["ciphers"] = cipher_string
            return real_set(cipher_string)

        ctx.set_ciphers = spy_set  # type: ignore[method-assign]
        return ctx

    monkeypatch.setattr(rest_client_mod.ssl, "create_default_context", spy_create)

    ctx = _make_ssl_context()

    assert (
        captured.get("ciphers") == "DEFAULT:@SECLEVEL=0"
    ), "IP1 needs @SECLEVEL=0; dropping it caused SSLV3_ALERT_HANDSHAKE_FAILURE"
    assert ctx.verify_mode == ssl.CERT_NONE
    assert ctx.check_hostname is False


def test_seclevel0_matches_ha_insecure_cipher():
    """Our fallback string must equal what HA's SSLCipherList.INSECURE applies."""
    assert SSL_CIPHER_LISTS[SSLCipherList.INSECURE] == "DEFAULT:@SECLEVEL=0"


# Only these talk to the IP1's REST API (host from config) — they need the
# legacy-TLS posture. push_client is deliberately excluded: it connects to a
# user-configured forwarder (push_ws_url), not the IP1, and must keep normal TLS.
IP1_REST_CALL_SITES = ["knx_gateway.py", "config_flow.py", "repairs.py"]


@pytest.mark.parametrize("filename", IP1_REST_CALL_SITES)
def test_ip1_call_sites_inject_insecure_cipher(filename):
    """Every IP1-REST call site must request the INSECURE cipher list.

    Static guard: the exact regression in v1.2.0-rc.1 was injecting a session
    with ``verify_ssl=False`` but WITHOUT ``ssl_cipher=INSECURE``.
    """
    source = (COMPONENT_DIR / filename).read_text(encoding="utf-8")
    assert "async_get_clientsession" in source, f"{filename} no longer injects a session"
    assert "ssl_cipher=SSLCipherList.INSECURE" in source, (
        f"{filename} injects a session without ssl_cipher=SSLCipherList.INSECURE "
        "— this reintroduces the IP1 handshake regression"
    )
    assert "verify_ssl=False" in source, f"{filename} must disable cert verification for the IP1"


def test_push_client_does_not_downgrade_tls():
    """push_client must NOT carry the IP1 legacy-TLS downgrade.

    ``push_ws_url`` is an arbitrary, possibly internet-facing, token-authenticated
    endpoint — disabling cert verification / lowering SECLEVEL there would be a
    security regression (it was, briefly, in v1.2.0-rc.3).
    """
    source = (COMPONENT_DIR / "push_client.py").read_text(encoding="utf-8")
    assert "async_get_clientsession" in source, "push_client should use HA's shared session"
    assert "ssl_cipher" not in source, "push_client must not weaken ciphers for the forwarder"
    assert "verify_ssl=False" not in source, "push_client must keep TLS verification"
