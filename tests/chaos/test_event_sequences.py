"""Exhaustive event-sequence ("chaos") tests for the gateway connection flag.

See event_harness.py. Hard guards must always pass. The xfail tests document
open findings from the spike (2026-11-21): when one is fixed, the strict xfail
flips to XPASS and fails, which is the signal to turn it into a normal test.
"""

import os

import pytest

from tests.chaos.event_harness import run_sequence, sequences

pytestmark = pytest.mark.asyncio

MAX_LEN = int(os.environ.get("CHAOS_MAX_LEN", "4"))
HARD_GUARDS = ("LOCK:", "LIVENESS: stuck unavailable (xknx up, tunneling on")


async def test_no_hang_no_lock_leak_and_no_stuck_with_tunneling_on():
    """Regression guard for #247: xknx up + tunneling on must never stay unavailable."""
    failures = []
    for seq in sequences(MAX_LEN):
        bad = [v for v in await run_sequence(seq) if v.startswith(HARD_GUARDS)]
        if bad:
            failures.append((" ".join(seq), bad))
    assert not failures, failures[:5]


@pytest.mark.xfail(strict=True, reason="finding: refresh sets connected=True without checking xknx")
async def test_refresh_must_not_claim_connected_while_xknx_down():
    """DISC arrives during a refresh; refresh then sets connected=True unconditionally."""
    assert not [v for v in await run_sequence(("RS", "DISC")) if v.startswith("SAFETY")]


@pytest.mark.xfail(strict=True, reason="finding: re-auth sets connected=True after a later DISC")
async def test_reconnect_reauth_must_not_claim_connected_after_later_disconnect():
    """CONN starts re-auth, DISC arrives meanwhile, re-auth completes and overwrites False."""
    assert not [v for v in await run_sequence(("DISC", "CONN", "DISC")) if v.startswith("SAFETY")]


@pytest.mark.xfail(
    strict=True, reason="finding: failed refresh leaves tunneling off until next 4h cycle"
)
async def test_failed_refresh_must_not_leave_entities_stuck_unavailable():
    """Refresh fails after logout(): xknx up, tunneling off, nothing retries for 4 h."""
    assert not [v for v in await run_sequence(("RF",)) if v.startswith("LIVENESS")]
