# LUXORliving v0.6.0-beta.1 – Silver Compliance

Release date: 7 January 2026  
Status: BETA (testing welcome)

---

## Quality Scale – Silver achieved

This beta implements all critical features for Home Assistant Silver compliance, based on the official Quality Scale guidelines.

Silver requirements met:
- Bronze foundation
- Stable user experience
- Active code owner
- Error recovery
- Re-authentication flow (new)
- Multi-language support (new)
- Detailed documentation

---

## New features

### Re-authentication flow

User-friendly recovery on authentication failures:
- Trigger: after 3 consecutive login failures
- Repair flow UI: prompt to update credentials
- Auto-reload: integration reload after successful re-auth
- No re-setup required: configuration is preserved

How it works:
1. On auth error, a repair issue appears in Home Assistant
2. Click “Repair” → enter credentials
3. Integration reconnects automatically

### Internationalization (i18n)

Full translations for:
- German (de.json)
- French (fr.json)
- English (en.json)

Translated areas:
- Config flow (setup assistant)
- Options flow (settings)
- Error messages
- Repair flow (UI)

---

## Bug fixes

- Performance test fix: `test_integration_entity_creation_benchmark` no longer requires a `hass` fixture
- Test suite: all 212 tests passing

---

## Documentation updates

Added end-user documentation:
- Automation examples: docs/AUTOMATIONS.md
- Dashboard examples: docs/DASHBOARD_EXAMPLES.md
- Compatible devices: docs/COMPATIBLE_DEVICES.md

---

## Upgrade from v0.5.x

Fully compatible – no breaking changes.

Recommended via HACS:
1. HACS → Integrations → LUXORliving → Update

Manual update:
```bash
cd /config/custom_components
wget https://github.com/phismith91/luxorliving/archive/refs/tags/v0.6.0-beta.1.zip
unzip v0.6.0-beta.1.zip
```

After update:
- Restart Home Assistant
- Language follows HA system settings

---

## Roadmap toward Gold

Next steps:
1. Automatic gateway discovery (SSDP/mDNS)
2. Reconfiguration flow (change IP/credentials via UI)
3. Additional end-user docs (blueprints)

---

## Technical details

Changed files:
- custom_components/luxor_living/repairs.py (new)
- custom_components/luxor_living/translations/ (new: de.json, fr.json, en.json)
- custom_components/luxor_living/coordinator.py – auth failure tracking
- custom_components/luxor_living/strings.json – issue/repair texts
- custom_components/luxor_living/manifest.json – version bump
- docs/AUTOMATIONS.md – new
- docs/DASHBOARD_EXAMPLES.md – new
- docs/COMPATIBLE_DEVICES.md – new

Dependencies:
- No new dependencies
- Home Assistant ≥ 2025.12.0

---

## Links

- Repository: https://github.com/phismith91/luxorliving
- Documentation: https://github.com/phismith91/luxorliving/tree/main/docs
- Changelog: https://github.com/phismith91/luxorliving/blob/main/CHANGELOG.md
- Quality Scale: https://www.home-assistant.io/docs/quality_scale/

---

## Contributors

- @phismith91 – implementation & testing

Special thanks:
- Home Assistant community for Quality Scale guidelines
- GitHub Copilot for code review support

---

Planned next stable: v0.6.0 (after successful beta)
