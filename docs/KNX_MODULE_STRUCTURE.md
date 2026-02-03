# KNX Gateway Module Structure

This document describes the modular structure of the KNX Gateway implementation.

## Overview

The KNX Gateway has been refactored from a monolithic 854-line file into a modular architecture with clear separation of concerns.

## Module Organization

```
custom_components/luxor_living/
├── knx_gateway.py              # Main orchestrator (467 lines)
└── knx/
    ├── __init__.py             # Module exports
    ├── discovery_engine.py     # Auto-discovery logic (198 lines)
    ├── listener_manager.py     # Event management (111 lines)
    └── telegram_processor.py   # Message processing (288 lines)
```

## Component Responsibilities

### knx_gateway.py (Main Orchestrator)
The main `LuxorKNXGateway` class provides:
- **Connection Management**: REST API authentication and KNX tunneling setup
- **Telegram I/O**: Sending and reading KNX telegrams
- **Public API**: Delegates to sub-components while maintaining the same public interface
- **Lifecycle**: Setup and teardown orchestration

**Key Methods:**
- `async_setup()` - Initialize REST and KNX connections
- `async_disconnect()` - Clean shutdown
- `async_send_telegram()` - Send KNX messages
- `async_read_group_address()` - Request group address values
- `register_listener()` - Register for telegram notifications

### knx/discovery_engine.py (Auto-Discovery)
Handles automatic discovery of KNX sensors:
- **Value Tracking**: Monitors DPT 9.xxx float values
- **Sensor Detection**: Determines sensor types based on value ranges
- **Stability Checking**: Ensures consistent readings before creating sensors
- **Debouncing**: Batches discoveries to prevent reload loops

**Key Features:**
- Temperature, humidity, illuminance, pressure detection
- Configurable stability thresholds
- Memory leak prevention with sample limits

### knx/listener_manager.py (Event Management)
Manages callbacks for incoming KNX telegrams:
- **Listener Registry**: Tracks callbacks per group address
- **Label Management**: Maps addresses to human-readable names
- **Notification**: Provides listeners for telegram events

**Key Methods:**
- `register_listener()` - Subscribe to group address updates
- `unregister_listener()` - Remove subscriptions
- `get_listeners()` - Retrieve callbacks for an address

### knx/telegram_processor.py (Message Processing)
Processes incoming and external messages:
- **Telegram Parsing**: Decodes KNX telegram payloads
- **DPT Conversion**: Handles binary, percent, and 2-byte float types
- **External Push**: Integrates webhook/WebSocket push events
- **Listener Notification**: Dispatches to registered callbacks
- **Discovery Integration**: Triggers auto-discovery for float values

**Supported DPT Types:**
- DPTBinary (on/off)
- DPT 5.001 (percent, 0-100%)
- DPT 9.xxx (2-byte float for sensors)

## Backward Compatibility

All public APIs remain unchanged. Constants used in tests are re-exported from `knx_gateway.py`:
- `DISCOVERY_DEBOUNCE_DELAY`
- `DISCOVERY_MAX_CANDIDATES_PER_ADDRESS`
- `DISCOVERY_MIN_SAMPLES`
- `DISCOVERY_VALUE_TOLERANCE`

## Benefits

1. **Maintainability**: Each file is now under 500 lines
2. **Testability**: Components can be tested independently
3. **Clarity**: Clear separation of concerns
4. **Extensibility**: Easy to add new features to specific modules
5. **No Breaking Changes**: Public API surface unchanged

## Usage Example

```python
from custom_components.luxor_living.knx_gateway import LuxorKNXGateway

# Create gateway (same as before)
gateway = LuxorKNXGateway(
    hass=hass,
    host="192.168.1.100",
    port=3671,
    username="admin",
    password="password",
)

# All methods work the same
await gateway.async_setup()
gateway.register_listener("1/2/3", callback)
await gateway.async_send_telegram("1/2/3", True, "binary")
```

## Migration Notes

- **No code changes required** in existing code using `LuxorKNXGateway`
- Internal implementation now uses composition instead of a single large class
- All existing tests should continue to work without modification
