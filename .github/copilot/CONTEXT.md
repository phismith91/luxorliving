# Copilot Context – luxor_living

This repository implements a Home Assistant integration for
**Theben LUXORliving IP1**, based on **KNX/IP**.

The project is designed to be:

* HACS-ready
* Community-friendly
* Maintainable long-term
* Independent of ETS or `.knxproj` files

Instead, it relies on **LUXORliving project exports (`.lxp`, XML)** for
automatic device and entity mapping.

---

## Core Principles

* **No ETS dependency**
* **KNX/IP only**, via LUXORliving IP1 (Weinzierl-based)
* **`.lxp` project files are optional but preferred**
* **Auto-mapping based on datapoint roles**
* **Simulation / Dry-Run mode is a first-class feature**
* HACS-first, but written close to HA Core standards

---

## Architecture Overview

* KNX/IP communication is abstracted
* LUXORliving-specific behavior is isolated
* `.lxp` parsing is independent of Home Assistant code
* Entity mapping is deterministic and role-based
* Fallback logic exists when no project file is provided

---

## Copilot Usage Rules

* Copilot agents are located in `.github/copilot/`
* Agents define **how** code should be generated
* This file defines **when** agents should be used
* Agents are written in **English**
* User messages may be in **German or English**
* All generated code, identifiers, and comments must be in **English**

---

## Agent Selection Guide

Use the following agents depending on the task you are working on.

---

### 🧠 Architecture & Structure

**Agent:** `agent_architect.md`

Use when:

* Creating or refactoring module structure
* Making high-level architectural decisions
* Introducing new subsystems (simulation, parsing, mapping)

---

### 🔌 Luxor Living / IP1 Domain Knowledge

**Agent:** `agent_luxor_expert.md`

Use when:

* Working with Luxor Living–specific behavior
* Handling differences between standard KNX and Luxor KNX
* Making assumptions about IP1 capabilities or limitations
* Evaluating feasibility of features

---

### 📂 LXP Project Import

**Agent:** `agent_lxp_import.md`

Use when:

* Parsing `.lxp` XML project files
* Handling devices, sensors, and datapoints
* Working with LuxorPlug namespaces or versions
* Improving robustness of project imports

---

### 🔁 Luxor → Home Assistant Mapping

**Agent:** `agent_mapping.md`

Use when:

* Creating Home Assistant entities
* Mapping Luxor datapoint roles to HA platforms
* Generating entity IDs, names, and devices
* Implementing fallback mappings

---

### 🔄 Config Flow & User Experience

**Agent:** `agent_config_flow.md`

Use when:

* Implementing `config_flow.py`
* Handling `.lxp` file uploads
* Improving onboarding for non-KNX users
* Validating IP1 connectivity

---

### 🧪 Simulation, Testing & Debugging

**Agent:** `agent_testing.md`

Use when:

* Working on simulation / dry-run mode
* Adding tests
* Debugging without real KNX hardware
* Improving logging and diagnostics

---

### 📦 HACS & Home Assistant Compliance

**Agent:** `agent_hacs.md`

Use when:

* Preparing releases
* Editing `manifest.json`, `hacs.json`
* Writing or reviewing README files
* Ensuring HACS and HA guideline compliance

---

### ✅ Quality & Community Review

**Agent:** `agent_quality_auditor.md`

Use when:

* Reviewing code quality and readability
* Preparing PRs for community review
* Improving documentation clarity
* Ensuring maintainability and positive community perception

---

## Notes for Contributors

* This integration intentionally avoids ETS-based workflows
* `.lxp` files are the primary source for automation metadata
* Simulation mode should always remain functional
* Clarity and maintainability are prioritized over feature completeness

---

This file provides **context and guidance** for GitHub Copilot and contributors.
It has **no runtime impact** on the integration.
