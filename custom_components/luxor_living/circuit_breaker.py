"""Circuit Breaker Pattern for resilient error handling."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

_LOGGER = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 60.0  # Seconds to wait before trying again
    success_threshold: int = 3  # Successes needed to close circuit
    timeout: float = 10.0  # Operation timeout in seconds


class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation for resilient error handling."""

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        """Initialize circuit breaker.

        Args:
            name: Identifier for this circuit breaker
            config: Configuration for thresholds and timeouts
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._call_count = 0

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self._state != CircuitBreakerState.OPEN:
            return False

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.recovery_timeout

    def _record_success(self):
        """Record a successful operation."""
        self._failure_count = 0

        if self._state == CircuitBreakerState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._state = CircuitBreakerState.CLOSED
                self._success_count = 0
                _LOGGER.info("Circuit breaker '%s' closed after %d successes",
                           self.name, self.config.success_threshold)

    def _record_failure(self):
        """Record a failed operation."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._success_count = 0

        if self._state == CircuitBreakerState.HALF_OPEN:
            self._state = CircuitBreakerState.OPEN
            _LOGGER.warning("Circuit breaker '%s' opened again after failure", self.name)
        elif (self._state == CircuitBreakerState.CLOSED and
              self._failure_count >= self.config.failure_threshold):
            self._state = CircuitBreakerState.OPEN
            _LOGGER.warning("Circuit breaker '%s' opened after %d failures",
                          self.name, self._failure_count)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit is open
            Exception: Original function exceptions
        """
        self._call_count += 1

        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._state = CircuitBreakerState.HALF_OPEN
            _LOGGER.info("Circuit breaker '%s' attempting reset", self.name)

        # Reject call if circuit is open
        if self._state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenException(
                f"Circuit breaker '{self.name}' is OPEN (failures: {self._failure_count})"
            )

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )

            self._record_success()
            return result

        except Exception as e:
            self._record_failure()

            # Re-raise original exception
            raise e

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "call_count": self._call_count,
            "last_failure_time": self._last_failure_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            }
        }


# Global circuit breakers for different operations
_rest_api_circuit_breaker = CircuitBreaker(
    "rest_api",
    CircuitBreakerConfig(
        failure_threshold=3,  # Open after 3 REST API failures
        recovery_timeout=30.0,  # Try again after 30 seconds
        success_threshold=2,   # Need 2 successes to close
        timeout=15.0          # 15 second timeout for REST calls
    )
)

_knx_circuit_breaker = CircuitBreaker(
    "knx_connection",
    CircuitBreakerConfig(
        failure_threshold=5,   # Open after 5 KNX connection failures
        recovery_timeout=60.0,  # Try again after 1 minute
        success_threshold=3,    # Need 3 successes to close
        timeout=30.0           # 30 second timeout for KNX operations
    )
)


def get_rest_api_circuit_breaker() -> CircuitBreaker:
    """Get the REST API circuit breaker instance."""
    return _rest_api_circuit_breaker


def get_knx_circuit_breaker() -> CircuitBreaker:
    """Get the KNX circuit breaker instance."""
    return _knx_circuit_breaker