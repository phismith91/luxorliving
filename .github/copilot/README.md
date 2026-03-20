# GitHub Copilot Agents - LUXORliving Integration

This directory contains specialized Copilot agents that assist with different
aspects of the LUXORliving Home Assistant integration development.

## 📁 File Structure

### Three Core Documentation Files:

1. **[CONTEXT.md](CONTEXT.md)** - Single Source of Truth
   - Production environment, architecture, current status
   - **All agents MUST read this first**

2. **[README.md](README.md)** - This file (Agent Documentation)
   - Agent overview, invocation syntax, coordination

3. **[../copilot-instructions.md](../copilot-instructions.md)** - Operational
   Workflows
   - SSH deployment, release process, security
   - Attached to Copilot globally (siehe attachments in instructions)

### Additional Copilot Resources

- `rules/` → always-follow guardrails (testing, git workflow, security,
  performance)
- `commands/` → quick command cards (/plan, /tdd, /code-review, /build-fix,
  /update-docs, /update-codemaps)
- `skills/` → context engineering patterns + tdd-workflow, coding-standards
- `hooks/` → warn-only hooks for HA anti-patterns (asyncio.run, time.sleep)
- `mcp-configs/` → minimal MCP server skeleton (GitHub, local fs; tokens
  placeholder)

---

## Active Agents (7)

### 🏗️ **agent_architect.md** (Primary Authority)

**Role:** System Architecture & Code Quality **Responsibilities:**

- Final authority on all architectural decisions
- Code quality standards and reviews
- Module structure and data flow design
- Release quality gates
- Technical debt management

**When to use:** Architecture decisions, code reviews, refactoring, pre-release
audits

---

### 🐛 **agent_defect_tracker.md**

**Role:** Bug Management & Quality Assurance **Responsibilities:**

- Bug triage and prioritization (CRITICAL/HIGH/MEDIUM/LOW)
- Root cause analysis
- GitHub issue tracking
- Regression prevention
- Fix verification
- **CI failure classification** (formatting, tests, version, docs)
- **Version verification** (always from manifest.json, never hardcoded)

**When to use:** Bug reports, code review findings, regression testing, CI
failures, quality metrics

---

### 🚀 **agent_release_manager.md**

**Role:** Release Coordination, Merge Authority & Deployment
**Responsibilities:**

- **EXCLUSIVE:** Merges to main branch (PR-only workflow)
- Enforces formatting-first (black/isort before commits)
- Version management (semver, consistency checks)
- Changelog & release notes generation
- GitHub release creation
- Deployment coordination (remote HA SSH)
- Local validation scripts (validate_readme.sh, check_release_notes.sh)

**When to use:** Merging PRs, version bumps, releases, hotfixes, deployment, CI
failures

---

### 🧪 **agent_testing.md**

**Role:** Test Strategy & CI/CD Quality Assurance **Responsibilities:**

- Test coverage requirements (80%+ target)
- Unit and integration test design
- CI/CD pipeline maintenance
- **Sync test count in README.md** with pytest output
- Never skip failing tests (fix root cause)
- Simulation testing
- Test quality review

**When to use:** Writing tests, test failures, coverage analysis, CI/CD setup,
README test count updates

---

### 📦 **agent_hacs_compliance.md**

**Role:** HACS & Home Assistant Core Standards **Responsibilities:**

- HACS integration requirements
- Home Assistant core compliance
- Integration quality checklist
- Community standards

**When to use:** HACS submission, core integration prep, compliance checks

---

### 🔌 **agent_knx_protocol.md**

**Role:** KNX Protocol Expert **Responsibilities:**

- KNX specifications and standards
- Group address interpretation
- Datapoint types (DPT)
- Tunneling vs. routing
- Protocol debugging

**When to use:** KNX protocol questions, telegram interpretation, DPT mapping

---

### 🏠 **agent_luxor_expert.md**

**Role:** LUXORliving Hardware & Protocol Specialist **Responsibilities:**

- Theben LUXORliving specifics
- IP1 interface details
- LXP file format
- Hardware limitations
- Device capabilities

**When to use:** Hardware questions, LXP parsing, device-specific issues

---

## Utility/Workflow Agents (supporting)

- **agent_tdd_guide.md** → enforces pytest-first workflow with HA async patterns
- **agent_code_reviewer.md** → severity-ordered review checklist for HA/Python
- **agent_security_reviewer.md** → security/privacy checks and mitigations

## Archive

Agents moved to `archive/` are no longer actively used (features completed,
merged into other agents, or scope too narrow for a solo project):

- `agent_code_quality.md` → Merged into **agent_architect.md**
- `agent_documentation.md` → Documentation handled by architect
- `agent_config_flow.md` → Feature complete, archived
- `agent_lxp_import.md` → Feature complete, archived
- `agent_mapping.md` → Feature complete, archived
- `github_release_workflow.md` → Workflow documentation, not an agent
- `agent_defect_tracker.md` → GitHub Issues sufficient for solo project
- `agent_refactor_cleaner.md` → Scope covered by agent_architect
- `agent_build_error_resolver.md` → Too narrow; use agent_architect
- `agent_doc_updater.md` → Too narrow; use agent_architect
- `agent_planner.md` → Too narrow; use agent_architect

---

## Agent Invocation

### Syntax

```
agent_[name]: [your question or request]
```

### Examples

**Architecture Decision:**

```
agent_architect: Should we use polling or event-based updates for the coordinator?
```

**Bug Triage:**

```
agent_defect_tracker: Triage this error:
[paste error log]
```

**Release Preparation:**

```
agent_release_manager: Prepare v0.3.4 release with these changes:
- Fixed Options Flow reload
- Added password redaction to diagnostics
```

**Test Coverage:**

```
agent_testing: What tests are missing for the new scan_interval feature?
```

**HACS Compliance:**

```
agent_hacs_compliance: Check if we meet all HACS requirements
```

**KNX Question:**

```
agent_knx_protocol: How do I interpret DPT 9.001 (temperature) telegrams?
```

**Hardware Question:**

```
agent_luxor_expert: What's the maximum number of group addresses supported by IP1?
```

---

## Agent Coordination

### Decision Hierarchy

1. **agent_architect** has final authority on architecture and code quality
2. **agent_release_manager** has exclusive authority on merges to main and
   releases
3. Specialist agents provide expertise in their domains
4. **agent_defect_tracker** coordinates bug fixes across agents
5. All agents must format code (black/isort) before any commit

### Cross-Agent Workflow

**Example: New Feature Development**

1. **architect** → Defines architecture and module structure
2. **testing** → Plans test strategy and coverage
3. **[specialist]** → Implements domain-specific logic
4. **[any agent]** → **Formats code** (black + isort) before commit
5. **architect** → Reviews code quality
6. **testing** → Validates test coverage, syncs test count to README
7. **defect_tracker** → Tracks any bugs found
8. **[any agent]** → Creates PR with changes (never push to main directly)
9. **release_manager** → Reviews PR, merges after green CI, coordinates release

---

## 📋 Project Context File

**[CONTEXT.md](CONTEXT.md)** ist die **Single Source of Truth** für alle Agents
und Copilot.

### Enthält:

- 🏗️ **Production Environment:** Remote SSH deployment (100.97.159.88)
- 📊 **Current Status:** v0.6.1 (Released 2026-01-16), v0.7.0 roadmap
- 🔧 **Development Stack:** Python 3.13.11, HA 2026.1.x, pytest 9.0.0
- 🏛️ **Architecture:** Layer design, core decisions
- 🚀 **Release Process:** PR-only workflow, formatting-first, merge ownership
- 🔒 **Security:** SSH config (`-F /dev/null`), credentials management
- 🤖 **Agent Rules:** Decision hierarchy, coordination, quality gates

### Agent Requirements:

- ✅ **Read CONTEXT.md first** before working on any task
- ✅ **Format before commit:** Run black/isort ALWAYS before staging changes
- ✅ **Follow production environment** (Remote-first development)
- ✅ **Respect architecture principles** (Separation of concerns)
- ✅ **Use correct SSH syntax** (`ssh -F /dev/null`)
- ✅ **Maintain quality standards** (Tests, type hints, formatting)
- ✅ **Defer merges to Release Manager:** Only Release Manager merges to main
- ✅ **Never skip tests:** Fix root cause, never bypass

**Bei Widersprüchen zwischen Dokumenten hat CONTEXT.md Priorität.**

---

## Maintenance

### Adding a New Agent

1. Create `agent_[name].md` in this directory
2. Define role, responsibilities, and scope
3. Document when to use the agent
4. Add example interactions
5. Update this README
6. Inform **agent_architect** to update CONTEXT.md

### Retiring an Agent

1. Move to `archive/` directory
2. Update this README
3. If responsibilities still needed, merge into another agent
4. Document reason for retirement in archive

### Updating an Agent

1. Make changes to agent file
2. Test with sample queries
3. Document major changes in agent file header
4. Notify **agent_architect** if responsibilities change

---

## Best Practices

1. **Be specific** when invoking agents - include context and details
2. **Use the right agent** - don't ask testing questions to the architect
3. **Provide examples** - paste code, errors, or configurations
4. **Follow up** - verify agent responses match your expectations
5. **Combine agents** - complex tasks may need multiple specialist inputs

---

## Success Metrics

- **Response relevance:** Agent answers match their expertise area
- **Decision quality:** Architectural decisions are sound and maintainable
- **Bug resolution:** Defects tracked and resolved systematically
- **Release quality:** Releases have minimal bugs, clear documentation
- **Test coverage:** New features have comprehensive tests

---

Last Updated: 2026-03-20 Active Agents: 7 Utility Agents: 3 Archived Agents: 11
