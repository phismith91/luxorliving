---
name: context-fundamentals
description: Context Engineering Fundamentals für GitHub Copilot - Management von Context Windows, Progressive Disclosure und Attention Budgets für Multi-Agent Systeme
---

# Context Engineering Fundamentals für LUXORliving

## When to Activate

- Wenn Agent-Koordination zwischen den 7 Copilot Agents optimiert werden soll
- Bei Context-bezogenen Performance-Problemen (z.B. Agent "vergisst" vorherige Änderungen)
- Wenn neue Agent-Instruktionen entworfen werden
- Bei LXP Parser Optimierung (3-Level Loading Pattern)

## Core Concepts

**Context als finite Resource**: Jeder Token reduziert das Attention Budget. LLMs haben wie Menschen ein limitiertes Working Memory.

**Progressive Disclosure**: Information nur laden wenn benötigt:
- **L1 (Discovery)**: Skill Name + Description (~50 tokens)
- **L2 (Activation)**: Vollständige Instructions (~200-500 tokens)  
- **L3 (Execution)**: Referenced Files, Data (~1000+ tokens)

**Attention Budget**: Context Position matters:
- **Start**: Höchste Attention → System Prompts, Critical Tasks
- **Middle**: Niedrigste Attention (Lost-in-Middle) → Bulk Data
- **End**: Hohe Attention → Key Findings, Current Task

## LUXORliving Spezifische Anwendung

### Agent Context Budgets

| Agent             | Role                       | Context Budget | Priority                                |
| ----------------- | -------------------------- | -------------- | --------------------------------------- |
| **Architect**     | Architektur-Entscheidungen | 50k tokens     | CONTEXT.md, Architecture Docs           |
| **KNX Protocol**  | BAOS/KNX Technical         | 80k tokens     | KNX_IMPLEMENTATION.md, LXP Parser       |
| **Testing**       | Test-Suite Management      | 30k tokens     | test_*.py, TESTS.md                     |
| **Documentation** | Docs + Changelog           | 40k tokens     | docs/, CHANGELOG.md                     |
| **Deployment**    | Release + SSH Deploy       | 35k tokens     | deploy scripts, copilot-instructions.md |
| **Security**      | Credentials + SSH Keys     | 25k tokens     | SECURITY.md, SSH procedures             |
| **Code Style**    | Python Best Practices      | 20k tokens     | requirements_*.txt, PEP 8               |

**Total Budget**: ~280k tokens across all agents

### Progressive Disclosure für LXP Parser

```python
# L1: Summary (auf Anfrage laden)
lxp_summary = {
    "version": "0.9",
    "elements": 243,
    "categories": ["Light", "Switch", "Climate", "Cover"]
}

# L2: Category Details (nur wenn relevant)
def load_category_elements(category: str):
    """Lädt nur Elemente einer Kategorie"""
    return parser.get_elements_by_category(category)

# L3: Full Element Data (on-demand)
def load_full_element(element_id: str):
    """Lädt komplette DPT, Flags, Metadata"""
    return parser.get_element_details(element_id)
```

### Context Organization Pattern

```markdown
<!-- Für jede Agent Instruction -->
<AGENT_IDENTITY>
Name: KNX Protocol Expert
Role: BAOS REST API + LXP File Parsing
</AGENT_IDENTITY>

<CRITICAL_CONTEXT>
<!-- Position: START (höchste Attention) -->
- Current Task: Parse Hauptwohnung.lxp
- Active Platform: Light (D1/D3 Dimmers)
- Context Budget: 80k tokens (70% used)
</CRITICAL_CONTEXT>

<DETAILED_INFORMATION>
<!-- Position: MIDDLE (bulk data, weniger kritisch) -->
- 243 KNX Elements parsed
- 7 Element Categories supported
- DPT Mapping: DPT1.001 (Switch), DPT5.001 (Dim%)
</DETAILED_INFORMATION>

<CURRENT_TASK>
<!-- Position: END (hohe Attention) -->
Goal: Implement H6 Climate Platform for Heating Actuators
Next Step: Parse DPT9.001 Temperature Values
</CURRENT_TASK>
```

## Practical Guidance

### File-Based Context Management

```python
# GOOD: Load only needed files
if task == "light_platform":
    context = [
        "custom_components/luxor_living/light.py",  # Primary file
        "docs/KNX_IMPLEMENTATION.md#L1-L50"        # Relevant section
    ]

# BAD: Load everything
context = glob.glob("**/*.py")  # 280k+ tokens!
```

### Agent Coordination mit CONTEXT.md

```markdown
<!-- .github/copilot/CONTEXT.md -->
## Active Agents

**Primary Agent**: KNX Protocol Expert
**Supporting Agents**: Testing, Code Style
**Context Sharing**: 
- Primary loads: lxp_parser.py (full)
- Testing loads: test_lxp_parser.py (full)
- Code Style loads: both (linting only)
```

### Context Compaction Trigger

```python
# Implementiere Trigger bei 70-80% Budget
def check_context_budget():
    if current_tokens / max_tokens > 0.75:
        # Compaction: Summarize conversation history
        history_summary = summarize_last_10_turns()
        # Keep only last 3 turns in full detail
        context = [history_summary] + recent_turns[-3:]
```

## Examples

**Example 1: Agent Switching mit Context Preservation**

```markdown
# Von Architecture Agent zu KNX Protocol Agent

[HANDOFF]
Previous Agent: Architecture
Decision: Use H6 Climate Platform for heating
Context Passed:
- DPT9.001 Temperature datapoints identified
- 12 heating actuators in Hauptwohnung.lxp
- Reference: docs/KNX_IMPLEMENTATION.md#L120-L145

Current Agent: KNX Protocol
Task: Implement Climate Platform
Context Loaded:
- climate.py (L1-L200)
- lxp_parser.py (only get_climate_elements method)
- test_climate.py (framework, not tests yet)
```

**Example 2: LXP Progressive Disclosure**

```python
# Step 1: Load Summary (100 tokens)
lxp_meta = parse_lxp_metadata("Hauptwohnung.lxp")
# Returns: version, element_count, categories

# Step 2: Load Category (wenn Light platform relevant)
lights = get_elements_by_category("Light")
# Returns: nur Element IDs + Names

# Step 3: Load Full Element (für konkreten Dimmer)
element_43 = get_full_element_details("43")
# Returns: DPT, Group Address, Flags, etc.
```

## Guidelines für LUXORliving Agents

1. **Context Budget Monitoring**: Track Token Usage in CONTEXT.md
2. **Critical Info at Edges**: Tasks + Decisions → START oder END
3. **Progressive Disclosure**: LXP, Test Files, Docs → Load on Demand
4. **Agent Isolation**: Jeder Agent hat eigenen Context Scope
5. **Compaction Trigger**: Bei >75% Budget → Summarize History
6. **Position Awareness**: System Prompts (START), Data (MIDDLE), Task (END)
7. **High-Signal Tokens**: Nur relevante Docs, nicht komplettes Repo
8. **Handoff Protocol**: Context Pass bei Agent-Wechsel dokumentieren

## Integration mit Anderen Skills

- **context-degradation**: Erkennung von "Lost-in-Middle" bei LXP Parsing
- **multi-agent-patterns**: Koordination der 7 Copilot Agents
- **evaluation**: Testing Framework für Context Quality

## References

- [Agent Skills Repository](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)
- [.github/copilot/CONTEXT.md](../.github/copilot/CONTEXT.md) - Single Source of Truth
- [AGENTS.md](../../AGENTS.md) - Setup + Testing Instructions

---

**Created**: 2026-01-01  
**Last Updated**: 2026-01-01  
**Author**: LUXORliving Context Engineering  
**Version**: 1.0.0
