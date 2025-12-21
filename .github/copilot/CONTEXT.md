# Copilot Context – luxor_living

This repository contains a Home Assistant integration for
**Theben LUXORliving IP1**, based on **KNX/IP**.

The integration is designed to be:

* HACS-ready
* Community-friendly
* Maintainable long-term
* Independent of ETS or `.knxproj` files

Instead of ETS, it optionally uses **LUXORliving project exports (`.lxp`, XML)**
to automatically discover and map devices.

---

## Core Principles

* No ETS dependency
* KNX/IP via LUXORliving IP1 (Weinzierl-based)
* `.lxp` project files are optional but preferred
* Deterministic auto-mapping based on datapoint roles
* Simulation / Dry-Run mode is a first-class feature
* HACS-first, but written close to Home Assistant Core standards

---

## High-Level Architecture

* KNX/IP communication is abstracted
* Luxor Living specifics are isolated from HA logic
* `.lxp` parsing is independent from Home Assistant code
* Mapping logic is role-based and predictable
* Fallback behavior exists when no project file is available
* Simulation mode must never affect production behavior

---

## Production Environment Architecture

**Physical Setup:**
```
Developer PC (Local)
  ↓ Git Push/Pull
GitHub/GitLab Repository
  ↓ Manual Download via HA UI
Proxmox Server (Madeira, Portugal)
  └── Home Assistant OS VM
       ├── Tailscale VPN (Remote Access)
       ├── Custom Components: /config/custom_components/luxor_living
       └── Local Network: 192.168.1.x
            └── LUXORliving IP1 Gateway: 192.168.1.3
                 ├── KNX/IP Port: 3671
                 ├── Web UI: Port 80/443
                 └── Supports: Tunneling + Routing
```

**Network Considerations:**
* Remote access via **Tailscale VPN** for UI control
* KNX Multicast (224.0.23.12) may **not** work over VPN
* **KNX Tunneling** (direct to 192.168.1.3:3671) recommended for remote setups
* HA VM and Gateway are in **same local network** → both modes work

**Deployment Workflow:**
1. Develop & test locally on developer PC
2. Commit & push to Git repository
3. Download via HA UI: **Einstellungen → Add-ons → HACS → LUXORliving**
4. Integration auto-updates in `/config/custom_components/luxor_living`
5. Restart HA Core to apply changes
6. Configure via HA UI (no SSH access needed)

**Testing Environment:**
* **Local:** pytest with mocks & simulation mode
* **Production:** Real hardware testing on Proxmox VM
* **Access:** UI-only via Tailscale (no direct SSH to HA OS)

**Important Constraints:**
* HA OS = **appliance mode** (limited shell access)
* Deployment via **UI only** (HACS or File Upload)
* Configuration changes via **HA UI or File Editor add-on**
* Logs accessible via **Settings → System → Logs**

---

## Language & Usage Rules

* Copilot agent definitions are written in **English**
* User prompts may be **German or English**
* All generated code, identifiers, comments, and documentation must be **English**
* Agents define *how* Copilot should behave
* This file defines *when* each agent must be used

---

## Agent Interaction Rules (IMPORTANT)

* Only **agent_architect** may make architectural or structural decisions
* Luxor/KNX domain assumptions come exclusively from **agent_luxor_expert**
* Parsing, mapping, UX, compliance, and quality concerns are strictly separated
* Review agents must not introduce new features or redesigns

### Conflict Resolution Order

If agents provide conflicting advice, resolve it in this order:

1. agent_architect
2. agent_luxor_expert
3. Functional agent (parser / mapping / config flow / testing)
4. Review agents (HACS / Quality Auditor)

---

## Agent Usage Guide

### 🧠 Architecture & Structure

**Agent:** `agent_architect.md`

Use when:

* Designing or refactoring overall architecture
* Defining module boundaries and data flow
* Introducing or restructuring subsystems
* Resolving conflicts between agent recommendations

---

### 🔌 Luxor Living & IP1 Domain Knowledge

**Agent:** `agent_luxor_expert.md`

Use when:

* Working with Luxor Living–specific behavior
* Handling differences between standard KNX and Luxor proprietary KNX
* Evaluating IP1 controller capabilities or limitations
* Assessing feasibility or constraints

---

### 📂 LXP Project Import

**Agent:** `agent_lxp_import.md`

Use when:

* Parsing `.lxp` (LuxorPlug XML) project files
* Handling namespaces, versions, and schema changes
* Extracting devices, channels, sensors, actuators, and datapoints
* Improving robustness of project import

---

### 🔁 Luxor → Home Assistant Mapping

**Agent:** `agent_mapping.md`

Use when:

* Creating Home Assistant entities
* Mapping Luxor datapoint roles to HA platforms
* Generating entity IDs, names, and device groupings
* Implementing fallback mappings

---

### 🔄 Config Flow & User Experience

**Agent:** `agent_config_flow.md`

Use when:

* Implementing or refining `config_flow.py`
* Designing onboarding flows
* Handling `.lxp` file uploads
* Improving error handling and user guidance
* Supporting simulation / dry-run setup

---

### 🧪 Simulation, Testing & Diagnostics

**Agent:** `agent_testing.md`

Use when:

* Implementing simulation or dry-run mode
* Writing or improving tests
* Debugging without physical KNX hardware
* Enhancing logging and diagnostics

---

### 📦 HACS & Home Assistant Compliance

**Agent:** `agent_hacs.md`

Use when:

* Preparing releases
* Reviewing `manifest.json` and `hacs.json`
* Ensuring README meets HACS requirements
* Checking versioning and metadata

---

### ✅ Quality & Community Review

**Agent:** `agent_quality_auditor.md`

Use when:

* Reviewing code readability and maintainability
* Improving documentation clarity
* Preparing pull requests for community review
* Evaluating long-term project health

---

### ✅ ### ✅ Quality & Community Review

**Agent:** `agent_ssl.md`

Use when:

* Advising on secure HTTP/HTTPS connections to the IP1 controller
* Validating certificate handling (self-signed vs CA-signed)
* Ensuring TLS configuration follows best practices
* Providing guidance for certificate imports or verification issues
* Warning about potential security pitfalls in remote connections


---


## Notes for Contributors

* This integration intentionally avoids ETS-based workflows
* `.lxp` files are the primary source for automation metadata
* Simulation mode must always remain functional
* Simplicity and clarity are prioritized over feature completeness
* Community expectations and maintainability matter as much as functionality

---

This file provides **context and behavioral guidance** for GitHub Copilot
and contributors. It has **no runtime impact** on the integration.
