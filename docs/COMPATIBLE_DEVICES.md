# Compatible Devices – LUXORliving

List of KNX devices tested with and supported by the LUXORliving integration.

Note: This list is based on real, tested LXP projects. Other Theben models may
also work. If your device is missing, please open an issue with details (see
links below).

## Contents

- Theben devices
- Supported features per platform
- Tested projects summary
- Known limitations
- Compatibility matrix
- Links and feedback

---

## Theben devices (tested)

### Switching actuators (lights/switches)

| Model | Type            | Channels | HA Platform    | Status |
| ----- | --------------- | -------- | -------------- | ------ |
| S4    | Switch actuator | 4        | switch / light | Tested |
| S8    | Switch actuator | 8        | switch / light | Tested |
| S16   | Switch actuator | 16       | switch / light | Tested |

Features:

- On/off switching
- State feedback
- Panic function
- Central off

### Dimming actuators (dimmable lights)

| Model | Type         | Channels | HA Platform | Status |
| ----- | ------------ | -------- | ----------- | ------ |
| D2    | Dim actuator | 2        | light       | Tested |
| D4    | Dim actuator | 4        | light       | Tested |

Features:

- On/off switching
- Brightness control (0–100%)
- Relative dimming (brighter/darker)
- Dim value limits
- Smooth transitions

### Blind/shutter actuators (covers)

| Model | Type           | Channels | HA Platform | Status |
| ----- | -------------- | -------- | ----------- | ------ |
| J4    | Blind actuator | 4        | cover       | Tested |
| J8    | Blind actuator | 8        | cover       | Tested |

Features:

- Open/close/stop
- Position control (0–100%)
- Tilt control (0–100%)
- State feedback (position + tilt)
- Window contact integration
- Weather protection (rain/wind/frost)
- Panic mode

Device classes:

- Auto-detection: shutter vs blind (based on tilt support)

### Heating actuators (climate)

| Model | Type             | Channels | HA Platform | Status |
| ----- | ---------------- | -------- | ----------- | ------ |
| H6    | Heating actuator | 6        | climate     | Tested |

Features:

- Current temperature
- Setpoint control (5–35 °C, 0.5 °C steps)
- Valve position (0–100%)
- HVAC modes (heat/off)
- Window contact integration
- Heat/cool switching (when configured in ETS)

Zones:

- Floor heating
- Infrared heating
- Wall heating

### Push buttons (binary sensors / switches)

| Model | Type     | Channels | HA Platform            | Status |
| ----- | -------- | -------- | ---------------------- | ------ |
| iON8  | 8-button | 8 + 2    | switch / binary_sensor | Tested |
| E1    | 2-button | 2        | switch / binary_sensor | Tested |

Features:

- Binary switch states
- Temperature sensor (iON8)
- Multi-channel per device

### Motion/presence detectors (binary sensors)

| Model | Type              | Features   | HA Platform   | Status |
| ----- | ----------------- | ---------- | ------------- | ------ |
| BI180 | Presence detector | 180°, temp | binary_sensor | Tested |
| BI360 | Presence detector | 360°, temp | binary_sensor | Tested |

Features:

- Motion/presence detection
- Brightness (lux)
- Temperature (separate sensor)

Device class: `motion`

### Weather station (sensors)

| Model             | Type           | Measurements    | HA Platform | Status |
| ----------------- | -------------- | --------------- | ----------- | ------ |
| Weather Station 1 | Outdoor sensor | temp, wind, lux | sensor      | Tested |

Sensors:

- Outdoor temperature (°C)
- Wind speed (km/h)
- Brightness middle/left/right (lux)

Device classes:

- Temperature: `temperature`
- Wind: `wind_speed`
- Brightness: `illuminance`

### Binary input module

| Model           | Type         | Inputs | HA Platform   | Status |
| --------------- | ------------ | ------ | ------------- | ------ |
| Binary Input 32 | Input module | 32     | binary_sensor | Tested |

Use cases:

- Window contacts
- Door contacts
- Alarms/faults
- External sensors

---

## Supported features per platform

### Light

- On/off
- Brightness control (dimmers)
- Relative dimming (+/–)
- Transition effects
- State feedback
- No color control (not supported by KNX devices)

### Cover

- Open/close/stop
- Position control (0–100%)
- Tilt control (0–100%)
- State feedback
- Window contacts
- Weather protection
- Panic function

### Climate

- Current temperature
- Setpoint control
- Valve position
- HVAC modes (heat/off)
- Window contact integration
- Cooling only when configured in ETS
- No "auto" mode (KNX limitation)

### Binary sensor

- Motion/presence
- Window/door contacts

### Sensor

- Temperature
- Brightness (lux)
- Wind speed
- Auto-discovery of DPT 9.xxx sensors

---

## Tested project: Hauptwohnung.lxp (reference)

Statistics:

- 63 devices
- 851 datapoints
- 137 Home Assistant entities

Device distribution: | Type | Count | HA Entities | |
----------------------------- | ----- | ---------------- | | Switch actuators
(S4/S8/S16) | 3 | 24 lights | | Dim actuators (D2/D4) | 10 | 19 lights | | Blind
actuators (J4/J8) | 2 | 15 covers | | Heating actuators (H6) | 2 | 9 climate | |
Push buttons (iON8, E1, etc.) | 30+ | 60+ switches | | Motion/presence detectors
| 4 | 4 binary sensors | | Weather station | 1 | 5 sensors |

---

## Known limitations

### KNX-specific

1. No color control for lights
2. Heating "auto" mode not supported (use ETS configuration)
3. Group address limits depend on model; complex scenarios require ETS
   configuration

### Integration-specific

1. LXP project file required (primary configuration)
2. State updates use KNX telegrams; coordinator polling as fallback
   (configurable)
3. REST API: use HTTPS; TLS 1.2+ required (self-signed certificates accepted)

---

## Compatibility matrix

| Device type     | Light | Switch | Cover | Climate | Binary sensor | Sensor     |
| --------------- | ----- | ------ | ----- | ------- | ------------- | ---------- |
| S4/S8/S16       | Yes   | Yes    | No    | No      | No            | No         |
| D2/D4           | Yes   | No     | No    | No      | No            | No         |
| J4/J8           | No    | No     | Yes   | No      | No            | No         |
| H6              | No    | No     | No    | Yes     | No            | No         |
| iON8            | No    | Yes    | No    | No      | No            | Yes (temp) |
| BI180/360       | No    | No     | No    | No      | Yes           | Yes (temp) |
| Weather station | No    | No     | No    | No      | No            | Yes        |
| Binary input    | No    | No     | No    | No      | Yes           | No         |

---

## Links and feedback

- Theben products: https://www.theben.de/
- LUXORplug software: https://www.theben.de/de/service/software-und-apps
- KNX Association: https://www.knx.org/
- ETS software: https://www.knx.org/knx-en/for-professionals/software/ets/

Missing device or issues? Create an issue:
https://github.com/phismith91/luxorliving/issues/new

# Compatible Devices - LUXORliving

Liste der getesteten und kompatiblen KNX-Geräte mit der LUXORliving Integration.

## 📋 Inhalt

- [Theben Geräte](#theben-geräte)
- [Unterstützte Funktionen](#unterstützte-funktionen)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)

---

## 🏭 Theben Geräte

### ✅ Vollständig getestet & kompatibel

Diese Geräte wurden mit echten LXP-Projekten getestet und funktionieren
vollständig:

#### Schaltaktoren (Switches/Lights)

| Modell  | Typ         | Kanäle | HA Platform        | Status      |
| ------- | ----------- | ------ | ------------------ | ----------- |
| **S4**  | Schaltaktor | 4      | `switch` / `light` | ✅ Getestet |
| **S8**  | Schaltaktor | 8      | `switch` / `light` | ✅ Getestet |
| **S16** | Schaltaktor | 16     | `switch` / `light` | ✅ Getestet |

**Funktionen:**

- Ein/Aus-Schaltung
- Status-Rückmeldung
- Panik-Funktion
- Zentral-Aus

#### Dimmaktoren (Dimmable Lights)

| Modell | Typ       | Kanäle | HA Platform | Status      |
| ------ | --------- | ------ | ----------- | ----------- |
| **D2** | Dimmaktor | 2      | `light`     | ✅ Getestet |
| **D4** | Dimmaktor | 4      | `light`     | ✅ Getestet |

**Funktionen:**

- Ein/Aus-Schaltung
- Helligkeitssteuerung (0-100%)
- Relative Dimmung (heller/dunkler)
- Dimmwertbegrenzung
- Sanfte Übergänge

#### Jalousieaktoren (Covers)

| Modell | Typ           | Kanäle | HA Platform | Status      |
| ------ | ------------- | ------ | ----------- | ----------- |
| **J4** | Jalousieaktor | 4      | `cover`     | ✅ Getestet |
| **J8** | Jalousieaktor | 8      | `cover`     | ✅ Getestet |

**Funktionen:**

- Auf/Ab/Stopp
- Positionssteuerung (Höhe 0-100%)
- Lamellensteuerung (Tilt 0-100%)
- Status-Rückmeldung (Position + Lamellen)
- Fensterkontakt-Integration
- Wetterschutz (Regen/Wind/Frost)
- Panik-Modus

**Device Classes:**

- Automatische Erkennung: Shutter vs. Blind (basierend auf Tilt-Unterstützung)

#### Heizungsaktoren (Climate)

| Modell | Typ           | Kanäle | HA Platform | Status      |
| ------ | ------------- | ------ | ----------- | ----------- |
| **H6** | Heizungsaktor | 6      | `climate`   | ✅ Getestet |

**Funktionen:**

- Temperatur-Anzeige (Istwert)
- Sollwert-Steuerung (5-35°C, Schritte 0.5°C)
- Ventilposition (Stellgröße 0-100%)
- HVAC-Modi (Heat/Off)
- Fensterkontakt-Integration
- Umschaltung Heizen/Kühlen (sofern konfiguriert)

**Unterstützte Zonen:**

- Fußbodenheizung (FBH)
- Infrarot-Heizung
- Wandheizung

#### Taster (Binary Sensors / Switches)

| Modell   | Typ           | Kanäle | HA Platform                | Status      |
| -------- | ------------- | ------ | -------------------------- | ----------- |
| **iON8** | Taster 8-fach | 8 + 2  | `switch` / `binary_sensor` | ✅ Getestet |
| **E1**   | Taster        | 2      | `switch` / `binary_sensor` | ✅ Getestet |

**Funktionen:**

- Binäre Schaltzustände
- Temperatursensor (bei iON8)
- Mehrere Kanäle pro Gerät

#### Bewegungsmelder (Binary Sensors)

| Modell    | Typ           | Features   | HA Platform     | Status      |
| --------- | ------------- | ---------- | --------------- | ----------- |
| **BI180** | Präsenzmelder | 180°, Temp | `binary_sensor` | ✅ Getestet |
| **BI360** | Präsenzmelder | 360°, Temp | `binary_sensor` | ✅ Getestet |

**Funktionen:**

- Bewegungserkennung
- Helligkeitsmessung
- Temperaturmessung (separater Sensor)

**Device Class:** `motion`

#### Wetterstation (Sensors)

| Modell              | Typ         | Messwerte       | HA Platform | Status      |
| ------------------- | ----------- | --------------- | ----------- | ----------- |
| **Wetterstation 1** | Außensensor | Temp, Wind, Lux | `sensor`    | ✅ Getestet |

**Sensoren:**

- Außentemperatur (°C)
- Windgeschwindigkeit (km/h)
- Helligkeit Mitte (Lux)
- Helligkeit Links (Lux)
- Helligkeit Rechts (Lux)

**Device Classes:**

- Temperature: `temperature`
- Wind: `wind_speed`
- Brightness: `illuminance`

#### Binäreingänge

| Modell              | Typ           | Eingänge | HA Platform     | Status      |
| ------------------- | ------------- | -------- | --------------- | ----------- |
| **Binäreingang 32** | Eingangsmodul | 32       | `binary_sensor` | ✅ Getestet |

**Funktionen:**

- Fensterkontakte
- Türkontakte
- Störmeldungen
- Externe Sensoren

---

## 🔌 Unterstützte Funktionen

### Nach Platform

#### Light Platform

- ✅ Ein/Aus-Schaltung
- ✅ Helligkeitssteuerung (Dimmaktoren)
- ✅ Relative Dimmung (+/-)
- ✅ Transition-Effekte
- ✅ Status-Rückmeldung
- ❌ Farbsteuerung (nicht von KNX-Geräten unterstützt)

#### Cover Platform

- ✅ Auf/Ab/Stopp
- ✅ Positionssteuerung (0-100%)
- ✅ Lamellensteuerung (Tilt 0-100%)
- ✅ Status-Rückmeldung
- ✅ Fensterkontakt-Integration
- ✅ Wetterschutz-Automatik
- ✅ Panik-Funktion

#### Climate Platform

- ✅ Temperatur-Anzeige
- ✅ Sollwert-Steuerung
- ✅ Ventilposition
- ✅ HVAC-Modi (Heat/Off)
- ✅ Fensterkontakt
- ⚠️ Kühlen (nur wenn in ETS konfiguriert)
- ❌ Auto-Modus (KNX-Limitierung)

#### Binary Sensor Platform

- ✅ Bewegungsmelder
- ✅ Präsenzmelder
- ✅ Fensterkontakte
- ✅ Türkontakte

#### Sensor Platform

- ✅ Temperatur
- ✅ Helligkeit (Lux)
- ✅ Windgeschwindigkeit
- ✅ Auto-Discovery von DPT 9.xxx Sensoren

---

## 📊 Getestete Projekte

### Hauptwohnung.lxp (Referenz-Projekt)

**Statistik:**

- 63 Geräte
- 851 Datapoints
- 137 Home Assistant Entities

**Geräteverteilung:** | Typ | Anzahl | HA Entities | |
--------------------------- | ------ | ---------------- | | Schaltaktoren
(S4/S8/S16) | 3 | 24 Lights | | Dimmaktoren (D2/D4) | 10 | 19 Lights | |
Jalousieaktoren (J4/J8) | 2 | 15 Covers | | Heizungsaktoren (H6) | 2 | 9 Climate
| | Taster (iON8, E1, etc.) | 30+ | 60+ Switches | | Bewegungsmelder (BI180/360)
| 4 | 4 Binary Sensors | | Wetterstation | 1 | 5 Sensors |

---

## ⚠️ Bekannte Einschränkungen

### KNX-spezifisch

1. **Farbsteuerung nicht möglich**
   - KNX-Geräte unterstützen nur Ein/Aus und Dimmen
   - Keine RGB/RGBW-Steuerung

2. **Auto-Modus bei Heizung**
   - H6 unterstützt nur Heat/Off
   - Auto-Regelung muss in ETS konfiguriert werden

3. **Gruppenadresse-Limitierungen**
   - Maximale Anzahl pro Gerät: Abhängig vom Modell
   - Komplexe Szenarien erfordern ETS-Konfiguration

### Integration-spezifisch

1. **LXP-Datei erforderlich**
   - Auto-Discovery nur für zusätzliche Sensoren (DPT 9.xxx)
   - Hauptkonfiguration via LXP Upload

2. **Polling-basierte Updates**
   - State-Updates via KNX Telegrams (Echtzeit)
   - Coordinator Polling als Fallback (konfigurierbar)

3. **REST API Authentifizierung**
   - HTTPS empfohlen (selbstsignierte Zertifikate werden akzeptiert)
   - TLS 1.2+ erforderlich

---

## 🆕 Geräte hinzufügen

### Neue Geräte testen

Wenn Sie ein Gerät haben, das nicht in dieser Liste steht:

1. **LXP-Datei exportieren** (aus LUXORPlug)
2. **Integration einrichten** mit Ihrer LXP-Datei
3. **Funktionalität testen**
4. **Feedback geben:**
   - [GitHub Issue erstellen](https://github.com/phismith91/luxorliving/issues/new)
   - Gerätetyp angeben
   - LXP-Datei anhängen (sensitive Daten entfernen!)
   - Screenshots der Entities

---

## 📝 Kompatibilitäts-Matrix

### Nach Device Type

| Device Type       | Light | Switch | Cover | Climate | Binary Sensor | Sensor    |
| ----------------- | ----- | ------ | ----- | ------- | ------------- | --------- |
| **S4/S8/S16**     | ✅    | ✅     | ❌    | ❌      | ❌            | ❌        |
| **D2/D4**         | ✅    | ❌     | ❌    | ❌      | ❌            | ❌        |
| **J4/J8**         | ❌    | ❌     | ✅    | ❌      | ❌            | ❌        |
| **H6**            | ❌    | ❌     | ❌    | ✅      | ❌            | ❌        |
| **iON8**          | ❌    | ✅     | ❌    | ❌      | ❌            | ✅ (Temp) |
| **BI180/360**     | ❌    | ❌     | ❌    | ❌      | ✅            | ✅ (Temp) |
| **Wetterstation** | ❌    | ❌     | ❌    | ❌      | ❌            | ✅        |
| **Binäreingang**  | ❌    | ❌     | ❌    | ❌      | ✅            | ❌        |

---

## 🔗 Weiterführende Links

- **Theben Produkte:** https://www.theben.de/
- **LUXORplug Software:** https://www.theben.de/de/service/software-und-apps
- **KNX Association:** https://www.knx.org/
- **ETS Software:** https://www.knx.org/knx-en/for-professionals/software/ets/

---

**Gerät fehlt oder funktioniert nicht?** →
[Issue erstellen](https://github.com/phismith91/luxorliving/issues/new)
