# LUXORliving Integration - Project Context

**Last Updated:** 2025-12-26  
**Version:** v0.3.3 → v0.3.4  
**Status:** Active Development (Private Repository)

---

## 🎯 Project Overview

**LUXORliving** ist eine Home Assistant Custom Integration für Theben LUXORliving KNX-Systeme über das IP1 Interface.

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
- **Stable:** v0.3.3
- **Next Release:** v0.3.4 (Critical fixes + enhanced diagnostics)
- **Roadmap:** v0.4.0 (Coordinator polling strategy, HACS prep)

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
│   │   ├── CONTEXT.md      # This file (project context)
│   │   ├── README.md       # Agent documentation
│   │   └── agent_*.md      # Specialized agents
│   └── copilot-instructions.md  # Copilot global instructions
└── [config files]
```

---

## 🔧 Development Stack

### Python Environment
- **Python:** 3.13.9
- **Home Assistant:** 2025.12.4 (OS)
- **Test Framework:** pytest 9.0.0
- **pytest-homeassistant-custom-component:** 0.13.300
- **Venv:** `/home/phil/gitlab_github/luxorliving/venv/`

### Key Dependencies
- `homeassistant` - Core HA
- `aiohttp` - Async HTTP client
- `voluptuous` - Schema validation
- `pytest`, `pytest-homeassistant-custom-component` - Testing
- `black`, `isort`, `mypy` - Code quality

### Quality Gates
- ✅ All tests passing (`python -m pytest tests/ -v`)
- ✅ Code formatted (black, isort)
- ✅ Type checking (mypy)
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

### v0.3.4 (Ready for Release)

**Critical Fixes:**
- ✅ Test fixtures fehlen → `conftest.py` mit MockConfigEntry
- ✅ Options Flow reload → Verifiziert (bereits korrekt)

**High Priority:**
- ✅ Passwords in diagnostics → Redacted (`**REDACTED**`)
- ✅ Entity handling → Enhanced mit detailed list + summary
- ✅ CONF_SCAN_INTERVAL → Konsistent verwendet

**Agent Reorganization:**
- ✅ Created `agent_defect_tracker.md`
- ✅ Expanded `agent_architect.md` mit code quality
- ✅ Archived 6 obsolete agents (12 → 7 active)
- ✅ Created `.github/copilot/README.md`

**Status:**
- ✅ 86/86 tests passing
- ✅ Deployed to remote HA
- ⏳ Awaiting HA restart + manual testing
- ⏳ Git commit pending

### v0.4.0 (Planned)
- ⏳ Coordinator polling strategy evaluation
- ⏳ HACS submission preparation
- ⏳ Core integration readiness

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

1. `python -m pytest tests/ -v` (all passing)
2. Optional: Deploy + Test auf Remote HA
3. Bump `manifest.json` "version"
4. Update `CHANGELOG.md`
5. Git commit, tag, push (siehe copilot-instructions.md)
6. Create GitHub Release with `gh release create`

**Siehe `.github/copilot-instructions.md` für detaillierte Release-Commands**

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

1. **agent_architect** - Final authority
2. **agent_luxor_expert** - Domain authority
3. **agent_knx_protocol** - KNX specifics
4. **Functional agents** - Domain implementations

### All Agents Must:

1. ✅ Respect production environment (Remote SSH)
2. ✅ Use `ssh -F /dev/null` (lokale config defekt)
3. ✅ Follow architecture principles
4. ✅ Maintain quality (type hints, tests, reviews)
5. ✅ Track bugs via agent_defect_tracker
6. ✅ **Read CONTEXT.md first** (Single Source of Truth)

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

**This file is the Single Source of Truth for all Copilot Agents.**  
**Bei Widersprüchen hat CONTEXT.md Priorität.**  
**For agent invocation syntax, see [README.md](README.md).**

