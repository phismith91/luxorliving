---
name: multi-agent-patterns
description:
  Multi-Agent Coordination Patterns für 7 spezialisierte GitHub Copilot Agents -
  Hierarchical Architecture, Context Isolation, Agent Handoffs
---

# Multi-Agent Patterns für LUXORliving

## When to Activate

- Wenn mehrere Agents parallel an verschiedenen Aspekten arbeiten
- Bei Agent-Koordinations-Problemen (z.B. Konflikte zwischen Code Style +
  Testing Agent)
- Wenn neue Agent-Rollen definiert werden
- Bei Refactoring der Agent-Hierarchie

## Core Concepts

**Decision Hierarchy**: Agents haben unterschiedliche Authority Levels:

- **L1 (Architecture)**: Strategic Decisions → Alle anderen Agents folgen
- **L2 (Domain Experts)**: KNX Protocol, Testing, Documentation → Technical
  Decisions
- **L3 (Operational)**: Deployment, Security, Code Style → Execution Decisions

**Context Isolation**: Jeder Agent hat eigenen Context Scope → verhindert
Context Clash

**Handoff Protocol**: Explizite Context-Übergabe zwischen Agents mit State
Documentation

## LUXORliving Agent Architecture

### Hierarchical Pattern (Current Implementation)

```
┌─────────────────────────────────────┐
│   L1: Architect Agent               │
│   Strategic Decisions               │
│   Authority: Architecture, Roadmap  │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┬────────────┬────────────┬───────────┐
       ▼               ▼            ▼            ▼           ▼
┌────────────┐  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│L2: KNX     │  │L2: Testing │ │L2: Docs  │ │L2: Deploy│ │L2: Code  │
│Protocol    │  │Agent       │ │Agent     │ │Agent     │ │Style     │
│Expert      │  │            │ │          │ │          │ │Agent     │
└────────────┘  └────────────┘ └──────────┘ └──────────┘ └──────────┘
       │
       ▼
┌────────────┐
│L2: Security│
│Agent       │
└────────────┘
```

### Agent Roles & Responsibilities

| Agent             | Level | Primary Responsibility                         | Context Sources                                      | Authority   |
| ----------------- | ----- | ---------------------------------------------- | ---------------------------------------------------- | ----------- |
| **Architect**     | L1    | Architecture Decisions, Roadmap                | CONTEXT.md, ARCHITECTURE_DECISION.md                 | FINAL       |
| **KNX Protocol**  | L2    | BAOS REST API, LXP Parsing, KNX Implementation | KNX_IMPLEMENTATION.md, lxp_parser.py, rest_client.py | Technical   |
| **Testing**       | L2    | Test Suite, Coverage, pytest                   | tests/, TESTS.md, pytest.ini                         | Quality     |
| **Documentation** | L2    | docs/, CHANGELOG.md, README.md                 | docs/\*\*                                            | Content     |
| **Deployment**    | L2    | SSH Deploy, Release Process                    | copilot-instructions.md, scripts/deploy_release.sh   | Operational |
| **Security**      | L2    | SSH Keys, Credentials, SECURITY.md             | SECURITY.md, SSH config                              | Security    |
| **Code Style**    | L3    | black, isort, mypy, PEP 8                      | requirements_style.txt, pyproject.toml               | Formatting  |

## Multi-Agent Coordination Patterns

### Pattern 1: Sequential Handoff (Orchestrator → Specialist)

**Use Case**: Feature Implementation (z.B. neue Climate Platform)

```markdown
## Agent 1: Architect (Orchestrator)

**Decision**:

- Implement H6 Climate Platform for heating actuators
- Use DPT9.001 for temperature values
- Follow existing platform pattern (Light, Switch)

**Context for Next Agent**:

- Platform: Climate (new)
- Reference Implementation: light.py, switch.py
- LXP Elements: 12 heating actuators identified
- DPTs: DPT9.001 (Temperature), DPT1.001 (On/Off)

**Handoff to**: KNX Protocol Expert

---

## Agent 2: KNX Protocol Expert

**Received Context**:

- Task: Implement Climate Platform
- Reference: light.py pattern
- Data: 12 heating actuators from LXP

**Implementation**:

- Create: custom_components/luxor_living/climate.py
- Parse: DPT9.001 temperature datapoints
- Map: Group addresses to climate entities

**Context for Next Agent**:

- File Created: climate.py (200 lines)
- Platform Registered: const.py updated
- Entity Mapping: 12 HeatingActuator entities

**Handoff to**: Testing Agent

---

## Agent 3: Testing Agent

**Received Context**:

- New Platform: Climate
- Implementation: climate.py
- Expected Coverage: >80%

**Testing**:

- Create: tests/test_climate.py
- Cover: Setup, state updates, service calls
- Validate: All 148 tests passing (incl. 15 new)

**Context for Next Agent**:

- Tests: 15 new tests created
- Coverage: 87% for climate.py
- All Tests: ✅ 148 passing

**Handoff to**: Documentation Agent
```

### Pattern 2: Parallel Specialists (Concurrent Work)

**Use Case**: Bug Fix + Documentation Update

```markdown
## Parallel Execution

┌──────────────────┐ ┌──────────────────┐ │ KNX Protocol │ │ Documentation │ │
Agent │ │ Agent │ ├──────────────────┤ ├──────────────────┤ │ Fix: DPT Mapping │
│ Update: KNX\_ │ │ in lxp_parser.py │ │ IMPLEMENTATION │ │ │ │ .md │ │ Context:
│ │ Context: │ │ - Only parser │ │ - Only docs/ │ │ - Isolated │ │ - Isolated │
└────────┬─────────┘ └─────────┬────────┘ │ │ └────────┬────────────────┘ │
┌────────▼─────────┐ │ Code Style │ │ Agent │ ├──────────────────┤ │ Check both:
│ │ - black format │ │ - mypy types │ └──────────────────┘
```

**Conflict Resolution**: Architect Agent hat FINAL Authority

### Pattern 3: Peer-to-Peer Validation

**Use Case**: Pre-Release Testing

```markdown
┌──────────────┐ │ Deployment │ ─┐ │ Agent │ │ └──────────────┘ │ ├──► Validate
against each other ┌──────────────┐ │ │ Testing │ ─┘ │ Agent │ └──────────────┘

Deployment: "Release v0.3.4 ready" Testing: "All 148 tests pass ✅" →
Cross-Validation: Both agree → Proceed
```

## Practical Guidance

### Agent Handoff Template

```markdown
## [AGENT HANDOFF]

**From**: [Source Agent Name] **To**: [Target Agent Name] **Date**: [ISO 8601
Timestamp]

**Context Passed**:

- Key Decision: [What was decided]
- Files Modified: [Explicit file list]
- State: [Current system state]
- Dependencies: [What target agent needs to know]

**Expected Outcome**:

- Deliverable: [What target agent should produce]
- Validation: [How to verify success]
- Handoff Next: [Next agent in chain]
```

### Context Isolation Pattern

```python
# GOOD: Agent-specific context loading
class AgentContext:
    def __init__(self, agent_name: str):
        self.agent = agent_name
        self.scope = self._load_scope()

    def _load_scope(self) -> dict:
        scopes = {
            "KNX Protocol": [
                "custom_components/luxor_living/*.py",
                "docs/KNX_IMPLEMENTATION.md"
            ],
            "Testing": [
                "tests/**/*.py",
                "pytest.ini",
                "docs/TESTS.md"
            ],
            "Documentation": [
                "docs/**/*.md",
                "CHANGELOG.md",
                "README.md"
            ]
        }
        return scopes.get(self.agent, [])

# BAD: All agents load everything
all_files = glob.glob("**/*")  # Context clash!
```

### Decision Conflict Resolution

````markdown
## Conflict Resolution Protocol

1. **Identify Authority Level**
   - L1 (Architect) > L2 (Domain) > L3 (Operational)

2. **Document Disagreement**

   ```markdown
   ## [CONFLICT]

   Agent 1 (Testing): Suggests mock BAOS API in tests Agent 2 (KNX Protocol):
   Prefers integration tests

   Authority: Testing Agent (L2, equal level) Escalate to: Architect Agent (L1)
   ```
````

3. **Architect Decision**

   ```markdown
   ## [RESOLUTION]

   Decision: Use both approaches

   - Unit tests: Mock BAOS API (fast)
   - Integration tests: Real BAOS (in CI only)

   Authority: Architect Agent (L1) Binding: YES
   ```

````

## Examples

**Example 1: Feature Development Flow**

```markdown
1. Architect Agent: Decides "Add Binary Sensor Platform"
   ↓
2. KNX Protocol Agent: Implements binary_sensor.py
   ↓
3. Testing Agent: Creates test_binary_sensor.py
   ↓
4. Code Style Agent: Validates black + mypy
   ↓
5. Documentation Agent: Updates README.md + CHANGELOG.md
   ↓
6. Deployment Agent: Prepares release v0.3.4
````

**Example 2: Bug Fix with Parallel Work**

```markdown
Bug: "Cover platform wrong DPT mapping"

┌─────────────────┐ │ KNX Protocol │ → Fix: cover.py DPT1.008 → DPT1.009
└─────────────────┘ ║ ║ (Parallel) ║ ┌─────────────────┐ │ Documentation │ →
Update: KNX_IMPLEMENTATION.md └─────────────────┘

Both complete → Merge ↓ Code Style Agent: Validate formatting ↓ Testing Agent:
Run all tests
```

## Guidelines

1. **Clear Handoffs**: Dokumentiere Context-Übergaben explizit
2. **Authority Respect**: L1 > L2 > L3 Hierarchy beachten
3. **Context Isolation**: Jeder Agent nur eigenen Scope laden
4. **Conflict Protocol**: Bei Disagreement zu höherem Level eskalieren
5. **State Documentation**: CONTEXT.md als Shared State nutzen
6. **Parallel Safety**: Nur disjunkte File Sets parallel bearbeiten
7. **Validation Gates**: Testing Agent prüft alle Changes

## Integration

- **context-fundamentals**: Context Budgets pro Agent
- **context-degradation**: Verhindert Lost-in-Middle bei langen Handoff-Chains
- **evaluation**: Misst Agent Coordination Quality

## References

- [.github/copilot/CONTEXT.md](../CONTEXT.md) - Agent Coordination Rules
- [AGENTS.md](../../AGENTS.md) - Agent Setup
- [Agent Skills Repository](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)

---

**Created**: 2026-01-01 **Last Updated**: 2026-01-01 **Author**: LUXORliving
Multi-Agent Team **Version**: 1.0.0
