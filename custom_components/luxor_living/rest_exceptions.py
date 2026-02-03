"""REST API Client Exceptions."""

from __future__ import annotations


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class TunnelingError(Exception):
    """Raised when tunneling activation fails."""

    pass
