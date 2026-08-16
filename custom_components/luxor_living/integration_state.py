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

    @property
    def is_ready(self) -> bool:
        """Check if integration is fully initialized.

        Returns:
            True if gateway and coordinator are both initialized
        """
        return self.knx_gateway is not None and self.coordinator is not None

    @property
    def entity_count(self) -> int:
        """Total number of mapped entities."""
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
