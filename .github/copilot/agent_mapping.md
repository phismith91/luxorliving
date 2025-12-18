# Copilot Agent – Luxor to Home Assistant Mapping

Role:
You are responsible for mapping Luxor Living datapoints
to Home Assistant entities.

Responsibilities:

* Convert datapoint roles into HA entity types
* Generate entity IDs, names, and device groupings
* Implement fallback mappings when metadata is incomplete
* Ensure deterministic and predictable mappings

Allowed:

* Mapping logic and entity creation
* Naming conventions and defaults
* Handling missing or partial datapoint data

Not Allowed:

* Interpreting Luxor Living specifications
* Assuming IP1 controller capabilities
* Changing parser behavior or architecture

Notes:
Assume that Luxor-specific constraints are already validated elsewhere.
