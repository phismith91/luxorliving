---
description:
  System architecture overview for LUXORliving Home Assistant integration
---

# LUXORliving Architecture Overview

## System Design

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Home Assistant Instance                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           LUXORliving Custom Integration                │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  Configuration Flow                             │   │  │
│  │  │  - File upload (LXP project)                    │   │  │
│  │  │  - Gateway IP/credentials                       │   │  │
│  │  │  - Connection mode (Tunneling/Routing)         │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │                        ↓                                │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  Entity Mapper (PlatformDetector + DI)          │   │  │
│  │  │  - LXP parsing & device extraction              │   │  │
│  │  │  - Role→Platform mapping                        │   │  │
│  │  │  - Override handling                            │   │  │
│  │  │  Output: MappedEntity[]                         │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │                        ↓                                │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  Coordinator (DataUpdateCoordinator)            │   │  │
│  │  │  - Periodic polling (configurable interval)     │   │  │
│  │  │  - State synchronization                        │   │  │
│  │  │  - Authentication failure tracking (3 → repair) │   │  │
│  │  │  - Circuit breaker protection                   │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │                        ↓                                │  │
│  │  ┌──────────┬──────────┬──────────┬────────────────┐  │  │
│  │  │ Light    │ Switch   │ Cover    │ Climate/Sensor │  │  │
│  │  │ Platform │ Platform │ Platform │ Platforms      │  │  │
│  │  └──────────┴──────────┴──────────┴────────────────┘  │  │
│  │                        ↓                                │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  KNX Gateway (REST API Client)                  │   │  │
│  │  │  - REST API communication                       │   │  │
│  │  │  - Tunneling/Routing mode support               │   │  │
│  │  │  - Circuit breaker on failures                  │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │                        ↓                                │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  Health Endpoint & Diagnostics                  │   │  │
│  │  │  - /api/luxor_living/health                     │   │  │
│  │  │  - /api/luxor_living/benchmark                  │   │  │
│  │  │  - /api/luxor_living/push (push webhook)        │   │  │

Push/WebSocket Client: The integration can optionally start a WebSocket client that connects to an external push forwarder and forwards pushed KNX values into the local KNX gateway. This reduces polling and improves latency for state updates.
│  │  └─────────────────────────────────────────────────┘   │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │  BAOS 777 Gateway   │
                    │  (Theben REST API)  │
                    └─────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │   KNX Bus Network   │
                    │  (Physical Devices) │
                    └─────────────────────┘
```

## Component Responsibilities

### Configuration & Setup

- **config_flow.py** - User interface for integration setup
  - Step 1: File upload or path entry
  - Step 2: Gateway configuration (IP, port, credentials)
  - Step 3: Connection mode selection
  - Output: ConfigEntry stored in HA

### Entity Creation

- **entity_mapper.py** - Converts LXP to HA entities
  - Parses LXP project file structure
  - Detects KNX datapoint roles
  - Creates MappedEntity objects
  - Applies user overrides

- **platform_detector.py** - Role→Platform mapping (extracted)
  - Maps KNX roles to HA platforms
  - Determines units & device classes
  - Supports 15+ KNX roles

- **override_handler.py** - User customizations (extracted)
  - Parses override YAML
  - Applies custom sensor names/units
  - Handles address normalization

### Runtime Operations

- **coordinator.py** (DataUpdateCoordinator)
  - Periodic polling of gateway state
  - Distributes state updates to entities
  - Tracks authentication failures
  - Triggers repair flow after 3 failures
  - State cache management

- **rest_client.py** - BAOS REST API client
  - HTTPS/HTTP communication
  - Authentication (token-based)
  - GroupValueRead/Write operations
  - Error handling & timeouts

- **knx_gateway.py** - KNX protocol abstraction
  - Tunneling mode setup
  - Routing mode setup
  - Telegram monitoring
  - Connection management

### Resilience & Health

- **circuit_breaker.py** - Failure resilience pattern
  - Closed → Open → Half-Open state machine
  - Prevents cascading failures
  - Auto-recovery after timeout
  - Statistics tracking

- **health.py** - System health endpoint
  - Integration status
  - Connection state
  - Error summary
  - Performance metrics

### Platform Implementations

- **light.py** - Light entities (dimmable & non-dimmable)
- **switch.py** - Switch entities
- **cover.py** - Cover/blind entities (position & tilt)
- **climate.py** - Climate/thermostat entities
- **sensor.py** - Sensor entities (temperature, humidity, etc.)
- **binary_sensor.py** - Binary sensor entities (motion, doors, etc.)

## Data Flow

### Initialization Flow

```
1. User adds integration
   ↓
2. config_flow shows form
   ↓
3. User uploads LXP file + gateway config
   ↓
4. LXPParser extracts project structure
   ↓
5. EntityMapper creates MappedEntity[] from LXP
   ↓
6. Platform files (light.py, etc.) create HA entities
   ↓
7. Coordinator starts polling for state updates
   ↓
8. HA entity states synchronized with KNX devices
```

### Update Flow (Periodic)

```
Coordinator (every X seconds)
   ↓
KNX Gateway.read_group_value()
   ↓
REST API call to BAOS: GET /1/groups/1/value
   ↓
Parse response
   ↓
Coordinator.async_set_updated_data()
   ↓
Distribute to listening entities
   ↓
Entity state updated in HA
```

### User Action Flow

```
User presses light button in HA UI
   ↓
Light entity.async_turn_on()
   ↓
KNX Gateway.send_telegram()
   ↓
REST API call to BAOS: PUT /1/groups/1/value
   ↓
BAOS forwards to KNX bus
   ↓
Physical light turns on
   ↓
Next polling cycle reads updated state
   ↓
HA entity state synchronized
```

## Key Design Decisions

### 1. REST API Over Direct Tunneling

**Decision:** Use BAOS REST API instead of direct KNX/IP tunneling

**Rationale:**

- No KNX/IP tunnel license required
- Simpler protocol (HTTP instead of binary)
- Better error handling
- Works with standard firewalls
- Easier debugging (HTTP logs)

**Trade-off:**

- Slightly higher latency (REST overhead)
- Dependency on BAOS firmware version

### 2. Coordinator Pattern

**Decision:** Use Home Assistant's DataUpdateCoordinator

**Rationale:**

- Built-in HA pattern (best practice)
- Automatic error handling
- Coordinator shares data across entities
- Retry logic included
- Memory efficient

**Alternative considered:** Direct REST calls per entity (rejected -
inefficient)

### 3. LXP over ETS

**Decision:** Parse LXP project files instead of using ETS software

**Rationale:**

- User-friendly (no ETS license needed)
- Portable (LXP is XML-based)
- Programmatic parsing possible
- Works with Theben LUXORPlug software

**Trade-off:**

- ETS-specific features not available
- Manual address configuration not supported

### 4. Circuit Breaker Protection

**Decision:** Implement circuit breaker pattern for error resilience

**Rationale:**

- Prevents cascading failures
- Automatic recovery
- Graceful degradation
- Monitoring-friendly

**States:**

- **Closed:** Normal operation
- **Open:** Too many errors, reject calls
- **Half-Open:** Testing recovery

### 5. Dependency Injection for EntityMapper

**Decision:** Inject PlatformDetector + OverrideHandler into EntityMapper

**Rationale:**

- Single Responsibility Principle
- Easier testing (can mock dependencies)
- Reduced coupling
- Cleaner code structure

## State Management

### Coordinator State Cache

```python
coordinator.data = {
    "1/2/3": {  # Group address
        "value": 255,              # Current brightness
        "last_update": 1704000000, # Timestamp
        "type": "5.001"            # DPT type
    },
    ...
}
```

**Lifetime:**

- Created on first read
- Updated on every poll
- Cleared on coordinator reload
- Persisted during HA session

### Entity-Level State

```python
@property
def brightness(self):
    """Current brightness from coordinator state."""
    return self.coordinator.data["1/2/3"]["value"]
```

## Performance Characteristics

### Initialization

- LXP parsing: ~100ms for typical project (100+ devices)
- Entity creation: ~50ms per 100 entities
- Total startup: ~200-300ms for full project

### Runtime

- Polling interval: Configurable (default: 30s)
- Per-entity update: <5ms (state sync only)
- State reads per cycle: 1 API call to BAOS
- Memory footprint: ~2-5MB per 100 entities

### Bottlenecks

- REST API latency (100-500ms per call)
- Network connectivity (timeouts)
- BAOS firmware performance (response time)

## Extension Points

### Adding New Platforms

1. Create `new_platform.py` (light.py as template)
2. Implement async_setup_entry()
3. Create entity class (inherit from HA entity)
4. Register in `__init__.py`

### Custom Role Mappings

```python
# PlatformDetector.ROLE_TO_PLATFORM
"CustomRole": Platform.LIGHT
```

### Override System

```yaml
# luxor_living_overrides.yaml
sensors:
  - role: "Temperature"
    address: "1/2/3"
    name: "Living Room Temp"
    unit: "°F"
```

## Testing Strategy

### Unit Tests

- Entity mapper role detection
- Platform detection logic
- Override parsing
- Circuit breaker state transitions

### Integration Tests

- Full LXP → entities flow
- Coordinator polling
- Entity state synchronization
- Config flow validation

### E2E Tests

- Real gateway communication
- Remote HA instance testing
- Full user workflow

## Security Considerations

1. **Credentials:** Stored in HA secrets, not in code
2. **HTTPS:** Enforced for REST API communication
3. **Input Validation:** All user inputs validated
4. **Error Messages:** No sensitive data leaked
5. **Audit Trail:** Repair flows tracked in HA logs
