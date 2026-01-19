"""Type-safe state management for LUXORliving integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import LuxorLivingCoordinator
    from .entity_mapper import EntityMapper
    from .knx_gateway import LuxorKNXGateway as KNXGateway


@dataclass
class IntegrationState:
    """Type-safe container for integration state.

    Replaces untyped dict storage in hass.data[DOMAIN][entry_id].
    Provides IDE autocomplete, type checking, and better maintainability.

    Attributes:
        mapper: Entity mapper with parsed LXP data and platform detection
        config: Configuration data from config entry
        overrides: User-defined overrides from YAML configuration
        knx_gateway: KNX gateway instance for device communication
        coordinator: Data update coordinator for periodic polling
        entry: Config entry reference (for diagnostics and debugging)
    """

    mapper: EntityMapper
    config: dict[str, Any]
    overrides: dict[str, Any]
    knx_gateway: KNXGateway | None = None
    coordinator: LuxorLivingCoordinator | None = None
    entry: ConfigEntry | None = field(default=None, repr=False)
    # Optional push client for receiving websocket events
    push_client: Any | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if self.mapper is None:
            raise ValueError("IntegrationState requires mapper instance")
        if self.config is None:
            raise ValueError("IntegrationState requires config dict")

    @property
    def is_ready(self) -> bool:
        """Check if integration is fully initialized.

        Returns:
            True if gateway and coordinator are both initialized
        """
        return self.knx_gateway is not None and self.coordinator is not None

    def get_entity_count(self) -> int:
        """Get total number of mapped entities.

        Returns:
            Number of entities from mapper
        """
        return len(self.mapper.entities)

    def get_gateway_or_raise(self) -> KNXGateway:
        """Get KNX gateway or raise if not initialized.

        Returns:
            KNX gateway instance

        Raises:
            RuntimeError: If gateway not yet initialized
        """
        if self.knx_gateway is None:
            raise RuntimeError("KNX Gateway not initialized - setup incomplete")
        return self.knx_gateway

    def get_coordinator_or_raise(self) -> LuxorLivingCoordinator:
        """Get coordinator or raise if not initialized.

        Returns:
            Coordinator instance

        Raises:
            RuntimeError: If coordinator not yet initialized
        """
        if self.coordinator is None:
            raise RuntimeError("Coordinator not initialized - setup incomplete")
        return self.coordinator


# Global registry for integration states (indexed by entry_id)
# Replaces hass.data[DOMAIN][entry_id] dict access
_integration_states: dict[str, IntegrationState] = {}


def get_integration_state(entry_id: str) -> IntegrationState:
    """Get integration state for config entry.

    Args:
        entry_id: Config entry ID

    Returns:
        Integration state instance

    Raises:
        KeyError: If entry_id not found (integration not set up)
    """
    if entry_id not in _integration_states:
        raise KeyError(
            f"Integration state not found for entry_id={entry_id}. "
            "Ensure async_setup_entry completed successfully."
        )
    return _integration_states[entry_id]


def register_integration_state(entry_id: str, state: IntegrationState) -> None:
    """Register integration state for config entry.

    Args:
        entry_id: Config entry ID
        state: Integration state instance to register
    """
    _integration_states[entry_id] = state


def unregister_integration_state(entry_id: str) -> IntegrationState | None:
    """Unregister integration state for config entry.

    Args:
        entry_id: Config entry ID to unregister

    Returns:
        Removed integration state, or None if not found
    """
    return _integration_states.pop(entry_id, None)


def has_integration_state(entry_id: str) -> bool:
    """Check if integration state exists for config entry.

    Args:
        entry_id: Config entry ID to check

    Returns:
        True if state registered, False otherwise
    """
    return entry_id in _integration_states
