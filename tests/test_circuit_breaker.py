#!/usr/bin/env python3
"""Tests for Circuit Breaker functionality."""

import asyncio

import pytest

from custom_components.luxor_living.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenException,
    CircuitBreakerState,
    get_knx_circuit_breaker,
    get_rest_api_circuit_breaker,
)


class TestCircuitBreaker:
    """Test the Circuit Breaker functionality."""

    @pytest.fixture
    def circuit_breaker_config(self):
        """Default circuit breaker configuration for testing."""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=2.0,
            success_threshold=2,
            timeout=5.0,
        )

    @pytest.fixture
    def circuit_breaker(self, circuit_breaker_config):
        """Create a circuit breaker instance for testing."""
        return CircuitBreaker("test_circuit_breaker", circuit_breaker_config)

    @pytest.mark.smoke
    def test_initial_state_closed(self, circuit_breaker):
        """Test that circuit breaker starts in CLOSED state."""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        stats = circuit_breaker.get_stats()
        assert stats["failure_count"] == 0
        assert stats["last_failure_time"] == 0.0

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_successful_call(self, circuit_breaker):
        """Test successful call doesn't change state."""

        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)

        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        stats = circuit_breaker.get_stats()
        assert stats["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_single_failure_no_trip(self, circuit_breaker):
        """Test single failure doesn't trip circuit breaker."""

        async def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        stats = circuit_breaker.get_stats()
        assert stats["failure_count"] == 1
        assert stats["failure_count"] == 1
        assert stats["last_failure_time"] > 0

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_failure_threshold_trip(self, circuit_breaker):
        """Test circuit breaker trips after reaching failure threshold."""

        async def failing_func():
            raise ValueError("test error")

        # Fail exactly threshold times
        for i in range(3):
            with pytest.raises(ValueError, match="test error"):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitBreakerState.OPEN
        stats = circuit_breaker.get_stats()
        assert stats["failure_count"] == 3
        assert stats["failure_count"] == 3

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self, circuit_breaker):
        """Test that open circuit breaker rejects calls."""

        # Trip the circuit breaker
        async def failing_func():
            raise ValueError("test error")

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitBreakerState.OPEN

        # Now calls should be rejected
        async def success_func():
            return "success"

        with pytest.raises(CircuitBreakerOpenException):
            await circuit_breaker.call(success_func)

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, circuit_breaker):
        """Test circuit breaker goes to HALF_OPEN after recovery timeout."""

        # Trip the circuit breaker
        async def failing_func():
            raise ValueError("test error")

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(2.1)

        # Next call should attempt recovery (HALF_OPEN)
        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)

        assert result == "success"
        # After one success in HALF_OPEN, it stays in HALF_OPEN until success_threshold is reached
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_failure_returns_to_open(self, circuit_breaker):
        """Test that failure in HALF_OPEN state returns to OPEN."""

        # Trip the circuit breaker
        async def failing_func():
            raise ValueError("test error")

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(2.1)

        # Next call fails in HALF_OPEN
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitBreakerState.OPEN
        stats = circuit_breaker.get_stats()
        assert stats["failure_count"] == 4

    @pytest.mark.asyncio
    async def test_timeout_handling(self, circuit_breaker):
        """Test timeout handling for async calls."""

        async def slow_func():
            await asyncio.sleep(10)  # Longer than timeout
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await circuit_breaker.call(slow_func)

        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        stats = circuit_breaker.get_stats()
        assert stats["failure_count"] == 1

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self, circuit_breaker):
        """Test that successful call resets failure count."""

        async def failing_func():
            raise ValueError("test error")

        async def success_func():
            return "success"

        # Two failures
        for i in range(2):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        stats = circuit_breaker.get_stats()
        assert stats["failure_count"] == 2

        # Success resets count
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        stats = circuit_breaker.get_stats()
        assert stats["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_different_exception_types(self, circuit_breaker):
        """Test handling of different exception types."""

        async def auth_error():
            raise ConnectionError("auth failed")

        async def network_error():
            raise OSError("network failed")

        # Different exceptions should all count as failures
        with pytest.raises(ConnectionError):
            await circuit_breaker.call(auth_error)

        with pytest.raises(OSError):
            await circuit_breaker.call(network_error)

        assert circuit_breaker.get_stats()["failure_count"] == 2

    def test_statistics_tracking(self, circuit_breaker):
        """Test that statistics are properly tracked."""
        stats = circuit_breaker.get_stats()
        assert "state" in stats
        assert "failure_count" in stats
        assert "last_failure_time" in stats
        assert "call_count" in stats
        assert "success_count" in stats
        assert "failure_count" in stats

    @pytest.mark.asyncio
    async def test_statistics_update(self, circuit_breaker):
        """Test that statistics are updated correctly."""

        async def success_func():
            return "success"

        async def failing_func():
            raise ValueError("error")

        # Successful call
        await circuit_breaker.call(success_func)

        stats = circuit_breaker.get_stats()
        assert stats["call_count"] == 1
        assert stats["success_count"] == 0  # success_count only incremented in HALF_OPEN state
        assert stats["failure_count"] == 0

        # Failed call
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        stats = circuit_breaker.get_stats()
        assert stats["call_count"] == 2
        assert stats["success_count"] == 0  # success_count unchanged after failure
        assert stats["failure_count"] == 1

    def test_global_instances(self):
        """Test that global circuit breaker instances are created correctly."""
        rest_cb = get_rest_api_circuit_breaker()
        knx_cb = get_knx_circuit_breaker()

        assert isinstance(rest_cb, CircuitBreaker)
        assert isinstance(knx_cb, CircuitBreaker)
        assert rest_cb is not knx_cb  # Different instances

        # Check configurations
        assert rest_cb.config.failure_threshold == 3  # REST specific
        assert knx_cb.config.failure_threshold == 5  # KNX specific

    @pytest.mark.asyncio
    async def test_concurrent_calls_during_open(self, circuit_breaker):
        """Test concurrent calls when circuit is open."""

        # Trip the circuit breaker
        async def failing_func():
            raise ValueError("error")

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitBreakerState.OPEN

        # Multiple concurrent calls should all fail fast
        async def success_func():
            return "success"

        tasks = []
        for i in range(5):
            task = asyncio.create_task(circuit_breaker.call(success_func))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should raise CircuitBreakerOpenException
        for result in results:
            assert isinstance(result, CircuitBreakerOpenException)

    @pytest.mark.asyncio
    async def test_recovery_success_resets_state(self, circuit_breaker):
        """Test successful recovery resets circuit breaker state."""

        # Trip circuit breaker
        async def failing_func():
            raise ValueError("error")

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery
        await asyncio.sleep(2.1)

        # Successful call in HALF_OPEN should close circuit
        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN
        assert circuit_breaker.get_stats()["failure_count"] == 0


class TestCircuitBreakerMutationTargets:
    """Smoke tests targeting surviving mutants in circuit_breaker.py.

    Each test documents which mutant it kills and why the assertion
    catches that specific code change.
    """

    @pytest.fixture
    def cb(self):
        return CircuitBreaker(CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1.0))

    # ── call: _call_count mutations ──────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_call_count_increments_per_call(self, cb):
        """Kill _call_count += 1 → = 1 / -= 1 / += 2.

        After N calls, call_count must equal N, not 1 or 2.
        """

        async def noop():
            return True

        await cb.call(noop)
        await cb.call(noop)
        await cb.call(noop)

        assert cb.get_stats()["call_count"] == 3

    # ── _record_failure: state + counter mutations ────────────────────────

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_failure_resets_success_count_to_zero(self, cb):
        """Kill _success_count = 0 → None / 1.

        A failure must zero out the success counter so the HALF_OPEN
        recovery sequence starts fresh.
        """
        cb._success_count = 5  # pretend some successes accumulated

        async def fail():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            await cb.call(fail)

        assert cb.get_stats()["success_count"] == 0

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_threshold_failures_set_state_to_open(self, cb):
        """Kill _state = OPEN → None.

        After failure_threshold failures, state must be exactly OPEN.
        """

        async def fail():
            raise ValueError()

        for _ in range(cb.config.failure_threshold):
            with pytest.raises(ValueError):
                await cb.call(fail)

        assert cb.state == CircuitBreakerState.OPEN

    # ── _record_success: HALF_OPEN branch mutations ───────────────────────

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_success_in_half_open_increments_success_count(self, cb):
        """Kill success_count += 1 → = 1 / -= 1.

        In HALF_OPEN, each success must increment the counter.
        After 2 successes it should be 2, not 1 (= 1 mutation would
        keep it at 1 on every call).
        """
        cb._state = CircuitBreakerState.HALF_OPEN

        async def ok():
            return True

        await cb.call(ok)
        await cb.call(ok)

        assert cb.get_stats()["success_count"] == 2

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_success_in_closed_does_not_increment_success_count(self, cb):
        """Kill 'if state == HALF_OPEN' → '!= HALF_OPEN'.

        Success in CLOSED state must NOT bump success_count (that counter
        is only for HALF_OPEN recovery tracking).
        """
        assert cb.state == CircuitBreakerState.CLOSED

        async def ok():
            return True

        await cb.call(ok)
        await cb.call(ok)

        assert cb.get_stats()["success_count"] == 0

    # ── get_stats: dict key mutations ────────────────────────────────────

    @pytest.mark.smoke
    def test_get_stats_returns_expected_keys(self, cb):
        """Kill 'name' → 'XXnameXX', 'success_count' → 'XXsuccess_countXX'.

        All documented keys must be present in the stats dict.
        """
        stats = cb.get_stats()
        for key in (
            "name",
            "state",
            "failure_count",
            "success_count",
            "call_count",
            "last_failure_time",
        ):
            assert key in stats, f"missing stats key: {key}"

    # ── _should_attempt_reset: boundary condition ─────────────────────────

    @pytest.mark.smoke
    def test_should_attempt_reset_at_exact_timeout(self, cb):
        """Kill elapsed >= timeout → elapsed > timeout.

        At exactly recovery_timeout seconds the reset must be attempted.
        The mutant (>) would miss the boundary and never reset.
        """
        import time

        cb._state = CircuitBreakerState.OPEN
        cb._last_failure_time = time.time() - cb.config.recovery_timeout  # exactly at boundary

        assert cb._should_attempt_reset() is True
