# LUXORliving v1.0.0 — Gold Quality Scale & Documentation Overhaul

## Highlights

First stable release. Achieves full **HA Integration Quality Scale Gold** compliance
and ships a complete documentation rewrite with persona-based guides.

## Added

- **Gold Quality Scale**: icon translations (`icons.json`), exception translations
  (`HomeAssistantError` with `translation_key`), zeroconf discovery
  (`_knxip._udp.local.`), docs use-cases and known-limitations sections
- **Options flow sections**: Standard options (scan interval, log level, simulation
  mode) and collapsible Push Webhook advanced section
- **Persona documentation**: `USER_GUIDE.md`, `ADVANCED_GUIDE.md`,
  `DEVELOPER_GUIDE.md`, `REFERENCE.md` — replaces scattered per-audience docs
- **README hub**: short hub README with 3-step quickstart and persona router

## Changed

- **Docs overhaul**: archived 15 outdated/duplicate files; all doc links use
  absolute `/blob/main/` URLs (avoids 404 on old release tags)
- **Translation sync**: `strings.json`, `en.json`, `de.json`, `fr.json` updated
  for all new options fields and zeroconf confirm step

## Upgrade Notes

- Install v1.0.0 via HACS and restart Home Assistant
- No breaking changes — existing config entries are fully compatible
