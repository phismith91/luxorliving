"""Exhaustive event-sequence ("chaos") tests for the gateway connection flag.

See event_harness.py. The named tests pin the three findings the harness
produced (2026-11-21), each with its shortest reproducing sequence. The
exhaustive test then checks ALL invariants over every sequence up to
CHAOS_MAX_LEN ops (default 4; 5-6 take 20-70 s).
"""

import os

import pytest

from tests.chaos.event_harness import run_sequence, sequences

pytestmark = pytest.mark.asyncio

MAX_LEN = int(os.environ.get("CHAOS_MAX_LEN", "4"))


async def test_all_sequences_keep_connected_flag_consistent():
    """No sequence may hang, leak the lock, lie about availability or stay stuck."""
    failures = []
    for seq in sequences(MAX_LEN):
        bad = await run_sequence(seq)
        if bad:
            failures.append((" ".join(seq), bad))
    assert not failures, failures[:5]


async def test_issue_247_refresh_then_second_disconnect_restores_flag():
    """#247: refresh done, DISCONNECTED, CONNECTED inside the cooldown."""
    assert await run_sequence(("RS", "FIN", "DISC", "CONN")) == []


async def test_refresh_must_not_claim_connected_while_xknx_down():
    """DISC arrives during a refresh; refresh then sets connected=True unconditionally."""
    assert await run_sequence(("RS", "DISC")) == []


async def test_reconnect_reauth_must_not_claim_connected_after_later_disconnect():
    """CONN starts re-auth, DISC arrives meanwhile, re-auth completes and overwrites False."""
    assert await run_sequence(("DISC", "CONN", "DISC")) == []


async def test_failed_refresh_must_not_leave_entities_stuck_unavailable():
    """Refresh fails after logout(): xknx up, tunneling off, nothing retries for 4 h."""
    assert await run_sequence(("RF",)) == []
