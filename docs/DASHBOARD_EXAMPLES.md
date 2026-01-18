# Dashboard Examples – LUXORliving

Examples for building useful Lovelace dashboards with the LUXORliving integration.

Note: Replace entity names with your setup. Examples use typical IDs (e.g., `light.living_room_ceiling`, `cover.living_room_balcony`). For climate attributes displayed as standalone rows, create template sensors first and reference those sensors.

## Contents

- Core cards
- Room dashboards
- Energy management
- Custom cards (HACS)
- Mobile layout
- Best practices

---

## Core cards

### Entities card – lights

```yaml
type: entities
title: Lighting – Living Area
show_header_toggle: true
entities:
  - entity: light.living_room_ceiling
    name: Living room
  - entity: light.dining_table
    name: Dining table
  - entity: light.kitchen_island
    name: Kitchen island
```

### Glance card – quick overview

```yaml
type: glance
title: Quick overview
entities:
  - entity: light.living_room_ceiling
    name: Lights
  - entity: cover.living_room_balcony
    name: Balcony blind
  - entity: climate.living_room
    name: Heating
  - entity: sensor.outdoor_temperature
    name: Outdoor
```

### Light card – brightness slider

```yaml
type: light
entity: light.kitchen_island
name: Kitchen island
```

### Cover card – position and tilt

```yaml
type: cover
entity: cover.living_room_balcony
name: Balcony
```

---

## Room dashboards

### Living room

```yaml
type: vertical-stack
cards:
  # Lights
  - type: entities
    title: 💡 Lighting
    entities:
      - entity: light.living_room_ceiling
        name: Ceiling
      - entity: light.floor_lamp
        name: Floor lamp

  # Covers
  - type: entities
    title: 🪟 Blinds
    entities:
      - entity: cover.living_room_balcony
        name: Balcony
      - entity: cover.living_room_window
        name: Window
    # Tip: For tilt or additional attributes, expose template sensors and list those here.

  # Climate
  - type: thermostat
    entity: climate.living_room
    name: Floor heating

  # Weather snapshot
  - type: horizontal-stack
    cards:
      - type: sensor
        entity: sensor.outdoor_temperature
        name: Outdoor temperature
      - type: sensor
        entity: sensor.outdoor_illuminance
        name: Outdoor illuminance
```

### Bedroom

```yaml
type: vertical-stack
cards:
  # Scene buttons
  - type: horizontal-stack
    cards:
      - type: button
        name: Good morning
        icon: mdi:weather-sunset-up
        tap_action:
          action: call-service
          service: scene.turn_on
          target:
            entity_id: scene.good_morning
      - type: button
        name: Good night
        icon: mdi:weather-night
        tap_action:
          action: call-service
          service: scene.turn_on
          target:
            entity_id: scene.good_night

  # Bed lights
  - type: entities
    title: Bed lighting
    entities:
      - entity: light.bed_right
        name: Right
      - entity: light.bed_left
        name: Left
      - entity: light.bedroom_ceiling
        name: Ceiling

  # Cover
  - type: cover
    entity: cover.bedroom
    name: Bedroom blind

  # Climate
  - type: thermostat
    entity: climate.bedroom
```

### Kitchen

```yaml
type: grid
columns: 2
cards:
  # Lights
  - type: light
    entity: light.kitchen_island
    name: Island
  - type: light
    entity: light.kitchen_niche
    name: Niche

  # Covers
  - type: cover
    entity: cover.kitchen_terrace
    name: Terrace
  - type: cover
    entity: cover.kitchen_north
    name: North

  # Climate
  - type: thermostat
    entity: climate.kitchen
    column_span: 2
```

---

## Energy management

Tip: To display climate attributes (e.g., `current_temperature`, `valve_position`) in entities cards, create template sensors and reference those sensors.

### Heating overview

```yaml
type: vertical-stack
cards:
  # Room temperatures (template sensors)
  - type: entities
    title: 🌡️ Room temperatures
    entities:
      - entity: sensor.living_room_current_temperature
        name: Living room
      - entity: sensor.bedroom_current_temperature
        name: Bedroom
      - entity: sensor.kitchen_current_temperature
        name: Kitchen

  # Targets
  - type: entities
    title: 🎯 Target temperatures
    entities:
      - entity: climate.living_room
        name: Living room
      - entity: climate.bedroom
        name: Bedroom
      - entity: climate.kitchen
        name: Kitchen

  # Valve positions (template sensors)
  - type: entities
    title: 📊 Valve positions
    entities:
      - entity: sensor.living_room_valve_position
        name: Living room
      - entity: sensor.bedroom_valve_position
        name: Bedroom

  # Thermostat view
  - type: thermostat
    entity: climate.bedroom
```

---

## Push Webhook Example Automation (Practical Example)

```yaml
alias: 'Forward LUXOR push to notification'
description: 'Example automation that reacts to push webhook and sends a notification.'
trigger:
  - platform: event
    event_type: luxor_living_push
    event_data:
      entry_id: 'entry_1'

condition: []

action:
  - service: notify.mobile_app_phil
    data:
      title: 'LUXOR Push'
      message: "Address {{ trigger.event.data.address }} changed to {{ trigger.event.data.value }}"
mode: single
```

This automation demonstrates how external pushes can be used to trigger user-facing actions; adapt the service and message to your environment.

---

## Custom cards (HACS)

Install via HACS → Frontend.

### Mushroom cards – modern design

Repo: https://github.com/piitaya/lovelace-mushroom

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-light-card
    entity: light.living_room_ceiling
    name: Living room
    use_light_color: true
    show_brightness_control: true

  - type: custom:mushroom-cover-card
    entity: cover.living_room_balcony
    name: Balcony blind
    show_position_control: true
    show_tilt_position_control: true

  - type: custom:mushroom-climate-card
    entity: climate.living_room
    name: Heating
    show_temperature_control: true
    hvac_modes:
      - heat
      - "off"
```

### Button Card – flexible layout

Repo: https://github.com/custom-cards/button-card

```yaml
type: custom:button-card
entity: light.living_room_ceiling
name: Living room
icon: mdi:sofa
show_state: true
show_name: true
styles:
  card:
    - height: 100px
  icon:
    - color: |
        [[[
          return entity.state === 'on'
            ? 'var(--paper-item-icon-active-color)'
            : 'var(--paper-item-icon-color)';
        ]]]
tap_action:
  action: toggle
hold_action:
  action: more-info
```

### Mini Graph Card – temperature history

Repo: https://github.com/kalkih/mini-graph-card

```yaml
type: custom:mini-graph-card
entities:
  - entity: sensor.living_room_current_temperature
    name: Living room (current)
  - entity: climate.living_room
    name: Living room (target)
    attribute: temperature
  - entity: sensor.outdoor_temperature
    name: Outdoor
hours_to_show: 24
points_per_hour: 4
line_width: 2
font_size: 75
animate: true
show:
  labels: true
  legend: true
```

### Layout Card – responsive grid

Repo: https://github.com/thomasloven/lovelace-layout-card

```yaml
type: custom:layout-card
layout_type: grid
layout:
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))
  grid-gap: 8px
cards:
  - type: light
    entity: light.living_room_ceiling
  - type: light
    entity: light.kitchen_island
  - type: cover
    entity: cover.living_room_balcony
  - type: thermostat
    entity: climate.living_room
```

---

## Mobile layout

### Compact mobile stack

```yaml
type: vertical-stack
cards:
  # Quick access
  - type: horizontal-stack
    cards:
      - type: button
        name: Morning
        icon: mdi:weather-sunset-up
        tap_action:
          action: call-service
          service: scene.turn_on
          target:
            entity_id: scene.good_morning
      - type: button
        name: Cinema
        icon: mdi:movie
        tap_action:
          action: call-service
          service: scene.turn_on
          target:
            entity_id: scene.cinema
      - type: button
        name: Night
        icon: mdi:weather-night
        tap_action:
          action: call-service
          service: scene.turn_on
          target:
            entity_id: scene.good_night

  # Key lights
  - type: entities
    title: Lighting
    show_header_toggle: true
    entities:
      - light.living_room_ceiling
      - light.kitchen_island
      - light.outdoor_entry

  # Blinds
  - type: entities
    title: Blinds
    entities:
      - cover.living_room_balcony
      - cover.dining_south
      - cover.bedroom
```

---

## Best practices

1. Mobile first: test layouts on phones.
2. Group related entities together.
3. Use clear icons from Material Design Icons.
4. Conditional cards: show cards only when relevant.
5. Badges: use badges for critical status info.

Further reading: https://www.home-assistant.io/lovelace/
