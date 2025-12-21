# 🧪 Test Review & Cleanup - Agent Testing

**Rolle:** Testing & Simulation Agent  
**Datum:** 21. Dezember 2025  
**Version:** v0.2.0 (REST API Authentication)

---

## 📊 Test Inventory

### Bestehende Tests (9 Dateien, ~1682 Zeilen)

| Datei | Status | Kommentar |
|-------|--------|-----------|
| `test_config_flow.py` | ⚠️ **VERALTET** | Fehlen Username/Password Tests |
| `test_knx_gateway.py` | ⚠️ **VERALTET** | Fehlt REST API Integration |
| `test_light.py` | ✅ **OK** | Platform-Tests noch gültig |
| `test_switch.py` | ✅ **OK** | Platform-Tests noch gültig |
| `test_lxp_parser.py` | ✅ **OK** | Parser unverändert |
| `test_entity_mapper.py` | ✅ **OK** | Mapper unverändert |
| `test_integration.py` | ⚠️ **VERALTET** | Setup ohne Credentials |
| `test_knx_tunneling.py` | ⚠️ **SKELETON** | Nur Struktur, keine Implementation |
| `test_yaml_config.py` | ❌ **IRRELEVANT** | YAML-Ansatz nicht mehr verwendet |

---

## 🗑️ Zu löschen

### test_yaml_config.py
**Grund:** Native KNX YAML-Ansatz wurde zugunsten REST API + Custom Component aufgegeben.

Die Tests sind für einen nicht-implementierten Workflow (LXP → YAML → HA KNX Integration).

---

## ⚠️ Zu aktualisieren

### 1. test_config_flow.py

**Problem:**
- Testet nur `host` und `port`
- Fehlen: `username`, `password` Validierung
- Keine REST API Login-Tests

**Benötigt:**
```python
async def test_gateway_step_with_credentials()
async def test_invalid_credentials()
async def test_credential_validation()
```

### 2. test_knx_gateway.py

**Problem:**
- Gateway-Init ohne `username`/`password`
- Keine REST API Mock-Tests
- Fehlt 3-stufiges Setup (Login → Tunneling → KNX)

**Benötigt:**
```python
async def test_setup_with_rest_auth()
async def test_tunneling_activation()
async def test_cleanup_on_shutdown()
```

### 3. test_integration.py

**Problem:**
- Setup ohne Credentials in Config Entry
- Keine End-to-End Tests mit REST API

**Benötigt:**
```python
async def test_integration_setup_with_auth()
async def test_integration_cleanup()
```

### 4. test_knx_tunneling.py

**Problem:**
- Nur Skeleton-Code
- Keine echten Implementierungen
- Mock-Aufrufe fehlen

**Benötigt:**
- Alle Test-Methoden implementieren
- REST Client Mocks
- KNX Gateway Mocks

---

## ✅ Neu zu erstellen

### test_rest_client.py

**Grund:** Neuer REST API Client benötigt dedizierte Tests.

**Test-Cases:**
```python
class TestBAOSRestClient:
    async def test_login_success()
    async def test_login_invalid_credentials()
    async def test_enable_tunneling()
    async def test_disable_tunneling()
    async def test_logout()
    async def test_session_timeout()
    async def test_context_manager()
    async def test_diagnostics()
```

---

## 📋 Test-Strategie für v0.2.0

### Layer 1: Unit Tests

**REST Client:**
- ✅ Login/Logout
- ✅ Session Management
- ✅ Tunneling Activation
- ✅ Error Handling

**Config Flow:**
- ✅ LXP Upload
- ✅ Credential Validation
- ✅ Error Messages

**Gateway:**
- ✅ 3-Step Setup
- ✅ REST Integration
- ✅ Cleanup

### Layer 2: Integration Tests

**Setup Flow:**
- ✅ LXP → Config Entry → Gateway → Entities
- ✅ Mit Credentials
- ✅ Error Handling

**Platform Tests:**
- ✅ Light Platform (bereits vorhanden)
- ✅ Switch Platform (bereits vorhanden)

### Layer 3: Simulation Tests

**Simulation Mode:**
- ✅ Ohne echte Hardware
- ✅ Mock-Telegramme
- ✅ State-Management

---

## 🎯 Action Plan

### Phase 1: Cleanup ✂️
```bash
# Löschen
rm tests/test_yaml_config.py
```

### Phase 2: Neue Tests erstellen 🆕
```bash
# Erstellen
touch tests/test_rest_client.py
```

### Phase 3: Bestehende aktualisieren 🔧
```bash
# Aktualisieren
- tests/test_config_flow.py
- tests/test_knx_gateway.py
- tests/test_integration.py
- tests/test_knx_tunneling.py
```

### Phase 4: Ausführen 🧪
```bash
# Alle Tests
pytest tests/ -v

# Mit Coverage
pytest tests/ --cov=custom_components.luxor_living --cov-report=html
```

---

## 🔍 Review-Kriterien

Jeder Test muss:
- ✅ **Isoliert** sein (keine Abhängigkeiten)
- ✅ **Deterministisch** sein (reproduzierbar)
- ✅ **Schnell** sein (<1s pro Test)
- ✅ **Aussagekräftig** sein (klare Fehler-Messages)
- ✅ **Mockbar** sein (keine echte Hardware)

---

## 📈 Metriken

### Aktuell
```
Tests: ~23 (viele veraltet)
Coverage: ~35%
Lines: ~1682
```

### Ziel v0.2.0
```
Tests: ~30-35 (relevant)
Coverage: >60%
Lines: ~1800-2000
```

---

**Status:** ⏳ In Arbeit  
**Agent:** Testing & Simulation  
**Next:** Implementation
