# LUXORliving v0.3.4 Release Notes

**Release Date:** 2025-12-26  
**Type:** Patch Release (Bug Fixes + Quality Improvements)

---

## 🎯 Overview

This release addresses critical code review findings and significantly improves the project's agent-based development infrastructure. All 86 tests passing.

---

## 🛠️ Critical Fixes

### C1: Test Fixtures Missing
- **Problem:** Tests lacked proper Home Assistant test fixtures
- **Solution:** Created `tests/conftest.py` with MockConfigEntry and HA-compatible fixtures
- **Impact:** Proper test isolation and HA integration testing

### C2: Options Flow Reload
- **Problem:** Unclear if Options Flow changes trigger reload
- **Solution:** Verified correct implementation (already working via `async_update_options` listener)
- **Impact:** Scan interval changes apply without full restart

---

## ⚡ High Priority Improvements

### H2: Password Redaction in Diagnostics
- **Problem:** Sensitive credentials exposed in diagnostics export
- **Solution:** `CONF_PASSWORD` and `CONF_LXP_FILE` now show `**REDACTED**`
- **Impact:** Improved security for public bug reports

### H3: Enhanced Diagnostics Entity Handling
- **Problem:** Entity diagnostics were basic dict dumps
- **Solution:** 
  - Detailed entity list (first 50 entities with id, name, platform, group_address)
  - Summary section with total count and by-platform breakdown
  - Improved coordinator info (scan_interval_configured, last_exception)
- **Impact:** Better debugging capabilities

### H4: Consistent Constant Usage
- **Problem:** Inconsistent use of CONF_SCAN_INTERVAL
- **Solution:** Verified consistent usage across __init__.py and coordinator
- **Impact:** Code maintainability

---

## 🏗️ Agent Infrastructure Overhaul

### New Agent Structure (12 → 7 Active Agents)

**Created:**
- `agent_defect_tracker.md` - Systematic bug tracking and quality assurance
  - Bug severity classification (CRITICAL/HIGH/MEDIUM/LOW)
  - Root cause analysis workflows
  - GitHub issue integration
  - Regression prevention strategies

**Enhanced:**
- `agent_architect.md` - Merged code quality responsibilities
  - Added type hints requirements
  - Exception handling best practices
  - Logging standards (% formatting, no f-strings)
  - Code complexity limits
  - Code review process

**Archived (6 agents):**
- `agent_code_quality.md` → Merged into architect
- `agent_config_flow.md` → Feature complete
- `agent_lxp_import.md` → Feature complete
- `agent_mapping.md` → Feature complete
- `agent_documentation.md` → Handled by architect
- `github_release_workflow.md` → Not an agent

### Documentation Improvements

**Created:**
- `.github/copilot/README.md` - Comprehensive agent documentation
  - Agent invocation syntax and examples
  - Decision hierarchy and coordination
  - Cross-agent workflows
  - Best practices

**Rewrote:**
- `.github/copilot/CONTEXT.md` - Single Source of Truth
  - Removed outdated Proxmox/Madeira references
  - Updated to current SSH deployment (100.97.159.88)
  - Current development status (v0.3.3 → v0.3.4)
  - Architecture principles and design decisions
  - Release process and security guidelines
  - Agent coordination rules

---

## ✅ Quality Metrics

- **Tests:** 86/86 passing (3.17s)
- **Coverage:** Maintained
- **Code Quality:** Enhanced with agent standards
- **Security:** Improved with diagnostics redaction

---

## 📦 Installation

### Via SSH (Pre-Release Testing)
```bash
ssh -F /dev/null phil@100.97.159.88 "mkdir -p /tmp/luxor_deploy"
rsync -avz --exclude="__pycache__" \
  -e "ssh -F /dev/null" \
  custom_components/luxor_living/ \
  phil@100.97.159.88:/tmp/luxor_deploy/
ssh -F /dev/null phil@100.97.159.88 \
  "sudo cp -r /tmp/luxor_deploy/* /config/custom_components/luxor_living/ && \
   rm -rf /tmp/luxor_deploy"
```

Then restart HA via UI: http://100.97.159.88:8123

### Via GitHub Release
1. Download `luxor_living.zip` from releases
2. Extract to `/config/custom_components/`
3. Restart Home Assistant

---

## 🔗 Links

- **Repository:** https://github.com/phismith91/luxorliving
- **Issues:** https://github.com/phismith91/luxorliving/issues
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

---

## 🙏 Acknowledgments

This release focused on improving development infrastructure and code quality based on comprehensive code review findings. The new agent structure provides better systematic bug tracking and quality assurance for future development.

---

**Full Changelog:** https://github.com/phismith91/luxorliving/compare/v0.3.3...v0.3.4
