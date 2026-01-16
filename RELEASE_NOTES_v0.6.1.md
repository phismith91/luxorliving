# 🎉 LUXORliving v0.6.1

**Release Date:** 16. Januar 2026

### ✨ Added

- **Push webhook & WebSocket client**
  - Optional `POST /api/luxor_living/push` endpoint for external KNX state pushes
  - Configurable WebSocket client (`push_ws_url`) for push-forwarders
  - Authentication modes: `none`, `token`, `bearer`, `hmac` (HMAC-SHA256)

### 🛠️ Changed

- Documented push options and added tests for push handling and WebSocket client

### 🧪 Testing & Quality

- **Tests:** 287/287 passing (unit + integration-style)
- **Quality gates:** README/CHANGELOG validation, HACS install test, zip structure validation

### ⚡ Upgrade Notes

- If you used earlier betas, remove nested copies before installing
- Install v0.6.1 via HACS and restart Home Assistant

---

For full changelog see `CHANGELOG.md`.
