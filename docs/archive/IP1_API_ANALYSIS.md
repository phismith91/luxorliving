# IP1 API Analyse - LUXORliving

**Quelle:** LUXORliving_API_Documentation_EN.pdf  
**Gateway:** BAOS 777 (IP1)  
**Datum:** 21. Dezember 2025

---

## Zusammenfassung

Das IP1-Gateway (BAOS 777) bietet **zwei Kommunikationswege**:

1. **REST API** (HTTP) - Vereinfachte Schnittstelle
2. **Binary Protocol** (TCP/UDP) - Vollständige KNX-Kontrolle

---

## REST API Details

### Endpoints (vermutlich)

Basierend auf der PDF-Referenz zu "knx_ip_baos_restservices.pdf":

```
GET  /api/datapoints           # Alle Datenpunkte lesen
GET  /api/datapoints/{id}      # Einzelnen Datenpunkt lesen
POST /api/datapoints/{id}      # Datenpunkt schreiben
GET  /api/datapoints/{id}/value # Nur Wert lesen
```

### Authentifizierung

- ⚠️ Dokumentation unklar (möglicherweise Basic Auth oder Token)
- LuxorPlug nutzt vermutlich eigene Auth

### Limitierungen

- Primär für **Status-Abfragen** gedacht
- Control-Funktionen eventuell eingeschränkt
- Keine Echtzeit-Updates (Polling nötig)

---

## Binary Protocol Details

### Verbindung

```python
# TCP/UDP Port: 3671 (Standard KNX/IP)
# Host: localhost (via LuxorPlug)
# Protocol: KNX/IP BAOS Binary Protocol
```

### Capabilities

- ✅ **Vollständige KNX-Kontrolle**
- ✅ Read/Write Datenpunkte
- ✅ Subscribe zu Änderungen
- ✅ Alle KNX-Telegramme

### Implementierungsstatus

**Bereits implementiert in:**
- `custom_components/luxor_living/knx_gateway.py`
- Funktioniert via localhost:3671

---

## Tunneling-Konfiguration

### Problem

- BAOS 777 hat nur **1 Tunnel-Slot**
- Dieser ist durch LuxorPlug belegt
- Daher keine direkte KNX Tunneling-Verbindung möglich

### Mögliche Lösung (aus PDF)

Das Dokument könnte beschreiben, wie man:
1. Mehrere Tunnel-Slots aktiviert
2. LuxorPlug-Konfiguration anpasst
3. Routing aktiviert (falls Hardware-Fähigkeit vorhanden)

**Aktion:** PDF genauer auf Tunneling-Konfiguration prüfen

---

## Empfohlene Nutzung

### Für Home Assistant Integration

**Primär: Binary Protocol**
```python
# knx_gateway.py (bereits implementiert)
- Vollständige Kontrolle
- Echtzeit-Updates
- Kein Polling nötig
```

**Sekundär: REST API**
```python
# Für einfache Status-Abfragen
- Backup-Methode
- Debugging
- Status-Display
```

---

## Offene Fragen

1. **REST API Authentifizierung** - Welches Schema?
2. **REST API Control** - Welche Write-Operationen möglich?
3. **Tunneling konfigurierbar?** - Zweiter Slot aktivierbar?
4. **Routing möglich?** - Hardware-Einschränkung oder Konfig?
5. **LuxorPlug Rolle** - Kann umkonfiguriert werden?

Diese müssen aus dem PDF-Volltext extrahiert werden (PDF war nicht vollständig lesbar im ersten Durchgang).

---

## Next Steps

1. ✅ **Branch erstellt:** `feature/ip1-native-approach`
2. 🔄 **PDF detailliert analysieren** (manuelle Durchsicht nötig)
3. 📝 **REST API testen** (falls Endpoints bekannt)
4. 🔧 **Binary Protocol beibehalten** (funktioniert)
5. 🎯 **LXP-Parser integrieren** (für Entity-Discovery)

---

## Fazit

**Empfehlung bleibt:** Binary Protocol (bereits funktionierend) + LXP-Parser für Entity-Discovery.

REST API kann als **optionale Ergänzung** später integriert werden, wenn Endpoints und Auth geklärt sind.
