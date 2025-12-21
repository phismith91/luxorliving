# 🔥 CRITICAL: Integration Setup Required!

## Problem
Die luxor_living Integration hat **KEINE Config Entry** und wird deshalb **nicht geladen**!

Status-Updates funktionieren nicht, weil die gesamte Integration nicht startet.

## ✅ Lösung: Setup über UI

1. **Home Assistant öffnen**
2. **Einstellungen → Geräte & Dienste**
3. **+ Integration hinzufügen** klicken
4. **"LUXORliving"** suchen
5. **Setup Dialog ausfüllen:**
   ```
   Host: localhost
   Port: 3671
   Username: admin
   Password: admin
   LXP File: /home/phil/.homeassistant/luxor_living/Schmidt_Madeira_V0.8.lxp
   Connection Type: tunneling
   Simulation Mode: NO (unchecked)
   ```
6. **Absenden** → Integration wird geladen!

## 🧪 Verification

Nach Setup solltest du in den Logs sehen:

```
🔥🔥🔥 LUXOR SETUP STARTED 🔥🔥🔥
Parsing LXP file: /home/phil/.homeassistant/luxor_living/Schmidt_Madeira_V0.8.lxp
🔥 Mapped XX entities from LXP project
Setting up LUXORliving lights
Creating XX light entities
Setting up LUXORliving switches
Creating XX switch entities
📖 Sent read request to 1/0/0 (initial)
📖 Sent read request to 1/0/1 (initial)
...
```

## 🔍 Debug: Was passiert nach Setup

1. **__init__.py async_setup_entry()** wird aufgerufen
2. **LXP File** wird geparst → 17 Devices, ~100 Entities
3. **EntityMapper** extrahiert Datapoints:
   - `datapoints["OnOff"] = 2048`  # 1/0/0
   - `datapoints["StatusOnOff"] = 2304`  # 1/1/0
4. **KNX Gateway** verbindet sich mit localhost:3671
5. **Light/Switch Entities** werden erstellt mit:
   - `self._address_on = 2048`
   - `self._address_status = 2304`
6. **async_added_to_hass()** sendet für jede Entity:
   - `GroupValueRead` an Adresse `2304` (StatusOnOff)
7. **KNX Bus antwortet** mit `GroupValueResponse`
8. **_telegram_received_callback()** empfängt Antwort
9. **_handle_knx_update()** wird aufgerufen
10. **Entity State** wird aktualisiert!

## ⚠️ Warum ist Config Entry weg?

Manuelle Edits an `.storage/core.config_entries` werden von Home Assistant beim Restart überschrieben, wenn die Integration nicht korrekt registriert ist.

Der **einzige sichere Weg** ist Setup über die UI mit dem config_flow!
