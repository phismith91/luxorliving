"""Listener management for KNX telegrams."""

from __future__ import annotations

import logging
from typing import Any, Callable

from xknx.telegram.address import GroupAddress

_LOGGER = logging.getLogger(__name__)


class ListenerManager:
    """Manages callbacks for incoming KNX telegrams."""

    def __init__(self) -> None:
        """Initialize the listener manager."""
        self._listeners: dict[str, list[Callable]] = {}
        self._ga_label_map: dict[str, list[str]] = {}
        self._ia_label_map: dict[str, list[str]] = {}

    def register_listener(
        self,
        group_address: str | int,
        callback: Callable[[str, Any], None],
    ) -> None:
        """Register a callback for incoming telegrams to a specific group address.

        Args:
            group_address: KNX group address to listen to (int or "x/y/z")
            callback: Callback function that receives (group_address, value)
        """
        # Normalize key to consistent string form "x/y/z"
        try:
            normalized = str(GroupAddress(group_address))
        except Exception:
            normalized = str(group_address)

        if normalized not in self._listeners:
            self._listeners[normalized] = []

        self._listeners[normalized].append(callback)
        _LOGGER.debug(
            "Registered listener for KNX address %s",
            normalized,
        )

    def unregister_listener(
        self,
        group_address: str | int,
        callback: Callable[[str, Any], None],
    ) -> None:
        """Unregister a callback for a group address."""
        try:
            normalized = str(GroupAddress(group_address))
        except Exception:
            normalized = str(group_address)

        if normalized in self._listeners:
            try:
                self._listeners[normalized].remove(callback)
                _LOGGER.debug("Unregistered listener for %s", normalized)
            except ValueError:
                pass

    def set_group_address_labels(self, label_map: dict[str, list[str]]) -> None:
        """Provide a GA→labels map to enrich KNX logs with names.

        Args:
            label_map: Mapping of 'x/y/z' → ['Name (ID)', ...]
        """
        self._ga_label_map = label_map or {}
        _LOGGER.debug("Loaded %d GA labels for log enrichment", len(self._ga_label_map))

    def set_individual_address_labels(self, label_map: dict[str, list[str]]) -> None:
        """Provide an IA→labels map to enrich KNX logs with source device names."""
        self._ia_label_map = label_map or {}
        _LOGGER.debug("Loaded %d IA labels for log enrichment", len(self._ia_label_map))

    def get_listeners(self, group_address: str) -> list[Callable]:
        """Get listeners for a specific group address.

        Args:
            group_address: Normalized group address string

        Returns:
            List of callbacks for this address
        """
        return self._listeners.get(group_address, [])

    def get_group_address_labels(self, group_address: str) -> list[str]:
        """Get labels for a group address.

        Args:
            group_address: Group address string

        Returns:
            List of labels for this address
        """
        return self._ga_label_map.get(group_address, [])

    def get_individual_address_labels(self, individual_address: str) -> list[str]:
        """Get labels for an individual address.

        Args:
            individual_address: Individual address string

        Returns:
            List of labels for this address
        """
        return self._ia_label_map.get(individual_address, [])
