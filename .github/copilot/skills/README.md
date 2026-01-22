# GitHub Copilot Skills für LUXORliving

Angepasste Context Engineering Skills basierend auf
[Agent Skills for Context Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering).

## Verfügbare Skills

### Foundational Skills

| Skill                                           | Beschreibung                                                  | Wann aktivieren                            |
| ----------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------ |
| [context-fundamentals](context-fundamentals.md) | Context Management, Progressive Disclosure, Attention Budgets | Agent-Koordination, LXP Parser Optimierung |
| [multi-agent-patterns](multi-agent-patterns.md) | Coordination der 7 Copilot Agents, Hierarchies, Handoffs      | Feature Development, Agent Conflicts       |
| [evaluation](evaluation.md)                     | Quality Gates, Testing Metrics, Agent Performance             | Pre-Release, CI/CD, Performance Monitoring |
| [coding-standards](coding-standards.md)         | Black/isort, Typing, HA async Do/Don'ts                       | Code Reviews, Implementierung              |
| [tdd-workflow](tdd-workflow.md)                 | Pytest-first Flow, Coverage ≥80%, deterministic tests         | Neue Features, Bugfixes                    |

## Nutzung in VS Code

Diese Skills sind automatisch für GitHub Copilot verfügbar durch die
`.github/copilot/` Struktur.

### Skill Aktivierung

GitHub Copilot lädt Skills automatisch wenn Keywords erwähnt werden:

```markdown
"optimize context for agents" → context-fundamentals.md "agent handoff to
testing" → multi-agent-patterns.md "pre-release quality check" → evaluation.md
```

### Progressive Disclosure Pattern

**Level 1 - Discovery**: Copilot kennt Skill Namen + Beschreibungen (~150
tokens)

**Level 2 - Activation**: Vollständige Skill Instructions geladen (~500 tokens)

**Level 3 - Execution**: Referenced Files + Data geladen (~1000+ tokens)

## LUXORliving Spezifische Anwendungen

### Context Budgets (aus context-fundamentals.md)

| Agent         | Budget | Primäre Context Sources                 |
| ------------- | ------ | --------------------------------------- |
| Architect     | 50k    | CONTEXT.md, ARCHITECTURE_DECISION.md    |
| KNX Protocol  | 80k    | KNX_IMPLEMENTATION.md, lxp_parser.py    |
| Testing       | 30k    | tests/, TESTS.md                        |
| Documentation | 40k    | docs/                                   |
| Deployment    | 35k    | copilot-instructions.md, deploy scripts |
| Security      | 25k    | SECURITY.md                             |
| Code Style    | 20k    | requirements_style.txt                  |

### Agent Hierarchie (aus multi-agent-patterns.md)

```
L1: Architect (Strategic Decisions) → FINAL Authority
 ├─ L2: KNX Protocol (Technical)
 ├─ L2: Testing (Quality)
 ├─ L2: Documentation (Content)
 ├─ L2: Deployment (Operations)
 ├─ L2: Security (Security)
 └─ L3: Code Style (Formatting)
```

### Quality Gates (aus evaluation.md)

```bash
# Pre-Release Checks
python -m pytest tests/ -v           # All tests pass
python -m pytest --cov=... --fail-under=80  # Coverage >80%
mypy custom_components/luxor_living/        # Type safety
black --check .                             # Formatting
```

## Erweiterung

### Neue Skill hinzufügen

1. Erstelle `skills/<skill-name>.md`
2. Füge YAML frontmatter hinzu:
   ```yaml
   ---
   name: skill-name
   description: Kurzbeschreibung wann/wie aktivieren
   ---
   ```
3. Strukturiere nach Template:
   - When to Activate
   - Core Concepts
   - LUXORliving Spezifische Anwendung
   - Practical Guidance
   - Examples
   - Guidelines
   - Integration
   - References

4. Update diese README.md

## Integration mit Projekt-Dokumentation

```
AGENTS.md (Universal Setup/Testing)
    ↓
.github/copilot-instructions.md (Deployment/Release Workflows)
    ↓
.github/copilot/CONTEXT.md (Project Status/Decisions)
    ↓
.github/copilot/skills/ (Context Engineering Patterns) ← Du bist hier
```

## Skill Trigger Keywords

| Skill                | Trigger Keywords                                                                |
| -------------------- | ------------------------------------------------------------------------------- |
| context-fundamentals | "context budget", "progressive disclosure", "agent context", "optimize context" |
| multi-agent-patterns | "agent handoff", "agent coordination", "decision hierarchy", "parallel agents"  |
| evaluation           | "pre-release", "quality gate", "test coverage", "agent performance"             |

## Best Practices

1. **Explizite Skill Referenz**: Erwähne Skill Name in Prompt

   ```
   "Use multi-agent-patterns for handoff to Testing Agent"
   ```

2. **Context Budget Monitoring**: Prüfe regelmäßig Token Usage

   ```
   python scripts/evaluate_agents.py
   ```

3. **Quality Gates**: Alle L1 Checks vor jedem Release

   ```
   python -m pytest tests/ -v && coverage report
   ```

4. **Handoff Dokumentation**: Nutze Handoff Template aus multi-agent-patterns.md

## Quellen

- **Original Repository**:
  [Agent Skills for Context Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)
- **VS Code Copilot Docs**:
  [GitHub Copilot in VS Code](https://code.visualstudio.com/docs/copilot/overview)
- **Project Context**: [.github/copilot/CONTEXT.md](../CONTEXT.md)

---

**Erstellt**: 2026-01-01 **Last Updated**: 2026-01-01 **Maintainer**:
LUXORliving Development Team
