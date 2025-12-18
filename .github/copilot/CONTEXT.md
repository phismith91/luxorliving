# Copilot Context – luxor_living

This repository implements a Home Assistant integration for
Theben LUXORliving IP1 based on KNX/IP.

The integration:

* Does NOT use ETS or .knxproj files
* Uses LUXORliving project exports (.lxp, XML)
* Supports automatic entity mapping
* Supports simulation / dry-run mode
* Is currently HACS-only

## Core Concepts

* KNX/IP communication is abstracted
* LUXORliving-specific logic is isolated
* .lxp project files are optional but preferred
* Entity creation is deterministic and role-based

## Copilot Usage Rules

* Copilot agents are located in `.github/copilot/`
* Agents define *how* code should be generated
* This file defines *when* agents should be used

## Agent Selection Guide

Use the following agents depending on the task:

### Architecture & Structure

Use:

* `agent_architect.md`

When:

* Creating new modules
* Refactoring structure
* Making high-level decisions

---

### LXP Project Import

Use:

* `agent_lxp_import.md`

When:

* Working with `.lxp` XML files
* Parsing devices, sensors, datapoints
* Handling LuxorPlug versions

---

### Luxor → Home Assistant Mapping

Use:

* `agent_mapping.md`

When:

* Creating Home Assistant entities
* Mapping datapoint roles to HA platforms
* Naming and grouping entities

---

### Config Flow & UX

Use:

* `agent_config_flow.md`

When:

* Implementing `config_flow.py`
* Handling file upload
* Improving onboarding UX

---

### Simulation & Testing

Use:

* `agent_testing.md`

When:

* Working on dry-run mode
* Adding tests
* Debugging without KNX hardware

## Language Policy

* Agents and context files: English
* User chat messages: German or English
* Generated code: English only

---

This file provides guidance for GitHub Copilot and contributors.
It has no runtime impact.
