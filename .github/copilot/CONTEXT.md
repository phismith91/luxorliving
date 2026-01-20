# LUXORliving Integration - Project Context

**Last Updated:** 2026-01-16 **Version:** v0.6.1 (Production) **Status:** Active
Development (Public Repository, HACS-ready) **Subscription:** GitHub Copilot
Individual ($10/month)

---

## 🎯 Project Overview

**LUXORliving** ist eine Home Assistant Custom Integration für Theben
LUXORliving KNX-Systeme über das IP1 Interface.

### Key Features

- KNX-Kommunikation via REST API (BAOS Web Services)
- LXP-Import für automatisches Entity-Mapping
- Unterstützte Plattformen: Light, Switch, Climate, Cover, Binary Sensor, Sensor
- Config Flow für UI-basierte Konfiguration
- Options Flow für Runtime-Anpassungen (scan_interval, etc.)
- Diagnostics mit sensiblen Daten-Redaktion

### Integration Design Principles

- **No ETS dependency** - verwendet LXP-Dateien statt ETS/knxproj
- **HACS-ready** - Community-friendly, maintainable long-term
- **Simulation Mode** - First-class support für Testing ohne Hardware
- **Deterministic Mapping** - Role-based auto-mapping aus LXP-Daten

### Current Version Status

- **Stable:** v0.6.1 (2026-01-16)
- **Quality:** Silver (Home Assistant Compliance)
- **Next Milestone:** Gold Compliance (Enhanced diagnostics, QA automation)
- **Roadmap:** v0.7.0 (Advanced features, community feedback)

---

## 🏗️ Production Environment

### Remote-First Development

**WICHTIG:** Development und Testing erfolgt remote via SSH!

- **Production HA:** 100.97.159.88 (via Tailscale VPN)
- **User:** phil
- **SSH Auth:** Key-based (`~/.ssh/id_rsa`) - passwortlos
- **Integration Path:** `/config/custom_components/luxor_living/`
- **Ownership:** root (benötigt `sudo` für File-Operationen)

### SSH Configuration

**Problem:** Lokale `~/.ssh/config` hat ungültige Einträge

**Solution:** Immer `-F /dev/null` verwenden:

```bash
ssh -F /dev/null phil@100.97.159.88 "command"
GIT_SSH_COMMAND='ssh -F /dev/null' git push
```

### Pre-Release Deployment Workflow

1. **Sync zu Temp:**

   ```bash
   ssh -F /dev/null phil@100.97.159.88 "mkdir -p /tmp/luxor_deploy"
   rsync -avz --exclude="__pycache__" \
     -e "ssh -F /dev/null" \
     custom_components/luxor_living/ \
     phil@100.97.159.88:/tmp/luxor_deploy/
   ```

2. **Copy mit sudo:**

   ```bash
   ssh -F /dev/null phil@100.97.159.88 \
     "sudo cp -r /tmp/luxor_deploy/* /config/custom_components/luxor_living/ && \
      rm -rf /tmp/luxor_deploy"
   ```

3. **HA Restart:** Manuell via UI (http://100.97.159.88:8123)
   - Einstellungen → System → Neustart
   - **Note:** SSH restart funktioniert nicht!

### Official Release Deployment

- Users installieren via HACS (planned for v1.0.0)
- Manual download via GitHub Releases
- File upload to `/config/custom_components/`

### Hardware Setup (Production)

```
Developer PC (Local) ──SSH──> Home Assistant (100.97.159.88)
         ↓                           ↓
    GitHub Repo                LAN: 192.168.1.x
                                     ↓
                            LUXORliving IP1: 192.168.1.3
                                ├── KNX/IP: 3671
                                ├── Web UI: 80/443
                                └── REST API (BAOS)
```

**Network:**

- Remote access via Tailscale VPN
- HA und IP1 im selben LAN (192.168.1.x)
- KNX Tunneling + Routing supported
- REST API bevorzugt (kein direktes Tunneling aktuell)

---

## 📦 Repository Structure

```
luxorliving/
├── custom_components/luxor_living/
│   ├── __init__.py          # Entry point, coordinator setup
│   ├── config_flow.py       # UI configuration
│   ├── diagnostics.py       # Debug data export
│   ├── entity_mapper.py     # LXP → HA entity mapping
│   ├── knx_gateway.py       # KNX protocol handler
│   ├── lxp_parser.py        # LXP file parser
│   ├── rest_client.py       # BAOS REST API client
│   └── [platform].py        # Platform implementations
├── tests/
│   ├── conftest.py          # Shared fixtures
│   └── test_*.py            # Unit tests (86 passing)
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── .github/
│   ├── copilot/
│   │   ├── CONTEXT.md       # This file (project context)
│   │   ├── README.md        # Agent documentation
│   │   ├── agent_*.md       # Specialized + utility agents
│   │   ├── skills/          # Context-engineering + coding/TDD skills
│   │   ├── rules/           # Guardrails (testing, git, security, performance)
│   │   ├── commands/        # Command cards (/plan, /tdd, /code-review, ...)
│   │   ├── hooks/           # Warn-only HA anti-pattern hooks
│   │   └── mcp-configs/     # Minimal MCP server configs (placeholders)
│   └── copilot-instructions.md  # Copilot global instructions
└── [config files]
```

---

## 🔧 Development Stack

### Python Environment

- **Python:** 3.13.11 (local), 3.11/3.13 (CI)
- **Home Assistant:** 2026.1.x (OS)
- **Test Framework:** pytest 9.0.0
- **pytest-homeassistant-custom-component:** 0.13.306
- **Venv:** `/home/phil/gitlab_github/luxorliving/venv/`
- **Formatters:** black, isort (enforced in CI)

### Key Dependencies

- `homeassistant` - Core HA
- `aiohttp` - Async HTTP client
- `voluptuous` - Schema validation
- `pytest`, `pytest-homeassistant-custom-component` - Testing
- `black`, `isort`, `mypy` - Code quality

### Quality Gates

- ✅ All tests passing (`pytest tests/ -v -m "not enable_socket"` → 294/294)- ✅
  **Gold Gates** enforced in CI: Smoke → Integration subset → HACS validation →
  Release dry-run (all must pass before merge)- ✅ Code formatted
  (black/isort) - MANDATORY before commits
- ✅ Local validation scripts pass (`./scripts/validate_readme.sh`,
  `./scripts/check_release_notes.sh`)
- ✅ Type checking (mypy) - Optional but recommended
- ✅ CI checks green (Release Checks, Code Quality, Tests)
- ✅ Optional: Pre-Release Testing auf Remote HA

---

## 🏛️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────┐
│         Config Flow (UI)                │
├─────────────────────────────────────────┤
│    Entity Mapper (LXP → HA Entities)    │
├─────────────────────────────────────────┤
│  Coordinator (State Management)         │
├─────────────────────────────────────────┤
│   KNX Gateway (Protocol Handler)        │
├─────────────────────────────────────────┤
│    REST Client (HTTP Communication)     │
└─────────────────────────────────────────┘
```

### Core Design Decisions

1. **Simulation Mode:** Dateibasierter Offline-Betrieb ohne Hardware
2. **LXP-First:** Entity-Mapping aus LXP-Export (nicht manuell)
3. **REST over Tunneling:** BAOS REST API statt direktem KNX Tunneling
4. **Polling Strategy:** Coordinator polling (event-based in backlog)
5. **Type Safety:** Type hints für alle öffentlichen APIs
6. **Error Handling:** Specific exceptions, kein `except:` ohne Type
7. **Separation of Concerns:** Klare Layer-Trennung (siehe Diagramm)

---

## 📊 Current Development Status

### v0.6.1 (Released 2026-01-16)

**Major Features:**

- ✅ Push webhook & WebSocket client for external KNX state updates
- ✅ Configurable authentication modes (none, token, bearer, HMAC-SHA256)
- ✅ Health endpoint with dynamic manifest version loading
- ✅ Comprehensive test suite (294/294 passing)
- ✅ Black/isort formatting enforcement in CI

**Quality Improvements:**

- ✅ Hardcoded versions eliminated (health endpoint loads from manifest.json)
- ✅ README.md test count sync (294 tests)
- ✅ Release checks include formatting validation
- ✅ CI workflow installs black/isort dependencies
- ✅ Release notes file structure standardized

**Agent System Updates:**

- ✅ Release Manager owns all merge operations
- ✅ Formatting-first workflow enforced
- ✅ Testing agent tracks test count in README
- ✅ Architect defers merges to Release Manager

**Status:**

- ✅ 294/294 tests passing (unit + integration-style)
- ✅ All CI checks green
- ✅ HACS-ready structure validated
- ✅ Silver compliance achieved

### v0.7.0 (Planned - Gold Compliance)

- ⏳ Enhanced diagnostics with consent UI
- ⏳ Automated QA matrix (HA versions, Python versions)
- ⏳ Blueprint automation examples
- ⏳ Dashboard templates
- ⏳ Error/retry policy documentation

### Known Limitations

1. **No Tunneling:** REST API only (kein direktes KNX Tunneling)
2. **No Events:** Polling-based updates (keine Bus-Events)
3. **IP1 Dependency:** Benötigt Theben IP1 Interface
4. **LXP Required:** Automatisches Mapping benötigt LXP-Export
5. **Manual Restart:** HA Restart via SSH funktioniert nicht

---

## 🚀 Release Process

### Semantic Versioning

- **MAJOR (X.0.0):** Breaking changes
- **MINOR (0.X.0):** New features, backward compatible
- **PATCH (0.0.X):** Bug fixes, enhancements

### Release Checklist

1. **Format Code:**
   `black custom_components tests scripts && isort custom_components tests scripts`
2. **Run Tests:** `pytest tests/ -v -m "not enable_socket"` (all 294 passing)
3. **Validate Locally:**
   `./scripts/validate_readme.sh && ./scripts/check_release_notes.sh`
4. **Update Metadata:**
   - Bump `manifest.json` "version"
   - Update `CHANGELOG.md` (move [Unreleased] to [X.Y.Z])
   - Update README.md release section and test count
   - Create `RELEASE_NOTES_vX.Y.Z.md`
5. **Create PR:** Push to branch, open PR, wait for green CI
6. **Merge PR:** Only after all checks pass (Release Manager authority)
7. **Tag & Release:** Create tag, build ZIP, `gh release create`
8. Optional: Deploy + Test auf Remote HA

**Siehe `agent_release_manager.md` für vollständigen Workflow**

---

## 🔒 Security

### SSH Key Authentication

- Local: `~/.ssh/id_rsa`
- Remote: `/etc/ssh/authorized_keys`
- No Passwords in code!

### Credentials Management

**NEVER commit:** Passwords, tokens, keys, credentials

**Bei versehentlichem Commit:** Siehe copilot-instructions.md für Recovery

### Diagnostics Redaction

- `CONF_PASSWORD` → `**REDACTED**`
- `CONF_LXP_FILE` → `**REDACTED**`

---

## 🤖 Agent Coordination

**See [README.md](README.md) for complete agent documentation.**

### Active Agents (7)

1. **agent_architect.md** - Architecture & Code Quality (Primary Authority)
2. **agent_defect_tracker.md** - Bug Management & QA
3. **agent_release_manager.md** - Release Coordination
4. **agent_testing.md** - Test Strategy & CI/CD
5. **agent_hacs_compliance.md** - HACS & HA Core Standards
6. **agent_knx_protocol.md** - KNX Protocol Expert
7. **agent_luxor_expert.md** - LUXORliving Hardware Specialist

### Decision Hierarchy

1. **agent_architect** - Final authority (L1)
2. **agent_luxor_expert** - Domain authority (L2)
3. **agent_knx_protocol** - KNX specifics (L2)
4. **Functional agents** - Domain implementations (L2/L3)

### Context Budgets (Context Engineering)

| Agent               | Level | Budget     | Primary Sources                        | Monitor | Authority               |
| ------------------- | ----- | ---------- | -------------------------------------- | ------- | ----------------------- |
| **Architect**       | L1    | 50k tokens | CONTEXT.md, ARCHITECTURE_DECISION.md   | <80%    | Architecture, Standards |
| **Release Manager** | L2    | 40k tokens | agent_release_manager.md, CI workflows | <80%    | Merges, Releases        |
| **KNX Protocol**    | L2    | 80k tokens | KNX_IMPLEMENTATION.md, lxp_parser.py   | <80%    | KNX Specs               |
| **Testing**         | L2    | 35k tokens | tests/, TESTS.md, pytest.ini           | <80%    | Test Strategy           |
| **Defect Tracker**  | L2    | 30k tokens | GitHub Issues, test failures           | <80%    | Bug Triage              |
| **HACS Compliance** | L2    | 25k tokens | hacs.json, manifest.json               | <80%    | HACS Standards          |
| **Luxor Expert**    | L2    | 30k tokens | LXP files, hardware docs               | <80%    | Hardware Specs          |

**Skills Reference**: [skills/](skills/) - Context Engineering Patterns

### AI Model Selection (Individual Plan)

**Subscription:** GitHub Copilot Individual ($10/month) - Limited Premium
requests

**Model-Use Guidelines:**

| Task Type                  | Recommended Model | Reason                             |
| -------------------------- | ----------------- | ---------------------------------- |
| **Quick edits, git ops**   | GPT-4o            | Fast, cost-effective, 128k context |
| **Code reviews**           | GPT-4o            | Good balance speed/quality         |
| **Complex refactoring**    | Claude 3.5 Sonnet | Best code quality, 200k context    |
| **Architecture decisions** | Claude 3.5 Sonnet | Deep reasoning, long context       |
| **LXP/KNX analysis**       | Claude 3.5 Sonnet | Handles large files well           |
| **Simple questions**       | GPT-4o            | Saves Premium quota                |
| **Documentation writing**  | GPT-4o            | Fast, coherent                     |
| **Debugging/reasoning**    | o1-preview/mini   | Deep analysis (use sparingly!)     |

**Premium Quota Management:**

- ✅ Use GPT-4o as default for most tasks
- ✅ Switch to Claude 3.5 Sonnet for complex code/architecture work
- ✅ Reserve o1-models for truly complex debugging
- ❌ Don't waste Premium on simple file edits
- ❌ Don't use Claude for basic git operations

**Cost Efficiency Tips:**

1. Use targeted searches (grep, semantic_search) before loading full files
2. Read only needed line ranges, not entire files
3. Batch independent operations in parallel
4. Clear conversation when switching contexts (new task)
5. Monitor token usage (stays visible in responses) | **HACS Compliance** | L2 |
   25k tokens | hacs.json, manifest.json | <80% | | **Code Quality** | L3 | 20k
   tokens | requirements_style.txt | <80% |

**Skills Reference**: [skills/](skills/) - Context Engineering Patterns

### All Agents Must:

1. ✅ **Read CONTEXT.md first** (Single Source of Truth)
2. ✅ Respect production environment (Remote SSH, `-F /dev/null`)
3. ✅ Follow architecture principles and code quality standards
4. ✅ Monitor context budget (<80% efficiency target)
5. ✅ Maintain quality (type hints, tests, formatting)
6. ✅ Track bugs via agent_defect_tracker
7. ✅ **Format before commit:** black/isort ALWAYS run first
8. ✅ **Never skip tests:** Fix root cause, never bypass
9. ✅ **Defer merges to Release Manager:** Only Release Manager merges to main
10. ✅ **Validate locally:** Run scripts before push (validate_readme.sh,
    check_release_notes.sh)

---

## Language Rules

- Copilot agents: **English**
- User prompts: **German or English**
- Code, comments, docs: **English only**

---

## 🔗 Important Links

- **Repository:** https://github.com/phismith91/luxorliving
- **Issues:** https://github.com/phismith91/luxorliving/issues
- **HA Docs:** https://developers.home-assistant.io/
- **HACS:** https://hacs.xyz/docs/publish/integration

---

## 📝 Notes

- `.lxp` files are primary automation metadata source
- Simulation mode must always work
- Simplicity > feature completeness
- Community standards matter
- See `copilot-instructions.md` for operational workflows

---

**This file is the Single Source of Truth for all Copilot Agents.** **Bei
Widersprüchen hat CONTEXT.md Priorität.** **For agent invocation syntax, see
[README.md](README.md).**
