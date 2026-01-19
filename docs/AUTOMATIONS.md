# Automation Examples – LUXORliving

Practical, copy-ready Home Assistant automations for the LUXORliving
integration.

Note: Replace entity IDs and notify services with your own setup (e.g.,
`light.front_entry`, `cover.bedroom`, `notify.mobile_app_your_device`). Avoid
`entity_id: all` unless you intentionally want to affect every entity in the
domain.

## Contents

- Lighting automations
- Cover control
- Heating automations
- Motion sensors
- Scenes & scripts
- Notes and tips

---

## Lighting automations

### Switch exterior lights at sunset

```yaml
automation:
  - alias: "Exterior lights at dusk"
    description: "Turn on exterior lights 30 minutes before sunset"
    trigger:
      - platform: sun
        event: sunset
        offset: "-00:30:00"
    action:
      - service: light.turn_on
        target:
          entity_id:
            - light.front_entry
            - light.side_lights
        data:
          brightness_pct: 80
```

### Night light with dimming

```yaml
automation:
  - alias: "Hall night light"
    description: "Dim hallway light to 10% at night"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.hallway_stairs
        data:
          brightness_pct: 10
          transition: 5
```

### Wake-up light (gradual)

```yaml
automation:
  - alias: "Wake-up light bedroom"
    description: "Gradually increase bedside lights as an alarm"
    trigger:
      - platform: time
        at: "06:30:00"
    condition:
      - condition: state
        entity_id: binary_sensor.workday
        state: "on"
    action:
      - service: light.turn_on
        target:
          entity_id:
            - light.bed_right
            - light.bed_left
        data:
          brightness_pct: 1
      - delay: "00:00:05"
      - repeat:
          count: 20
          sequence:
            - service: light.turn_on
              target:
                entity_id:
                  - light.bed_right
                  - light.bed_left
              data:
                brightness_step_pct: 5
            - delay: "00:01:00"
```

### Turn lights off when nobody is home

Option A – Zone trigger per person + template condition:

```yaml
automation:
  - alias: "Turn off lights when everyone leaves"
    trigger:
      - platform: zone
        entity_id: person.john
        zone: zone.home
        event: leave
      - platform: zone
        entity_id: person.jane
        zone: zone.home
        event: leave
    condition:
      - condition: template
        value_template: >-
          {{ not states.person | selectattr('state','eq','home') | list }}
    action:
      - service: light.turn_off
        target:
          entity_id:
            - light.living_room
            - light.dining_table
            - light.kitchen_island
      - service: notify.mobile_app_your_device
        data:
          message: "All lights were turned off"
```

Option B – Use a people group created in the UI (example `group.household`):

```yaml
automation:
  - alias: "Turn off lights when household leaves"
    trigger:
      - platform: state
        entity_id: group.household
        from: "home"
        to: "not_home"
        for: "00:05:00"
    action:
      - service: light.turn_off
        target:
          entity_id:
            - light.living_room
            - light.dining_table
            - light.kitchen_island
```

Note: Prefer explicit lists, areas, or groups instead of `entity_id: all` for
safer control.

---

## Cover control

### Open bedroom covers at sunrise

```yaml
automation:
  - alias: "Morning sun covers"
    trigger:
      - platform: sun
        event: sunrise
        offset: "00:15:00"
    condition:
      - condition: state
        entity_id: binary_sensor.workday
        state: "on"
    action:
      - service: cover.open_cover
        target:
          entity_id:
            - cover.bedroom
            - cover.wardrobe
```

### Heat protection – close south-facing covers

```yaml
automation:
  - alias: "Sun protection when hot"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 28
    condition:
      - condition: sun
        after: sunrise
        before: sunset
      - condition: numeric_state
        entity_id: sensor.outdoor_illuminance
        above: 30000
    action:
      - service: cover.close_cover
        target:
          entity_id:
            - cover.dining_south
            - cover.living_balcony
      - service: cover.set_cover_tilt_position
        target:
          entity_id:
            - cover.dining_south
            - cover.living_balcony
        data:
          tilt_position: 30
```

### Storm protection – raise selected covers on strong wind

```yaml
automation:
  - alias: "Raise covers during storm"
    trigger:
      - platform: numeric_state
        entity_id: sensor.wind_speed
        above: 50
    action:
      - service: cover.open_cover
        target:
          entity_id:
            - cover.living_balcony
            - cover.dining_south
            - cover.bedroom
      - service: notify.mobile_app_your_device
        data:
          title: "Weather protection"
          message: "Storm detected: covers raised"
```

### Evening privacy – close covers after sunset

```yaml
automation:
  - alias: "Close covers in the evening"
    trigger:
      - platform: sun
        event: sunset
        offset: "00:30:00"
    action:
      - service: cover.close_cover
        target:
          entity_id:
            - cover.living_balcony
            - cover.dining_south
            - cover.bedroom
            - cover.bathroom
      - service: cover.set_cover_tilt_position
        target:
          entity_id:
            - cover.living_balcony
            - cover.dining_south
        data:
          tilt_position: 0
```

---

## Heating automations

### Night setback

```yaml
automation:
  - alias: "Heating night setback"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id:
            - climate.bedroom
            - climate.living_room
        data:
          temperature: 18
```

### Morning comfort

```yaml
automation:
  - alias: "Heating wake-up"
    trigger:
      - platform: time
        at: "06:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.workday
        state: "on"
    action:
      - service: climate.set_temperature
        target:
          entity_id:
            - climate.bedroom
            - climate.bathroom
        data:
          temperature: 22
```

### Window contact cut-off

```yaml
automation:
  - alias: "Turn heating off if window open"
    trigger:
      - platform: state
        entity_id: binary_sensor.window_contact_bedroom
        to: "on"
        for: "00:05:00"
    action:
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.bedroom
        data:
          hvac_mode: "off"
      - service: notify.mobile_app_your_device
        data:
          message: "Bedroom heating disabled due to open window"
```

---

## Motion sensors

### Hallway light on motion, off after inactivity

```yaml
automation:
  - alias: "Hallway light on motion"
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_hall
        to: "on"
    condition:
      - condition: numeric_state
        entity_id: sensor.outdoor_illuminance
        below: 500
    action:
      - service: light.turn_on
        target:
          entity_id: light.hallway
        data:
          brightness_pct: 60
      - wait_for_trigger:
          - platform: state
            entity_id: binary_sensor.motion_hall
            to: "off"
            for: "00:02:00"
        timeout: "00:10:00"
      - service: light.turn_off
        target:
          entity_id: light.hallway
```

### Exterior security lighting at night

```yaml
automation:
  - alias: "Exterior motion lighting at night"
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_front
        to: "on"
    condition:
      - condition: time
        after: "22:00:00"
        before: "06:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.front_entry
        data:
          brightness_pct: 100
      - service: notify.mobile_app_your_device
        data:
          message: "Motion detected at front entrance"
      - delay: "00:05:00"
      - service: light.turn_off
        target:
          entity_id: light.front_entry
```

---

## Scenes & scripts (with services)

Scenes define states; for reliable cover/heating control prefer service-based
automations.

### "Home theater"

```yaml
scene:
  - name: "Home theater"
    entities:
      light.living_room:
        state: off
      light.dining_table:
        state: on
        brightness: 10
      cover.living_balcony:
        state: closed
      cover.living_window:
        state: closed
```

Activate scene on media start:

```yaml
automation:
  - alias: "Activate theater scene on playback"
    trigger:
      - platform: state
        entity_id: media_player.living_room_tv
        to: "playing"
    condition:
      - condition: sun
        after: sunset
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.home_theater
```

### "Good morning"

```yaml
scene:
  - name: "Good morning"
    entities:
      cover.living_balcony:
        state: open
      cover.dining_south:
        state: open
      cover.bedroom:
        state: open
      light.kitchen_island:
        state: on
        brightness: 70
```

### "Good night" as a script

```yaml
script:
  good_night:
    alias: "Good night"
    sequence:
      - service: light.turn_off
        target:
          entity_id:
            - light.living_room
            - light.dining_table
            - light.kitchen_island
      - service: cover.close_cover
        target:
          entity_id:
            - cover.living_balcony
            - cover.dining_south
      - service: climate.set_temperature
        target:
          entity_id:
            - climate.living_room
            - climate.bedroom
        data:
          temperature: 18
```

---

## Notes and tips

- Notifications: Replace `notify.mobile_app_your_device` with your specific
  notify service (check `services` in the Developer Tools).
- Presence: Prefer zone triggers and template conditions, or use a people group
  (`group.household`) for simpler automations.
- Avoid `entity_id: all`: Prefer explicit lists, areas, or groups for safer
  control.
- Traces: Use Home Assistant’s Trace to debug failing automations.
- Conditions: Add conditions to avoid unwanted triggers (e.g., only at night).
- Delays: Use short delays to avoid flicker with motion sensors.
- Blueprints: Community blueprints are a great starting point.

Further reading: https://www.home-assistant.io/docs/automation/
