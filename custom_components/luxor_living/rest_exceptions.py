"""REST API Client Exceptions."""

from __future__ import annotations


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class TunnelingError(Exception):
    """Raised when tunneling activation fails."""

