# 🎉 LUXORliving v0.5.3

**Release Date:** 2. Januar 2026

## 🎯 Quality Assurance & Release Process Improvements

This release focuses on enhancing the quality assurance process and preventing documentation errors before releases.

---

## Highlights

### ✅ Quality Gates Implementation
- **Automated README.md Validation**: Script validates version consistency, test count accuracy, and documentation links
- **CHANGELOG.md Quality Gates**: Ensures proper release entries and prevents common mistakes
- **Pre-Release Validation**: 6-step automated quality gate (`./scripts/validate_readme.sh`)
- **Error Prevention**: Detects versioned [Unreleased] sections and missing release entries

### 📋 Documentation Improvements
- **Release Operations**: Enhanced with comprehensive quality gate workflows
- **Agent Coordination**: Updated release manager with CHANGELOG.md validation
- **GitHub Release Template**: Updated with current metrics (207 tests)
- **Review Report**: Added comprehensive RELEASE_OPERATIONS_REVIEW.md

---

## 📦 What's New

### Added
- **Automated Validation Script** (`scripts/validate_readme.sh`):
  - Version consistency checks (manifest.json ↔ README.md ↔ CHANGELOG.md)
  - Test count accuracy verification (pytest ↔ README.md)
  - Documentation link validation (no 404s)
  - CHANGELOG.md release entry validation
  - Detection of versioned [Unreleased] sections

- **Enhanced Documentation**:
  - Updated `docs/RELEASE_OPERATIONS.md` with quality gates
  - Added `RELEASE_OPERATIONS_REVIEW.md` (comprehensive review)
  - Updated `agent_release_manager.md` with CHANGELOG workflows
  - SSH workaround documentation (`-F /dev/null`)

### Fixed
- **CHANGELOG.md**: Corrected v0.5.2 release entry (was marked as [Unreleased])
- **README.md**: Removed broken link to non-existent `AGENTS.md`
- **Documentation**: Updated all test count references to 207
- **Release Process**: Eliminated RELEASE_NOTES.md references (uses CHANGELOG.md)

### Changed
- **Quality Standards**: README and CHANGELOG validated with same rigor as code tests
- **Release Workflow**: Mandatory validation script before each release
- **Error Prevention**: Common documentation mistakes caught automatically

---

## 📊 Quality Metrics

- **Tests:** 207/207 passing (100% success rate) ✅
- **Validation:** 6-step automated quality gate ✅
- **Quality Coverage:** README + CHANGELOG + Links + Version consistency
- **Type Hints:** 100% on critical modules
- **Code Style:** Black compliant
- **Documentation:** Complete and validated

---

## 🔧 Installation

### Via HACS (Recommended)
1. Open HACS → Integrations → ⋮ (menu) → Custom repositories
2. Add `https://github.com/phismith91/luxorliving` as Integration
3. Click Download → Restart Home Assistant

### Manual Installation
1. Download the latest release
2. Extract to `config/custom_components/luxor_living/`
3. Restart Home Assistant

### Configuration
1. **Settings** → **Devices & Services** → **Add Integration** → **LUXORliving**
2. Upload LXP file or enter path
3. Enter gateway IP
4. Select connection type (Tunneling recommended)
5. Click Submit

---

## 🚀 For Developers

### Pre-Release Validation
```bash
# Run before each release
./scripts/validate_readme.sh

# Checks:
# 1. Version consistency (manifest ↔ README ↔ CHANGELOG)
# 2. Test count accuracy (pytest ↔ README)
# 3. Documentation links (all files exist)
# 4. Outdated patterns detection
# 5. CHANGELOG release entry validation
# 6. [Unreleased] section validation
```

**Exit Codes:**
- `0` = All checks passed (safe to release)
- `1` = Errors found (must fix before release)

---

## ⚠️ Known Issues

No known issues in this release. See [Issues](https://github.com/phismith91/luxorliving/issues) for feature requests.

---

## 🙏 Credits

Thanks to all contributors and testers!

---

## 🔗 Links

- [GitHub Repository](https://github.com/phismith91/luxorliving)
- [CHANGELOG](./CHANGELOG.md)
- [Documentation](./docs/)
- [Installation Guide](./docs/INSTALLATION.md)
- [Issues](https://github.com/phismith91/luxorliving/issues)

---

**Full Changelog:** See [CHANGELOG.md](./CHANGELOG.md) for complete history
