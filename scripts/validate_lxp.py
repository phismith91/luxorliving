#!/usr/bin/env python3
"""LXP File Validation Script for LUXORliving Integration.

This script validates LXP project files for common issues and provides
detailed reports about configuration problems.
"""

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# Add the custom_components directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from custom_components.luxor_living.lxp_parser import LXPCache


@dataclass
class ValidationIssue:
    """Represents a validation issue found in the LXP file."""

    severity: str  # "error", "warning", "info"
    category: str
    message: str
    device_name: str | None = None
    device_address: str | None = None
    suggestion: str | None = None


class LXPValidator:
    """Validator for LXP project files."""

    def __init__(self, lxp_path: Path):
        """Initialize the validator.

        Args:
            lxp_path: Path to the LXP file to validate
        """
        self.lxp_path = lxp_path
        self.issues: List[ValidationIssue] = []
        self.stats: Dict[str, Any] = {}

    async def validate(self) -> bool:
        """Run all validation checks.

        Returns:
            True if no errors were found, False otherwise
        """
        print(f"🔍 Validating LXP file: {self.lxp_path.name}")
        print("=" * 60)

        # Check file exists and is readable
        if not self._check_file_exists():
            return False

        # Parse the file
        try:
            cache = LXPCache()
            project = await cache.get_or_parse(self.lxp_path, include_unaffected=True)
        except Exception as e:
            self.issues.append(
                ValidationIssue(
                    severity="error",
                    category="parsing",
                    message=f"Failed to parse LXP file: {e}",
                    suggestion="Check if the file is corrupted or not a valid LXP file",
                )
            )
            return False

        # Collect statistics
        self._collect_statistics(project)

        # Run validation checks
        self._check_devices_without_datapoints(project)
        self._check_duplicate_addresses(project)
        self._check_invalid_gateway_config(project)
        self._check_sensor_actuator_config(project)
        self._check_naming_conventions(project)

        # Print results
        self._print_results()

        # Return True if no errors
        return not any(issue.severity == "error" for issue in self.issues)

    def _check_file_exists(self) -> bool:
        """Check if the LXP file exists and is readable."""
        if not self.lxp_path.exists():
            self.issues.append(
                ValidationIssue(
                    severity="error",
                    category="file",
                    message=f"LXP file not found: {self.lxp_path}",
                )
            )
            return False

        if not self.lxp_path.is_file():
            self.issues.append(
                ValidationIssue(
                    severity="error",
                    category="file",
                    message=f"Path is not a file: {self.lxp_path}",
                )
            )
            return False

        return True

    def _collect_statistics(self, project) -> None:
        """Collect statistics about the project."""
        self.stats = {
            "project_name": project.name,
            "gateway": f"{project.gateway_address}:{project.gateway_port}",
            "total_devices": len(project.devices),
            "total_sensors": sum(len(d.sensors) for d in project.devices),
            "total_actuators": sum(len(d.actuators) for d in project.devices),
            "total_datapoints": sum(len(s.datapoints) for d in project.devices for s in d.sensors)
            + sum(len(a.datapoints) for d in project.devices for a in d.actuators),
            "devices_without_datapoints": sum(
                1 for d in project.devices if not d.sensors and not d.actuators
            ),
        }

    def _check_devices_without_datapoints(self, project) -> None:
        """Check for devices without any datapoints."""
        devices_without_datapoints = [
            d for d in project.devices if not d.sensors and not d.actuators
        ]

        if devices_without_datapoints:
            for device in devices_without_datapoints:
                self.issues.append(
                    ValidationIssue(
                        severity="warning",
                        category="configuration",
                        message="Device has no datapoints configured",
                        device_name=device.name,
                        device_address=device.address,
                        suggestion="Check KNX programming in LUXORplug and assign group addresses",
                    )
                )

    def _check_duplicate_addresses(self, project) -> None:
        """Check for duplicate device addresses."""
        address_map: Dict[str, List[str]] = {}

        for device in project.devices:
            if device.address not in address_map:
                address_map[device.address] = []
            address_map[device.address].append(device.name)

        for address, device_names in address_map.items():
            if len(device_names) > 1:
                self.issues.append(
                    ValidationIssue(
                        severity="error",
                        category="addressing",
                        message=f"Duplicate KNX address {address} used by {len(device_names)} devices: {', '.join(device_names)}",
                        suggestion="Each device must have a unique KNX address",
                    )
                )

    def _check_invalid_gateway_config(self, project) -> None:
        """Check for invalid gateway configuration."""
        # Check gateway IP
        if not project.gateway_address or project.gateway_address == "0.0.0.0":
            self.issues.append(
                ValidationIssue(
                    severity="error",
                    category="gateway",
                    message="Invalid gateway IP address",
                    suggestion="Configure a valid gateway IP in LUXORplug",
                )
            )

        # Check gateway port
        if project.gateway_port <= 0 or project.gateway_port > 65535:
            self.issues.append(
                ValidationIssue(
                    severity="error",
                    category="gateway",
                    message=f"Invalid gateway port: {project.gateway_port}",
                    suggestion="KNX/IP default port is 3671",
                )
            )

    def _check_sensor_actuator_config(self, project) -> None:
        """Check for sensors/actuators without datapoints."""
        for device in project.devices:
            # Check sensors
            for sensor in device.sensors:
                if not sensor.datapoints:
                    self.issues.append(
                        ValidationIssue(
                            severity="info",
                            category="configuration",
                            message=f"Sensor '{sensor.name}' has no datapoints",
                            device_name=device.name,
                            device_address=device.address,
                        )
                    )

            # Check actuators
            for actuator in device.actuators:
                if not actuator.datapoints:
                    self.issues.append(
                        ValidationIssue(
                            severity="info",
                            category="configuration",
                            message=f"Actuator '{actuator.name}' has no datapoints",
                            device_name=device.name,
                            device_address=device.address,
                        )
                    )

    def _check_naming_conventions(self, project) -> None:
        """Check for naming convention issues."""
        for device in project.devices:
            # Check for very long names
            if len(device.name) > 50:
                self.issues.append(
                    ValidationIssue(
                        severity="info",
                        category="naming",
                        message=f"Device name is very long ({len(device.name)} characters)",
                        device_name=device.name,
                        device_address=device.address,
                        suggestion="Consider using shorter, more concise names for better readability",
                    )
                )

            # Check for devices without meaningful names
            if not device.name or device.name.strip() == "":
                self.issues.append(
                    ValidationIssue(
                        severity="warning",
                        category="naming",
                        message="Device has no name",
                        device_address=device.address,
                        suggestion="Assign a descriptive name in LUXORplug",
                    )
                )

    def _print_results(self) -> None:
        """Print validation results."""
        print("\n📊 Project Statistics:")
        print(f"  • Project: {self.stats['project_name']}")
        print(f"  • Gateway: {self.stats['gateway']}")
        print(f"  • Devices: {self.stats['total_devices']}")
        print(f"  • Sensors: {self.stats['total_sensors']}")
        print(f"  • Actuators: {self.stats['total_actuators']}")
        print(f"  • Datapoints: {self.stats['total_datapoints']}")

        if self.stats["devices_without_datapoints"] > 0:
            print(
                f"\n⚠️  {self.stats['devices_without_datapoints']} device(s) without datapoints "
                f"({self.stats['devices_without_datapoints'] / self.stats['total_devices'] * 100:.1f}%)"
            )

        # Group issues by severity
        errors = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        infos = [i for i in self.issues if i.severity == "info"]

        print("\n" + "=" * 60)
        print("🔍 Validation Results:")
        print("=" * 60)

        if not self.issues:
            print("✅ No issues found - LXP file is valid!")
            return

        # Print errors
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for issue in errors:
                self._print_issue(issue)

        # Print warnings
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for issue in warnings:
                self._print_issue(issue)

        # Print infos
        if infos:
            print(f"\nℹ️  Information ({len(infos)}):")
            for issue in infos:
                self._print_issue(issue)

        # Print summary
        print("\n" + "=" * 60)
        print(f"Summary: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info")

        if errors:
            print("❌ Validation FAILED - Fix errors before using this LXP file")
        elif warnings:
            print("⚠️  Validation passed with warnings - Review warnings for best results")
        else:
            print("✅ Validation PASSED - LXP file is ready for use")

    def _print_issue(self, issue: ValidationIssue) -> None:
        """Print a single validation issue."""
        indent = "  "
        print(f"{indent}• [{issue.category.upper()}] {issue.message}")

        if issue.device_name:
            print(f"{indent}  Device: {issue.device_name}")
        if issue.device_address:
            print(f"{indent}  Address: {issue.device_address}")
        if issue.suggestion:
            print(f"{indent}  💡 {issue.suggestion}")
        print()


async def main():
    """Main entry point for the validation script."""
    if len(sys.argv) < 2:
        print("Usage: python validate_lxp.py <path_to_lxp_file>")
        print("\nExample:")
        print("  python validate_lxp.py docs/Hauptwohnung.lxp")
        sys.exit(1)

    lxp_path = Path(sys.argv[1])

    validator = LXPValidator(lxp_path)
    success = await validator.validate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
