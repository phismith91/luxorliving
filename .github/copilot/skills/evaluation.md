---
name: evaluation
description: Evaluation Framework für LUXORliving - Testing Quality, Agent Performance, Context Engineering Metrics
---

# Evaluation für LUXORliving

## When to Activate

- Vor jedem Release (Quality Gate)
- Bei Agent Performance Problemen
- Wenn Test Coverage sinkt
- Bei Context Engineering Optimierung

## Core Concepts

**Multi-Level Evaluation**:
- **L1: Code Quality**: Tests, Coverage, Linting
- **L2: Agent Performance**: Context Usage, Decision Quality
- **L3: System Behavior**: Integration Tests, Real-World Performance

**Automated Gates**: CI/CD Checks vor Release

**LLM-as-Judge**: Für subjektive Quality Metrics (Code Readability, Documentation Quality)

## LUXORliving Evaluation Framework

### L1: Code Quality Metrics

```bash
# Pre-Release Checklist (automatisiert in CI)

# 1. Unit Tests
python -m pytest tests/ -v
# PASS Criteria: All 148+ tests passing

# 2. Coverage
python -m pytest --cov=custom_components.luxor_living tests/
# PASS Criteria: >80% coverage

# 3. Type Checking
mypy custom_components/luxor_living/
# PASS Criteria: No errors

# 4. Code Formatting
black --check custom_components/luxor_living/ tests/
isort --check-only custom_components/luxor_living/ tests/
# PASS Criteria: No changes needed

# 5. Linting (optional)
ruff check custom_components/luxor_living/
# PASS Criteria: No critical issues
```

### L2: Agent Performance Metrics

```markdown
## Agent Evaluation Rubric

| Metric                 | Measurement                 | Target      | Current |
| ---------------------- | --------------------------- | ----------- | ------- |
| **Context Efficiency** | Token Usage / Task          | <50k tokens | ?       |
| **Decision Quality**   | Conflicts / 10 Decisions    | <1          | ?       |
| **Handoff Clarity**    | Undefined Context / Handoff | 0           | ?       |
| **Scope Isolation**    | File Overlaps / Agent Pair  | 0           | ?       |
| **Authority Respect**  | L3 overrides L1 / Month     | 0           | ?       |

### Measurement Script

```python
# scripts/evaluate_agents.py

def measure_context_efficiency():
    """Analysiere CONTEXT.md für Token Usage"""
    agents = parse_agent_sections("CONTEXT.md")
    
    for agent in agents:
        tokens_used = count_tokens(agent.loaded_files)
        tokens_budget = agent.context_budget
        efficiency = tokens_used / tokens_budget
        
        print(f"{agent.name}: {efficiency:.1%} budget used")
        
        if efficiency > 0.8:
            print(f"⚠️  {agent.name} approaching budget limit!")

def detect_file_overlaps():
    """Finde Agents die gleiche Files laden"""
    agent_files = {}
    
    for agent in agents:
        agent_files[agent.name] = set(agent.loaded_files)
    
    for a1, a2 in combinations(agents, 2):
        overlap = agent_files[a1] & agent_files[a2]
        if overlap:
            print(f"Overlap: {a1} ↔ {a2}: {overlap}")
```

### L3: System Behavior Evaluation

```python
# tests/test_integration_quality.py

import pytest
from custom_components.luxor_living import LuxorLivingIntegration

@pytest.mark.integration
async def test_full_lxp_workflow():
    """End-to-End Test: LXP Upload → Entity Creation"""
    
    # Step 1: Upload LXP
    result = await upload_lxp("docs/Hauptwohnung.lxp")
    assert result.success
    
    # Step 2: Parse Elements
    elements = await parse_lxp_elements(result.file_id)
    assert len(elements) == 243  # Expected element count
    
    # Step 3: Create Entities
    entities = await create_entities_from_elements(elements)
    
    # Evaluation: Platform Distribution
    assert entities.count_by_platform("light") == 89
    assert entities.count_by_platform("switch") == 54
    assert entities.count_by_platform("climate") == 12
    assert entities.count_by_platform("cover") == 88
    
    # Evaluation: DPT Mapping Correctness
    for entity in entities:
        assert entity.dpt in SUPPORTED_DPTS
        assert entity.group_address is not None

@pytest.mark.evaluation
async def test_agent_context_isolation():
    """Validate: Agents don't leak context"""
    
    # Scenario: KNX Agent modifies lxp_parser.py
    knx_agent = Agent("KNX Protocol")
    knx_agent.modify_file("lxp_parser.py")
    
    # Testing Agent should NOT see uncommitted changes
    testing_agent = Agent("Testing")
    visible_files = testing_agent.list_modified_files()
    
    assert "lxp_parser.py" not in visible_files
    # Context isolation: Changes only visible after commit
```

## LLM-as-Judge für Subjektive Metrics

```python
# scripts/llm_judge.py

from openai import OpenAI

def evaluate_code_readability(file_path: str) -> dict:
    """Verwendet GPT-4 um Code Readability zu bewerten"""
    
    client = OpenAI()
    code = read_file(file_path)
    
    rubric = """
    Evaluate Python code readability on 1-5 scale:
    
    5: Exceptional - Self-documenting, perfect structure
    4: Good - Clear naming, good comments
    3: Acceptable - Understandable with effort
    2: Poor - Confusing structure or naming
    1: Very Poor - Difficult to understand
    
    Consider:
    - Function/variable naming clarity
    - Code structure and organization
    - Comment quality and necessity
    - Complexity management
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": rubric},
            {"role": "user", "content": f"Evaluate this code:\n\n{code}"}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def evaluate_documentation_quality(doc_path: str) -> dict:
    """Bewertet Documentation Completeness"""
    
    rubric = """
    Evaluate documentation on 1-5 scale:
    
    5: Complete - All sections, examples, troubleshooting
    4: Good - Core sections covered, some examples
    3: Acceptable - Basic information present
    2: Incomplete - Missing critical sections
    1: Poor - Barely documented
    
    Check for:
    - Installation instructions
    - Configuration examples
    - API reference
    - Troubleshooting guide
    - Update/changelog
    """
    
    # Similar LLM call as above
    return evaluate_with_rubric(doc_path, rubric)
```

## Practical Guidance

### Pre-Release Evaluation Checklist

```markdown
## Release v0.3.4 Quality Gate

### L1: Code Quality ✅
- [x] All 148 tests passing
- [x] Coverage: 87% (>80% target)
- [x] mypy: No errors
- [x] black/isort: Formatted

### L2: Agent Performance ⚠️
- [x] Context Efficiency: 68% avg (target <80%)
- [x] Zero decision conflicts
- [ ] Documentation: 3/5 (LLM-Judge) → Needs improvement

### L3: System Behavior ✅
- [x] Integration test: All platforms working
- [x] LXP parsing: 243/243 elements mapped
- [x] SSH Deploy: Tested on remote HA

### Blockers
- None

### Recommendations
- Improve docs/ with more examples (LLM-Judge score 3→4)
- KNX Protocol Agent approaching 80% context budget → Optimize

**Decision**: Release APPROVED ✅
```

### Continuous Evaluation (CI/CD)

```yaml
# .github/workflows/quality-gate.yml

name: Quality Gate

on: [push, pull_request]

jobs:
  L1-code-quality:
    runs-on: ubuntu-latest
    steps:
      - name: Run Tests
        run: python -m pytest tests/ -v
      
      - name: Check Coverage
        run: |
          coverage run -m pytest tests/
          coverage report --fail-under=80
      
      - name: Type Check
        run: mypy custom_components/luxor_living/
      
      - name: Format Check
        run: |
          black --check .
          isort --check-only .
  
  L2-agent-performance:
    runs-on: ubuntu-latest
    steps:
      - name: Evaluate Agent Context Usage
        run: python scripts/evaluate_agents.py
      
      - name: Detect Context Overlaps
        run: python scripts/detect_overlaps.py
  
  L3-integration:
    runs-on: ubuntu-latest
    steps:
      - name: Integration Tests
        run: python -m pytest tests/ -m integration -v
```

## Examples

**Example 1: Coverage Regression Detection**

```bash
# Current Release: v0.3.3 (87% coverage)
# New Changes: Add binary_sensor.py

python -m pytest --cov=custom_components.luxor_living tests/

# Output:
# coverage: 84% (-3%)
# FAIL: Below 80% threshold → Block release

# Action:
# Testing Agent: Add test_binary_sensor.py
# Re-run: 88% coverage (+1%) → PASS
```

**Example 2: Agent Context Budget Alert**

```python
# scripts/evaluate_agents.py output

Agent Context Budget Report:
- Architect: 22k/50k (44%) ✅
- KNX Protocol: 78k/80k (98%) ⚠️ CRITICAL
- Testing: 18k/30k (60%) ✅
- Documentation: 31k/40k (78%) ⚠️ Warning
- Deployment: 12k/35k (34%) ✅
- Security: 8k/25k (32%) ✅
- Code Style: 9k/20k (45%) ✅

Recommendations:
⚠️ KNX Protocol: Implement progressive disclosure for lxp_parser.py
⚠️ Documentation: Archive old ROADMAP docs
```

## Guidelines

1. **Automated L1 Checks**: Immer in CI/CD (Tests, Coverage, Linting)
2. **Manual L2 Review**: Vor jedem Release (Agent Performance)
3. **Integration Tests**: Bei major Changes (Platform additions)
4. **LLM-as-Judge**: Für subjektive Metrics (Code/Doc Quality)
5. **Context Monitoring**: Wöchentlich Agent Budget prüfen
6. **Regression Prevention**: Coverage darf nie <80% fallen
7. **Quality Gates**: Alle L1 Checks müssen grün sein vor Merge

## Integration

- **context-fundamentals**: Context Budget Tracking
- **multi-agent-patterns**: Agent Performance Metrics
- **tool-design**: Evaluation Tool Design Best Practices

## References

- [docs/TESTS.md](../../docs/TESTS.md) - Testing Documentation
- [pytest.ini](../../pytest.ini) - Test Configuration
- [Agent Skills Repository](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)

---

**Created**: 2026-01-01  
**Last Updated**: 2026-01-01  
**Author**: LUXORliving QA Team  
**Version**: 1.0.0
