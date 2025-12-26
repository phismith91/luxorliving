# GitHub Copilot Agents - LUXORliving Integration

This directory contains specialized Copilot agents that assist with different aspects of the LUXORliving Home Assistant integration development.

## 📁 File Structure

### Three Core Documentation Files:

1. **[CONTEXT.md](CONTEXT.md)** - Single Source of Truth
   - Production environment, architecture, current status
   - **All agents MUST read this first**
   
2. **[README.md](README.md)** - This file (Agent Documentation)
   - Agent overview, invocation syntax, coordination
   
3. **[../copilot-instructions.md](../copilot-instructions.md)** - Operational Workflows
   - SSH deployment, release process, security
   - Attached to Copilot globally (siehe attachments in instructions)

---

## Active Agents (7)

### 🏗️ **agent_architect.md** (Primary Authority)
**Role:** System Architecture & Code Quality  
**Responsibilities:**
- Final authority on all architectural decisions
- Code quality standards and reviews
- Module structure and data flow design
- Release quality gates
- Technical debt management

**When to use:** Architecture decisions, code reviews, refactoring, pre-release audits

---

### 🐛 **agent_defect_tracker.md**
**Role:** Bug Management & Quality Assurance  
**Responsibilities:**
- Bug triage and prioritization (CRITICAL/HIGH/MEDIUM/LOW)
- Root cause analysis
- GitHub issue tracking
- Regression prevention
- Fix verification

**When to use:** Bug reports, code review findings, regression testing, quality metrics

---

### 🚀 **agent_release_manager.md**
**Role:** Release Coordination & Deployment  
**Responsibilities:**
- Version management (semver)
- Changelog generation
- Release notes
- GitHub release creation
- Deployment coordination

**When to use:** Version bumps, releases, hotfixes, deployment planning

---

### 🧪 **agent_testing.md**
**Role:** Test Strategy & CI/CD  
**Responsibilities:**
- Test coverage requirements
- Unit and integration test design
- CI/CD pipeline
- Simulation testing
- Test quality review

**When to use:** Writing tests, test failures, coverage analysis, CI/CD setup

---

### 📦 **agent_hacs_compliance.md**
**Role:** HACS & Home Assistant Core Standards  
**Responsibilities:**
- HACS integration requirements
- Home Assistant core compliance
- Integration quality checklist
- Community standards

**When to use:** HACS submission, core integration prep, compliance checks

---

### 🔌 **agent_knx_protocol.md**
**Role:** KNX Protocol Expert  
**Responsibilities:**
- KNX specifications and standards
- Group address interpretation
- Datapoint types (DPT)
- Tunneling vs. routing
- Protocol debugging

**When to use:** KNX protocol questions, telegram interpretation, DPT mapping

---

### 🏠 **agent_luxor_expert.md**
**Role:** LUXORliving Hardware & Protocol Specialist  
**Responsibilities:**
- Theben LUXORliving specifics
- IP1 interface details
- LXP file format
- Hardware limitations
- Device capabilities

**When to use:** Hardware questions, LXP parsing, device-specific issues

---

## Archive

Agents moved to `archive/` are no longer actively used (features completed or merged into other agents):

- `agent_code_quality.md` → Merged into **agent_architect.md**
- `agent_documentation.md` → Documentation handled by architect
- `agent_config_flow.md` → Feature complete, archived
- `agent_lxp_import.md` → Feature complete, archived
- `agent_mapping.md` → Feature complete, archived
- `github_release_workflow.md` → Workflow documentation, not an agent

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
2. Specialist agents provide expertise in their domains
3. **agent_defect_tracker** coordinates bug fixes across agents
4. **agent_release_manager** coordinates releases with all agents

### Cross-Agent Workflow

**Example: New Feature Development**

1. **architect** → Defines architecture and module structure
2. **testing** → Plans test strategy and coverage
3. **[specialist]** → Implements domain-specific logic
4. **architect** → Reviews code quality
5. **testing** → Validates test coverage
6. **defect_tracker** → Tracks any bugs found
7. **release_manager** → Coordinates release when ready

---

## 📋 Project Context File

**[CONTEXT.md](CONTEXT.md)** ist die **Single Source of Truth** für alle Agents und Copilot.

### Enthält:
- 🏗️ **Production Environment:** Remote SSH deployment (100.97.159.88)
- 📊 **Current Status:** v0.3.3 → v0.3.4, development roadmap
- 🔧 **Development Stack:** Python 3.13.9, HA 2025.12.4, pytest
- 🏛️ **Architecture:** Layer design, core decisions
- 🚀 **Release Process:** Semver, deployment workflow
- 🔒 **Security:** SSH config, credentials management
- 🤖 **Agent Rules:** Decision hierarchy, coordination

### Agent Requirements:
- ✅ **Read CONTEXT.md first** before working on any task
- ✅ **Follow production environment** (Remote-first development)
- ✅ **Respect architecture principles** (Separation of concerns)
- ✅ **Use correct SSH syntax** (`ssh -F /dev/null`)
- ✅ **Maintain quality standards** (Tests, type hints, reviews)

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

Last Updated: 2025-12-26  
Active Agents: 7  
Archived Agents: 6
