"""Entity mapper for LUXORliving integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.const import Platform
from xknx.telegram.address import GroupAddress

from .const import DOMAIN
from .knxprod_reader import DEVICE_CATEGORIES
from .lxp_parser import LXPActuator, LXPDevice, LXPProject, LXPSensor
from .mapped_entity import MappedEntity
from .override_handler import OverrideHandler
from .platform_detector import PlatformDetector

_LOGGER = logging.getLogger(__name__)


class EntityMapper:
    """Maps LXP devices to Home Assistant entities.

    Uses dependency injection to delegate platform detection and override handling
    to specialized modules:
    - PlatformDetector: Determines HA platform from KNX role
    - OverrideHandler: Applies user-defined sensor overrides

    This design reduces EntityMapper from 523 to ~250 LOC by removing duplicate logic.
    """

    def __init__(
        self,
        project: LXPProject,
        overrides: dict[str, Any] | None = None,
        platform_detector: PlatformDetector | None = None,
        override_handler: OverrideHandler | None = None,
    ) -> None:
        """Initialize the mapper with optional dependency injection.

        Args:
            project: LXP project to map
            overrides: Override configuration dict
            platform_detector: Custom platform detector (default: new instance)
            override_handler: Custom override handler (default: new instance)
        """
        self.project = project
        self.entities: list[MappedEntity] = []
        self._overrides = overrides or {}

        # Dependency injection - use provided instances or create defaults
        self.platform_detector = platform_detector or PlatformDetector()
        self.override_handler = override_handler or OverrideHandler(self._overrides)

        # Track (device_id, istwert_addr) already mapped for H6 actuators.
        # Prevents duplicate climate entities when two channels within the SAME H6 device
        # share a KNX Istwert address (both wired to one room sensor).
        # Intentionally per-device: R718 thermostats and iON RTR sensors are separate
        # physical units and must each produce their own climate entity even when they
        # share Istwert addresses with an H6 actuator in the same heating zone.
        self._h6_claimed_zones: set[tuple[str, int]] = set()

        # Automatically map all entities on init
        self.map_all()

    def map_all(self) -> list[MappedEntity]:
        """Map all devices to entities."""
        if self._overrides.get("map_onoff_to_binary") is not None:
            _LOGGER.warning(
                "Override key 'map_onoff_to_binary' is no longer needed and will be ignored. "
                "All sensor OnOff channels now always map to binary_sensor. "
                "Remove this key from your luxor_living_overrides.yaml."
            )
        _LOGGER.info("Mapping %d devices to entities", len(self.project.devices))

        for device in self.project.devices:
            self._map_device(device)

        self._deduplicate_unique_ids()

        # Apply overrides via dependency injection
        try:
            self.override_handler.apply_overrides(self.entities)
        except Exception as err:
            _LOGGER.error("Failed applying overrides: %s", err)

        # Add health monitoring entity
        health_entity = MappedEntity(
            platform=Platform.BINARY_SENSOR,
            unique_id=f"{DOMAIN}_health",
            name="System Health",
            device_name="LUXORliving",
            device_id=f"{DOMAIN}_system",
            entity_type="health",
            datapoints={},
            attributes={},
            parameters={},
        )
        self.entities.append(health_entity)

        _LOGGER.info("Mapped %d entities total", len(self.entities))
        return self.entities

    def _deduplicate_unique_ids(self) -> None:
        """Disambiguate same-platform unique_id collisions.

        HA's entity registry is keyed on (platform, unique_id) — when two
        entities of the same platform collide, HA silently drops the second
        one. Address-based IDs can collide when two channels share a group
        address (e.g. two actuator channels wired to the same switch GA).

        The first claimant keeps its ID so existing registries stay intact;
        later entities get a channel suffix. Cross-platform duplicates are
        HA-legal and left untouched for the same reason.
        """
        seen: set[tuple[Platform, str]] = set()
        collisions = 0
        for entity in self.entities:
            key = (entity.platform, entity.unique_id)
            if key not in seen:
                seen.add(key)
                continue
            base = entity.unique_id
            channel = entity.attributes.get("channel")
            candidate = f"{base}_ch{channel}" if channel is not None else f"{base}_2"
            counter = 2
            while (entity.platform, candidate) in seen:
                counter += 1
                candidate = f"{base}_{counter}"
            # Expected for multi-channel devices (e.g. climate controllers expose
            # several channels under one device_id) — disambiguation is the normal
            # path, so log per-collision detail at DEBUG and summarise once below.
            _LOGGER.debug(
                "unique_id collision on %s '%s' (%s) — renamed to %s",
                entity.platform,
                entity.name,
                base,
                candidate,
            )
            entity.unique_id = candidate
            seen.add((entity.platform, candidate))
            collisions += 1

        if collisions:
            _LOGGER.info(
                "Disambiguated %d unique_id collision(s) via channel suffixes",
                collisions,
            )

    def _map_device(self, device: LXPDevice) -> None:
        """Map a single device to entities."""
        # Wetterstation is identified by name (matches lxp_parser._is_weather_station_device)
        # and handled entirely in _map_sensor; bypass the appId-based category check
        # so it is never silently skipped. The device shares appId 18585 with M140.
        name_lower = device.name.lower()
        is_weather_station = "wetterstation" in name_lower or "weather station" in name_lower

        if not is_weather_station:
            category = DEVICE_CATEGORIES.get(device.device_type)
            if category == "input_only":
                _LOGGER.debug(
                    "Skipping input-only device '%s' (%s)", device.name, device.device_type
                )
                return
            if category == "unsupported":
                _LOGGER.info(
                    "Device '%s' (%s) is not yet supported — no entities created",
                    device.name,
                    device.device_type,
                )
                return

        # Map actuators (lights, switches, covers)
        for actuator in device.actuators:
            self._map_actuator(device, actuator)

        # Map sensors (binary sensors)
        for sensor in device.sensors:
            self._map_sensor(device, sensor)

    def _map_actuator(self, device: LXPDevice, actuator: LXPActuator) -> None:
        """Map an actuator to entities."""
        # Collect datapoints by role
        datapoints = {dp.role: dp.address for dp in actuator.datapoints}

        # Debug: Log extracted datapoints
        if datapoints:
            _LOGGER.debug(
                "📋 Actuator '%s' datapoints: %s",
                actuator.name,
                {
                    role: f"{addr} ({addr >> 11}/{(addr >> 8) & 0x7}/{addr & 0xFF})"
                    for role, addr in datapoints.items()
                },
            )

        # Heating actuator detection: heizungsart parameter + Istwert + Sollwert roles
        if (
            "heizungsart" in actuator.parameters
            and "Istwert" in datapoints
            and "Sollwert" in datapoints
        ):
            istwert_addr = datapoints["Istwert"]
            zone_key = (device.id, istwert_addr)
            if zone_key in self._h6_claimed_zones:
                _LOGGER.debug(
                    "Skipping H6 channel %s — Istwert %d already claimed by another channel on device %s",
                    actuator.name,
                    istwert_addr,
                    device.id,
                )
                return
            platform = Platform.CLIMATE
            entity_type = "climate"
            self._h6_claimed_zones.add(zone_key)
        else:
            # Determine platform based on primary roles
            determined_platform = self._determine_platform(datapoints)
            if determined_platform is None:
                roles = list(datapoints.keys())
                unknown = [r for r in roles if r not in self.platform_detector.ROLE_TO_PLATFORM]
                if unknown:
                    _LOGGER.warning(
                        "Skipping actuator '%s' — unrecognised roles: %s. "
                        "Please open an issue at https://github.com/phismith91/luxorliving/issues "
                        "so this device type can be added.",
                        actuator.name,
                        unknown,
                    )
                else:
                    known_skipped = {
                        r for r in roles if r in self.platform_detector.ROLE_TO_PLATFORM
                    }
                    _LOGGER.debug(
                        "Skipping actuator '%s' — roles %s are intentionally unmapped "
                        "(e.g. Scene, ZentralAus, status-only datapoints).",
                        actuator.name,
                        known_skipped,
                    )
                return
            platform = determined_platform

            # Determine entity type
            if platform == Platform.LIGHT:
                if "Dimmen%" in datapoints or "status@Dim" in datapoints:
                    entity_type = "dimmable_light"
                else:
                    entity_type = "light"
            else:
                entity_type = platform.value

        # Generate unique ID - use control address to ensure uniqueness
        # Different actuators can have same name but different addresses
        control_address = (
            datapoints.get("OnOff")
            or datapoints.get("SchaltenOnOff")
            or datapoints.get("UpDown")
            or datapoints.get("Dimmen%")
            or list(datapoints.values())[0]
            if datapoints
            else "unknown"
        )
        unique_id = f"{device.id}_{control_address}"

        # Generate friendly name
        name = actuator.name or f"{device.name} Ch{actuator.channel}"

        # Remove device name prefix if present to avoid duplication
        if name.startswith(device.name + " "):
            name = name[len(device.name) + 1 :]

        # Detect cooling capability for climate entities
        cooling_capable = platform == Platform.CLIMATE and "UmschaltenHeitzenKühlen" in datapoints

        # Create mapped entity
        entity = MappedEntity(
            platform=platform,
            unique_id=unique_id,
            name=name,
            device_name=device.name,
            device_id=device.id,
            entity_type=entity_type,
            datapoints=datapoints,
            attributes={
                "channel": actuator.channel,
                "on_icon": actuator.on_icon,
                "off_icon": actuator.off_icon,
                "use_case": actuator.use_case,
                "serial_number": device.serial_number,
                "knx_address": device.address,
            },
            parameters=actuator.parameters,
            cooling_capable=cooling_capable,
        )

        self.entities.append(entity)
        if cooling_capable:
            _LOGGER.debug(
                "Mapped %s actuator '%s' to %s (cooling capable)", entity_type, name, platform
            )
        else:
            _LOGGER.debug("Mapped %s actuator '%s' to %s", entity_type, name, platform)

    def _make_sensor_climate_entity(
        self, device: LXPDevice, sensor: LXPSensor, datapoints: dict[str, int], label: str
    ) -> MappedEntity:
        """Build a CLIMATE MappedEntity from a sensor channel (R718 or RTR)."""
        name = sensor.name or f"{device.name} Ch{sensor.channel}"
        if name.startswith(device.name + " "):
            name = name[len(device.name) + 1 :]
        entity = MappedEntity(
            platform=Platform.CLIMATE,
            unique_id=f"{device.id}_{datapoints['Istwert']}",
            name=name,
            device_name=device.name,
            device_id=device.id,
            entity_type="climate",
            datapoints=datapoints,
            attributes={
                "channel": sensor.channel,
                "sensor_type": sensor.sensor_type,
                "serial_number": device.serial_number,
                "knx_address": device.address,
            },
            parameters=sensor.parameters,
        )
        _LOGGER.debug("Mapped %s '%s' to climate", label, name)
        return entity

    def _map_sensor(self, device: LXPDevice, sensor: LXPSensor) -> None:
        """Map a sensor to entities."""
        # Collect datapoints by role
        datapoints = {dp.role: dp.address for dp in sensor.datapoints}

        if not datapoints:
            _LOGGER.debug("Skipping sensor %s - no datapoints", sensor.name)
            return

        # Special handling for Wetterstation: extract individual sensor entities
        if "wetterstation" in device.name.lower():
            self._map_wetterstation_sensor(device, sensor, datapoints)
            return

        # R718 standalone thermostat: Istwert + Sollwert + status@Sollwert (no activateRTR param)
        # Theben RTR 718 is a dedicated room thermostat device, distinct from iON panel RTR.
        # R718 and H6 in the same zone intentionally share KNX group addresses — both must
        # produce a climate entity (wall display vs. valve actuator). See issue #141.
        if (
            "Istwert" in datapoints
            and "Sollwert" in datapoints
            and "status@Sollwert" in datapoints
            and sensor.parameters.get("activateRTR") != "1"
        ):
            self.entities.append(
                self._make_sensor_climate_entity(device, sensor, datapoints, "R718 thermostat")
            )
            return

        # RTR thermostat detection: activateRTR=1 + Istwert + (Sollwert or status@Sollwert)
        if (
            sensor.parameters.get("activateRTR") == "1"
            and "Istwert" in datapoints
            and ("Sollwert" in datapoints or "status@Sollwert" in datapoints)
        ):
            self.entities.append(
                self._make_sensor_climate_entity(device, sensor, datapoints, "RTR sensor")
            )
            return

        # Determine platform based on sensor roles
        # Priority 1: Check for sensor types (Temperature, Humidity, etc.)
        platform = None
        entity_type = None
        device_class = None
        unit_of_measurement = None

        # Use PlatformDetector to find matching sensor role
        detected_role = None
        for role in datapoints.keys():
            if self.platform_detector.detect_platform(role) == Platform.SENSOR:
                detected_role = role
                break

        if detected_role:
            platform = Platform.SENSOR
            entity_type = detected_role.lower()
            device_class = self.platform_detector.get_device_class(detected_role)
            unit_of_measurement = self.platform_detector.get_unit(detected_role)

        # Priority 2: Check for binary control/status
        # Sensors are always input devices — OnOff in a sensor context is a contact
        # state, never a controllable switch. B6, T-series, and other binary inputs
        # must map to binary_sensor regardless of whether status@OnOff is also present.
        if platform is None:
            if "status@OnOff" in datapoints or "OnOff" in datapoints:
                platform = Platform.BINARY_SENSOR
                entity_type = (
                    "motion"
                    if ("MasterSlave" in datapoints or sensor.sensor_type == 1)
                    else "binary_sensor"
                )

        if platform is None:
            roles = list(datapoints.keys())
            unknown = [r for r in roles if r not in self.platform_detector.ROLE_TO_PLATFORM]
            if unknown:
                _LOGGER.warning(
                    "Skipping sensor '%s' — unrecognised roles: %s. "
                    "Please open an issue at https://github.com/phismith91/luxorliving/issues "
                    "so this device type can be added.",
                    sensor.name,
                    unknown,
                )
            else:
                known_skipped = {r for r in roles if r in self.platform_detector.ROLE_TO_PLATFORM}
                _LOGGER.debug(
                    "Skipping sensor '%s' — roles %s are intentionally unmapped "
                    "(e.g. Scene, ZentralAus, status-only datapoints).",
                    sensor.name,
                    known_skipped,
                )
            return

        # Generate unique ID - use the first datapoint address to ensure uniqueness
        # Different sensors can have same name but different addresses
        primary_addr: str | int = list(datapoints.values())[0] if datapoints else "unknown"
        unique_id = f"{device.id}_{primary_addr}"

        # Generate friendly name
        name = sensor.name or f"{device.name} Ch{sensor.channel}"

        # Remove device name prefix if present to avoid duplication
        if name.startswith(device.name + " "):
            name = name[len(device.name) + 1 :]

        # Create mapped entity with sensor-specific attributes
        attributes = {
            "channel": sensor.channel,
            "sensor_type": sensor.sensor_type,
            "serial_number": device.serial_number,
            "knx_address": device.address,
        }

        # Add sensor-specific attributes
        if device_class:
            attributes["device_class"] = device_class
        if unit_of_measurement:
            attributes["unit_of_measurement"] = unit_of_measurement

        entity = MappedEntity(
            platform=platform,
            unique_id=unique_id,
            name=name,
            device_name=device.name,
            device_id=device.id,
            entity_type=entity_type,  # type: ignore
            datapoints=datapoints,
            attributes=attributes,
            parameters=sensor.parameters,
        )

        self.entities.append(entity)
        _LOGGER.debug(
            "Mapped sensor '%s' to %s (type=%s, unit=%s)",
            name,
            platform,
            entity_type,
            unit_of_measurement,
        )

    def _determine_platform(self, datapoints: dict[str, int]) -> Platform | None:
        """Determine the platform based on datapoint roles.

        Delegates to PlatformDetector for role-to-platform mapping.
        """
        # Priority order for role detection
        control_roles = ["OnOff", "SchaltenOnOff", "Dimmen%", "UpDown"]

        for role in control_roles:
            if role in datapoints:
                return self.platform_detector.detect_platform(role)

        return None

    def get_entities_by_platform(self, platform: Platform) -> list[MappedEntity]:
        """Get all entities for a specific platform."""
        return [e for e in self.entities if e.platform == platform]

    def get_entity_by_unique_id(self, unique_id: str) -> MappedEntity | None:
        """Get entity by unique ID."""
        return next((e for e in self.entities if e.unique_id == unique_id), None)

    def get_group_address_label_map(self) -> dict[str, list[str]]:
        """Build a map of KNX group address string → list of labels 'Name (ID)'.

        This is used to enrich KNX logs with human-friendly names.
        """
        ga_labels: dict[str, list[str]] = {}
        for entity in self.entities:
            label = f"{entity.name} ({entity.unique_id})"
            for role, addr in entity.datapoints.items():
                try:
                    ga_str = str(GroupAddress(addr))
                except Exception as err:
                    _LOGGER.debug(
                        "Could not parse group address %r, using bitmask fallback: %s", addr, err
                    )
                    # Fallback: derive GA via bit masks (main/line/group)
                    ga_str = f"{addr >> 11}/{(addr >> 8) & 0x7}/{addr & 0xFF}"
                if label not in ga_labels.setdefault(ga_str, []):
                    ga_labels[ga_str].append(label)
        return ga_labels

    def get_individual_address_label_map(self) -> dict[str, list[str]]:
        """Build a map of KNX individual address (IA) → labels 'DeviceName (DeviceID)'."""
        ia_labels: dict[str, list[str]] = {}
        for entity in self.entities:
            # Device-level label
            dev_label = f"{entity.device_name} ({entity.device_id})"
            ia = entity.attributes.get("knx_address")
            if not ia:
                continue
            ia_str = str(ia)
            if dev_label not in ia_labels.setdefault(ia_str, []):
                ia_labels[ia_str].append(dev_label)
        return ia_labels

    # --- Wetterstation special handling ---
    def _map_wetterstation_sensor(
        self, device: LXPDevice, sensor: LXPSensor, datapoints: dict[str, int]
    ) -> None:
        """Create individual sensor entities from Wetterstation datapoints.

        Wetterstation sensors have multiple roles (Temperatur, HelligkeitMitte, etc.)
        but are marked affected=0. We create separate entities for each role.

        Uses PlatformDetector for role-to-attributes mapping.
        """
        # Role -> entity_name_suffix mapping (uses PlatformDetector for class/unit)
        #
        # The role strings below come straight from Theben's LXP export and do
        # NOT match physical sensor position — confirmed via #141 by comparing
        # live values against LuxorPlay (ground truth) for the same install.
        # The rc.9 fix rotated all three one step too far (Marcus, 2026-07-26):
        # only HelligkeitMitte is actually swapped; Links/Rechts are correct as-is.
        #   role HelligkeitMitte  is physically "Links"
        #   role HelligkeitLinks  is physically "Vorne"
        #   role HelligkeitRechts is physically "Rechts"
        wetterstation_roles = {
            "Temperatur": "Außentemperatur",
            "Windgeschwindigkeit": "Windgeschwindigkeit",
            "HelligkeitMitte": "Helligkeit Links",
            "HelligkeitLinks": "Helligkeit Vorne",
            "HelligkeitRechts": "Helligkeit Rechts",
            "Regen": "Regen",  # Binary/status
        }

        for role, name_suffix in wetterstation_roles.items():
            if role not in datapoints:
                continue

            addr = datapoints[role]
            unique_id = f"{device.id}_{addr}"

            # Check if already exists (avoid duplicates)
            if any(e.unique_id == unique_id for e in self.entities):
                continue

            # Regen (rain sensor) is a binary signal → binary_sensor entity
            if role == "Regen":
                entity = MappedEntity(
                    platform=Platform.BINARY_SENSOR,
                    unique_id=unique_id,
                    name=f"{device.name} {name_suffix}",
                    device_name=device.name,
                    device_id=device.id,
                    entity_type="regen",
                    datapoints={role: addr},
                    attributes={
                        "channel": sensor.channel,
                        "sensor_type": sensor.sensor_type,
                        "serial_number": device.serial_number,
                        "knx_address": device.address,
                    },
                    parameters=sensor.parameters,
                )
                self.entities.append(entity)
                _LOGGER.debug(
                    "Mapped Wetterstation rain sensor '%s' at address %s", entity.name, addr
                )
                continue

            # Use PlatformDetector for device class and unit
            dev_class = self.platform_detector.get_device_class(role)
            unit = self.platform_detector.get_unit(role)

            entity = MappedEntity(
                platform=Platform.SENSOR,
                unique_id=unique_id,
                name=f"{device.name} {name_suffix}",
                device_name=device.name,
                device_id=device.id,
                entity_type=role.lower(),
                datapoints={role: addr},
                attributes={
                    "device_class": dev_class,
                    "unit_of_measurement": unit,
                    "channel": sensor.channel,
                    "sensor_type": sensor.sensor_type,
                    "serial_number": device.serial_number,
                    "knx_address": device.address,
                },
                parameters=sensor.parameters,
            )

            self.entities.append(entity)
            _LOGGER.debug(
                "Mapped Wetterstation sensor '%s' (%s) at address %s",
                entity.name,
                role,
                addr,
            )
