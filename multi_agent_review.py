#!/usr/bin/env python3
"""
Multi-Agent Code Review System for LUXORliving Repository

This system coordinates multiple specialized AI agents to perform a comprehensive
code review across different dimensions: security, quality, architecture,
performance, testing, and documentation.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys


class AgentRole(Enum):
    """Specialized roles for code review agents."""
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPENDENCIES = "dependencies"


@dataclass
class Finding:
    """Represents a single review finding."""
    severity: str  # critical, high, medium, low, info
    category: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class AgentReport:
    """Report from a single agent."""
    agent_role: AgentRole
    findings: List[Finding] = field(default_factory=list)
    summary: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0


class ReviewAgent:
    """Base class for specialized review agents."""

    def __init__(self, role: AgentRole, repo_path: Path):
        self.role = role
        self.repo_path = repo_path
        self.component_path = repo_path / "custom_components" / "luxor_living"
        self.test_path = repo_path / "tests"

    async def analyze(self) -> AgentReport:
        """Execute the agent's analysis."""
        raise NotImplementedError("Subclasses must implement analyze()")

    def _create_finding(self, severity: str, category: str, title: str,
                       description: str, **kwargs) -> Finding:
        """Helper to create a finding."""
        return Finding(
            severity=severity,
            category=category,
            title=title,
            description=description,
            **kwargs
        )


class SecurityAgent(ReviewAgent):
    """Agent focused on security vulnerabilities and best practices."""

    def __init__(self, repo_path: Path):
        super().__init__(AgentRole.SECURITY, repo_path)

    async def analyze(self) -> AgentReport:
        """Analyze security aspects of the codebase."""
        start_time = asyncio.get_event_loop().time()
        findings = []

        # Check for common security issues
        findings.extend(await self._check_xml_security())
        findings.extend(await self._check_input_validation())
        findings.extend(await self._check_authentication())
        findings.extend(await self._check_secrets_management())
        findings.extend(await self._check_dependency_vulnerabilities())

        execution_time = asyncio.get_event_loop().time() - start_time

        summary = f"Security review completed. Found {len(findings)} potential security concerns."

        return AgentReport(
            agent_role=self.role,
            findings=findings,
            summary=summary,
            metrics={"total_findings": len(findings)},
            execution_time=execution_time
        )

    async def _check_xml_security(self) -> List[Finding]:
        """Check for XML security issues."""
        findings = []
        lxp_parser = self.component_path / "lxp_parser.py"

        if lxp_parser.exists():
            content = lxp_parser.read_text()
            if "defusedxml" in content:
                findings.append(self._create_finding(
                    "info",
                    "XML Security",
                    "Secure XML parsing implemented",
                    "The code uses defusedxml library which protects against XML attacks (XXE, billion laughs, etc.)",
                    file_path=str(lxp_parser),
                    recommendation="Continue using defusedxml for all XML parsing operations."
                ))
            else:
                findings.append(self._create_finding(
                    "high",
                    "XML Security",
                    "Potentially unsafe XML parsing",
                    "Standard xml.etree may be vulnerable to XML attacks. Consider using defusedxml.",
                    file_path=str(lxp_parser),
                    recommendation="Replace xml.etree with defusedxml.ElementTree"
                ))

        return findings

    async def _check_input_validation(self) -> List[Finding]:
        """Check for input validation issues."""
        findings = []
        config_flow = self.component_path / "config_flow.py"

        if config_flow.exists():
            content = config_flow.read_text()
            if "vol." in content and "schema" in content.lower():
                findings.append(self._create_finding(
                    "info",
                    "Input Validation",
                    "Input validation using Voluptuous",
                    "Configuration inputs are validated using Voluptuous schema validation.",
                    file_path=str(config_flow),
                    recommendation="Ensure all user inputs are validated through schemas."
                ))

        return findings

    async def _check_authentication(self) -> List[Finding]:
        """Check authentication implementation."""
        findings = []
        rest_client = self.component_path / "rest_client.py"

        if rest_client.exists():
            content = rest_client.read_text()

            # Check for hardcoded credentials
            if any(keyword in content.lower() for keyword in ["password =", "token =", "api_key ="]):
                # Check if it's just variable assignment, not hardcoded value
                if '"' in content or "'" in content:
                    findings.append(self._create_finding(
                        "medium",
                        "Authentication",
                        "Verify no hardcoded credentials",
                        "Detected potential credential assignment. Verify no passwords/tokens are hardcoded.",
                        file_path=str(rest_client),
                        recommendation="Use configuration storage or environment variables for credentials."
                    ))

            # Check for HTTPS
            if "http://" in content and "https://" not in content:
                findings.append(self._create_finding(
                    "medium",
                    "Authentication",
                    "Unencrypted HTTP connections",
                    "HTTP connections detected. Authentication should use HTTPS.",
                    file_path=str(rest_client),
                    recommendation="Enforce HTTPS for all authentication and API calls."
                ))

        return findings

    async def _check_secrets_management(self) -> List[Finding]:
        """Check for secrets management issues."""
        findings = []

        # Check .gitignore
        gitignore = self.repo_path / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            if "*.env" in content or ".env" in content:
                findings.append(self._create_finding(
                    "info",
                    "Secrets Management",
                    "Environment files ignored in git",
                    ".env files are properly excluded from version control.",
                    file_path=str(gitignore)
                ))

        return findings

    async def _check_dependency_vulnerabilities(self) -> List[Finding]:
        """Check for known vulnerable dependencies."""
        findings = []

        # Check if bandit security scanner is configured
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "bandit" in content:
                findings.append(self._create_finding(
                    "info",
                    "Security Scanning",
                    "Security scanner configured",
                    "Bandit security scanner is configured in the project.",
                    file_path=str(pyproject),
                    recommendation="Run bandit regularly in CI/CD pipeline."
                ))

        return findings


class CodeQualityAgent(ReviewAgent):
    """Agent focused on code quality, style, and best practices."""

    def __init__(self, repo_path: Path):
        super().__init__(AgentRole.CODE_QUALITY, repo_path)

    async def analyze(self) -> AgentReport:
        """Analyze code quality aspects."""
        start_time = asyncio.get_event_loop().time()
        findings = []

        findings.extend(await self._check_code_formatting())
        findings.extend(await self._check_type_hints())
        findings.extend(await self._check_docstrings())
        findings.extend(await self._check_complexity())
        findings.extend(await self._check_error_handling())

        execution_time = asyncio.get_event_loop().time() - start_time

        summary = f"Code quality review completed. Found {len(findings)} observations."

        return AgentReport(
            agent_role=self.role,
            findings=findings,
            summary=summary,
            metrics={"total_findings": len(findings)},
            execution_time=execution_time
        )

    async def _check_code_formatting(self) -> List[Finding]:
        """Check code formatting configuration."""
        findings = []
        pyproject = self.repo_path / "pyproject.toml"

        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.black]" in content:
                findings.append(self._create_finding(
                    "info",
                    "Code Formatting",
                    "Black formatter configured",
                    "Black code formatter is configured for consistent code style.",
                    file_path=str(pyproject)
                ))

            if "[tool.isort]" in content:
                findings.append(self._create_finding(
                    "info",
                    "Import Sorting",
                    "Import sorting configured",
                    "isort is configured for consistent import organization.",
                    file_path=str(pyproject)
                ))

        return findings

    async def _check_type_hints(self) -> List[Finding]:
        """Check for type hints usage."""
        findings = []

        # Check if mypy is configured
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.mypy]" in content:
                findings.append(self._create_finding(
                    "info",
                    "Type Safety",
                    "Static type checking enabled",
                    "mypy is configured for static type analysis.",
                    file_path=str(pyproject),
                    recommendation="Ensure strict mode is enabled and all code passes mypy checks."
                ))

        # Sample check: look at a key file for type hints
        init_file = self.component_path / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            type_hint_indicators = ["->", ": str", ": int", ": bool", ": Dict", ": List"]
            if any(indicator in content for indicator in type_hint_indicators):
                findings.append(self._create_finding(
                    "info",
                    "Type Hints",
                    "Type hints present in code",
                    "Code uses type hints for better type safety and IDE support.",
                    file_path=str(init_file)
                ))

        return findings

    async def _check_docstrings(self) -> List[Finding]:
        """Check for docstring presence and quality."""
        findings = []

        # Check if flake8 with docstring plugin is configured
        flake8_config = self.repo_path / ".flake8"
        if flake8_config.exists():
            content = flake8_config.read_text()
            if "D" in content:  # D-series are docstring errors
                findings.append(self._create_finding(
                    "info",
                    "Documentation",
                    "Docstring linting enabled",
                    "Flake8 is configured to check docstring quality.",
                    file_path=str(flake8_config)
                ))

        return findings

    async def _check_complexity(self) -> List[Finding]:
        """Check for code complexity issues."""
        findings = []

        # Check if radon is configured
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "radon" in content.lower():
                findings.append(self._create_finding(
                    "info",
                    "Code Complexity",
                    "Complexity analysis tool configured",
                    "Radon is available for measuring code complexity.",
                    file_path=str(pyproject),
                    recommendation="Set complexity thresholds and fail builds on violations."
                ))

        # Check large files that might benefit from refactoring
        for py_file in self.component_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            lines = py_file.read_text().split("\n")
            if len(lines) > 600:
                findings.append(self._create_finding(
                    "low",
                    "Code Complexity",
                    f"Large file: {py_file.name}",
                    f"File has {len(lines)} lines. Consider breaking into smaller modules.",
                    file_path=str(py_file),
                    recommendation="Split large files into smaller, focused modules for better maintainability."
                ))

        return findings

    async def _check_error_handling(self) -> List[Finding]:
        """Check error handling patterns."""
        findings = []

        # Check for circuit breaker pattern
        circuit_breaker = self.component_path / "circuit_breaker.py"
        if circuit_breaker.exists():
            findings.append(self._create_finding(
                "info",
                "Error Handling",
                "Circuit breaker pattern implemented",
                "Resilience pattern for fault tolerance is implemented.",
                file_path=str(circuit_breaker),
                recommendation="Ensure circuit breaker is used for all external service calls."
            ))

        return findings


class ArchitectureAgent(ReviewAgent):
    """Agent focused on architecture and design patterns."""

    def __init__(self, repo_path: Path):
        super().__init__(AgentRole.ARCHITECTURE, repo_path)

    async def analyze(self) -> AgentReport:
        """Analyze architecture and design."""
        start_time = asyncio.get_event_loop().time()
        findings = []

        findings.extend(await self._check_separation_of_concerns())
        findings.extend(await self._check_design_patterns())
        findings.extend(await self._check_async_patterns())
        findings.extend(await self._check_modularity())

        execution_time = asyncio.get_event_loop().time() - start_time

        summary = f"Architecture review completed. Found {len(findings)} architectural observations."

        return AgentReport(
            agent_role=self.role,
            findings=findings,
            summary=summary,
            metrics={"total_findings": len(findings)},
            execution_time=execution_time
        )

    async def _check_separation_of_concerns(self) -> List[Finding]:
        """Check for proper separation of concerns."""
        findings = []

        # Check if different concerns are in separate files
        key_components = {
            "config_flow.py": "Configuration management",
            "knx_gateway.py": "KNX communication",
            "lxp_parser.py": "LXP file parsing",
            "entity_mapper.py": "Entity mapping logic",
            "rest_client.py": "REST API client"
        }

        present_components = []
        for filename, purpose in key_components.items():
            if (self.component_path / filename).exists():
                present_components.append(f"{filename} ({purpose})")

        if len(present_components) >= 4:
            findings.append(self._create_finding(
                "info",
                "Architecture",
                "Good separation of concerns",
                f"Code is well-organized into separate modules: {', '.join(present_components)}",
                recommendation="Maintain this separation as the codebase evolves."
            ))

        return findings

    async def _check_design_patterns(self) -> List[Finding]:
        """Check for design pattern usage."""
        findings = []

        # Check for coordinator pattern (Home Assistant specific)
        coordinator_file = self.component_path / "coordinator.py"
        if coordinator_file.exists():
            findings.append(self._create_finding(
                "info",
                "Design Patterns",
                "Coordinator pattern implemented",
                "Using DataUpdateCoordinator for efficient state management.",
                file_path=str(coordinator_file),
                recommendation="Ensure all entities use the coordinator for data updates."
            ))

        # Check for entity pattern
        entity_file = self.component_path / "entity.py"
        if entity_file.exists():
            findings.append(self._create_finding(
                "info",
                "Design Patterns",
                "Base entity abstraction",
                "Common entity functionality is abstracted in a base class.",
                file_path=str(entity_file),
                recommendation="All platform entities should inherit from this base class."
            ))

        return findings

    async def _check_async_patterns(self) -> List[Finding]:
        """Check for async/await patterns."""
        findings = []

        # Check key files for async usage
        for py_file in self.component_path.glob("*.py"):
            content = py_file.read_text()
            if "async def" in content:
                # Check if async is used correctly
                if "await" in content:
                    continue  # Looks good
                else:
                    findings.append(self._create_finding(
                        "medium",
                        "Async Patterns",
                        f"Async functions without await in {py_file.name}",
                        "File contains async functions but no await statements. Verify if async is necessary.",
                        file_path=str(py_file),
                        recommendation="Review async functions and ensure they properly await async operations."
                    ))

        return findings

    async def _check_modularity(self) -> List[Finding]:
        """Check code modularity."""
        findings = []

        # Count platform implementations
        platforms = ["light.py", "switch.py", "sensor.py", "binary_sensor.py",
                    "climate.py", "cover.py"]
        found_platforms = [p for p in platforms if (self.component_path / p).exists()]

        if len(found_platforms) >= 4:
            findings.append(self._create_finding(
                "info",
                "Modularity",
                "Multiple platform support",
                f"Integration supports {len(found_platforms)} platforms: {', '.join(found_platforms)}",
                recommendation="Ensure platform implementations follow consistent patterns."
            ))

        return findings


class PerformanceAgent(ReviewAgent):
    """Agent focused on performance optimization."""

    def __init__(self, repo_path: Path):
        super().__init__(AgentRole.PERFORMANCE, repo_path)

    async def analyze(self) -> AgentReport:
        """Analyze performance aspects."""
        start_time = asyncio.get_event_loop().time()
        findings = []

        findings.extend(await self._check_caching())
        findings.extend(await self._check_rate_limiting())
        findings.extend(await self._check_async_operations())
        findings.extend(await self._check_benchmarking())

        execution_time = asyncio.get_event_loop().time() - start_time

        summary = f"Performance review completed. Found {len(findings)} performance-related observations."

        return AgentReport(
            agent_role=self.role,
            findings=findings,
            summary=summary,
            metrics={"total_findings": len(findings)},
            execution_time=execution_time
        )

    async def _check_caching(self) -> List[Finding]:
        """Check for caching implementation."""
        findings = []

        lxp_parser = self.component_path / "lxp_parser.py"
        if lxp_parser.exists():
            content = lxp_parser.read_text()
            if "cache" in content.lower():
                findings.append(self._create_finding(
                    "info",
                    "Performance",
                    "Caching implemented",
                    "LXP parser implements caching to avoid redundant parsing operations.",
                    file_path=str(lxp_parser),
                    recommendation="Monitor cache hit rates and adjust TTL as needed."
                ))

        return findings

    async def _check_rate_limiting(self) -> List[Finding]:
        """Check for rate limiting."""
        findings = []

        switch_file = self.component_path / "switch.py"
        if switch_file.exists():
            content = switch_file.read_text()
            if "rate" in content.lower() or "throttle" in content.lower():
                findings.append(self._create_finding(
                    "info",
                    "Performance",
                    "Rate limiting implemented",
                    "Switch platform includes rate limiting to prevent rapid state changes.",
                    file_path=str(switch_file),
                    recommendation="Verify rate limits are appropriate for the use case."
                ))

        return findings

    async def _check_async_operations(self) -> List[Finding]:
        """Check for efficient async operations."""
        findings = []

        init_file = self.component_path / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            if "asyncio.gather" in content or "create_task" in content:
                findings.append(self._create_finding(
                    "info",
                    "Performance",
                    "Parallel async operations",
                    "Code uses asyncio.gather or create_task for parallel execution.",
                    file_path=str(init_file),
                    recommendation="Ensure error handling for parallel tasks is robust."
                ))

        return findings

    async def _check_benchmarking(self) -> List[Finding]:
        """Check for performance benchmarking."""
        findings = []

        benchmark_file = self.component_path / "benchmark.py"
        if benchmark_file.exists():
            findings.append(self._create_finding(
                "info",
                "Performance",
                "Performance benchmarking framework",
                "Dedicated benchmarking module for performance regression detection.",
                file_path=str(benchmark_file),
                recommendation="Run benchmarks regularly and track metrics over time."
            ))

        return findings


class TestingAgent(ReviewAgent):
    """Agent focused on testing quality and coverage."""

    def __init__(self, repo_path: Path):
        super().__init__(AgentRole.TESTING, repo_path)

    async def analyze(self) -> AgentReport:
        """Analyze testing aspects."""
        start_time = asyncio.get_event_loop().time()
        findings = []

        findings.extend(await self._check_test_coverage())
        findings.extend(await self._check_test_organization())
        findings.extend(await self._check_test_types())
        findings.extend(await self._check_fixtures())

        execution_time = asyncio.get_event_loop().time() - start_time

        summary = f"Testing review completed. Found {len(findings)} testing observations."

        return AgentReport(
            agent_role=self.role,
            findings=findings,
            summary=summary,
            metrics={"total_findings": len(findings)},
            execution_time=execution_time
        )

    async def _check_test_coverage(self) -> List[Finding]:
        """Check test coverage configuration."""
        findings = []

        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.coverage" in content or "[tool.pytest" in content:
                findings.append(self._create_finding(
                    "info",
                    "Test Coverage",
                    "Coverage tracking configured",
                    "pytest with coverage tracking is configured.",
                    file_path=str(pyproject),
                    recommendation="Set minimum coverage thresholds and enforce in CI."
                ))

        return findings

    async def _check_test_organization(self) -> List[Finding]:
        """Check test organization."""
        findings = []

        if self.test_path.exists():
            test_files = list(self.test_path.glob("test_*.py"))
            if len(test_files) >= 10:
                findings.append(self._create_finding(
                    "info",
                    "Test Organization",
                    f"Comprehensive test suite with {len(test_files)} test files",
                    "Tests are well-organized with separate files for different components.",
                    file_path=str(self.test_path),
                    recommendation="Maintain test organization as new features are added."
                ))

        return findings

    async def _check_test_types(self) -> List[Finding]:
        """Check for different types of tests."""
        findings = []

        test_types = {
            "test_integration.py": "Integration tests",
            "test_error_scenarios.py": "Error scenario tests",
            "test_performance.py": "Performance tests"
        }

        found_types = []
        for filename, description in test_types.items():
            if (self.test_path / filename).exists():
                found_types.append(description)

        if found_types:
            findings.append(self._create_finding(
                "info",
                "Test Types",
                "Multiple test types present",
                f"Repository includes: {', '.join(found_types)}",
                recommendation="Ensure all test types are run in CI pipeline."
            ))

        return findings

    async def _check_fixtures(self) -> List[Finding]:
        """Check for pytest fixtures."""
        findings = []

        conftest = self.test_path / "conftest.py"
        if conftest.exists():
            findings.append(self._create_finding(
                "info",
                "Test Fixtures",
                "Pytest fixtures configured",
                "conftest.py provides shared fixtures for tests.",
                file_path=str(conftest),
                recommendation="Document complex fixtures and their usage."
            ))

        return findings


class DocumentationAgent(ReviewAgent):
    """Agent focused on documentation quality."""

    def __init__(self, repo_path: Path):
        super().__init__(AgentRole.DOCUMENTATION, repo_path)

    async def analyze(self) -> AgentReport:
        """Analyze documentation."""
        start_time = asyncio.get_event_loop().time()
        findings = []

        findings.extend(await self._check_readme())
        findings.extend(await self._check_technical_docs())
        findings.extend(await self._check_changelog())
        findings.extend(await self._check_api_docs())

        execution_time = asyncio.get_event_loop().time() - start_time

        summary = f"Documentation review completed. Found {len(findings)} documentation observations."

        return AgentReport(
            agent_role=self.role,
            findings=findings,
            summary=summary,
            metrics={"total_findings": len(findings)},
            execution_time=execution_time
        )

    async def _check_readme(self) -> List[Finding]:
        """Check README quality."""
        findings = []

        readme = self.repo_path / "README.md"
        if readme.exists():
            content = readme.read_text()

            # Check for key sections
            required_sections = {
                "installation": ["installation", "install"],
                "usage": ["usage", "getting started"],
                "configuration": ["configuration", "config"],
                "features": ["features", "capabilities"]
            }

            missing_sections = []
            for section, keywords in required_sections.items():
                if not any(keyword in content.lower() for keyword in keywords):
                    missing_sections.append(section)

            if not missing_sections:
                findings.append(self._create_finding(
                    "info",
                    "Documentation",
                    "Comprehensive README",
                    "README includes all key sections: installation, usage, configuration, and features.",
                    file_path=str(readme)
                ))
            else:
                findings.append(self._create_finding(
                    "medium",
                    "Documentation",
                    "README missing sections",
                    f"README should include: {', '.join(missing_sections)}",
                    file_path=str(readme),
                    recommendation=f"Add sections for: {', '.join(missing_sections)}"
                ))
        else:
            findings.append(self._create_finding(
                "high",
                "Documentation",
                "Missing README",
                "No README.md found in repository root.",
                recommendation="Create a comprehensive README with installation, usage, and configuration instructions."
            ))

        return findings

    async def _check_technical_docs(self) -> List[Finding]:
        """Check for technical documentation."""
        findings = []

        docs_path = self.repo_path / "docs"
        if docs_path.exists():
            doc_files = list(docs_path.glob("*.md"))
            if len(doc_files) >= 3:
                findings.append(self._create_finding(
                    "info",
                    "Documentation",
                    f"Technical documentation present ({len(doc_files)} files)",
                    "Dedicated docs directory with multiple documentation files.",
                    file_path=str(docs_path),
                    recommendation="Keep documentation up to date with code changes."
                ))

        return findings

    async def _check_changelog(self) -> List[Finding]:
        """Check for changelog."""
        findings = []

        changelog = self.repo_path / "CHANGELOG.md"
        if changelog.exists():
            findings.append(self._create_finding(
                "info",
                "Documentation",
                "Changelog maintained",
                "CHANGELOG.md tracks version history and changes.",
                file_path=str(changelog),
                recommendation="Update changelog with each release following Keep a Changelog format."
            ))
        else:
            findings.append(self._create_finding(
                "medium",
                "Documentation",
                "No changelog found",
                "Consider adding CHANGELOG.md to track version history.",
                recommendation="Create CHANGELOG.md following Keep a Changelog format."
            ))

        return findings

    async def _check_api_docs(self) -> List[Finding]:
        """Check for API documentation."""
        findings = []

        # Check if code has docstrings
        sample_files = list(self.component_path.glob("*.py"))[:5]
        docstring_count = 0

        for py_file in sample_files:
            content = py_file.read_text()
            if '"""' in content or "'''" in content:
                docstring_count += 1

        if docstring_count >= 3:
            findings.append(self._create_finding(
                "info",
                "API Documentation",
                "Code includes docstrings",
                f"Sampled {len(sample_files)} files, {docstring_count} have docstrings.",
                recommendation="Ensure all public APIs have comprehensive docstrings."
            ))

        return findings


class DependenciesAgent(ReviewAgent):
    """Agent focused on dependency management."""

    def __init__(self, repo_path: Path):
        super().__init__(AgentRole.DEPENDENCIES, repo_path)

    async def analyze(self) -> AgentReport:
        """Analyze dependencies."""
        start_time = asyncio.get_event_loop().time()
        findings = []

        findings.extend(await self._check_dependency_files())
        findings.extend(await self._check_version_constraints())
        findings.extend(await self._check_dependency_updates())

        execution_time = asyncio.get_event_loop().time() - start_time

        summary = f"Dependencies review completed. Found {len(findings)} dependency observations."

        return AgentReport(
            agent_role=self.role,
            findings=findings,
            summary=summary,
            metrics={"total_findings": len(findings)},
            execution_time=execution_time
        )

    async def _check_dependency_files(self) -> List[Finding]:
        """Check for dependency management files."""
        findings = []

        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            findings.append(self._create_finding(
                "info",
                "Dependencies",
                "Modern Python packaging",
                "Using pyproject.toml for dependency management (PEP 518).",
                file_path=str(pyproject),
                recommendation="Keep dependencies up to date and use version constraints."
            ))

        manifest = self.component_path / "manifest.json"
        if manifest.exists():
            findings.append(self._create_finding(
                "info",
                "Dependencies",
                "Home Assistant manifest",
                "manifest.json declares integration dependencies.",
                file_path=str(manifest),
                recommendation="Ensure manifest.json versions match pyproject.toml."
            ))

        return findings

    async def _check_version_constraints(self) -> List[Finding]:
        """Check version constraint best practices."""
        findings = []

        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()

            # Check for pinned versions (potentially problematic)
            if "==" in content:
                findings.append(self._create_finding(
                    "low",
                    "Dependencies",
                    "Pinned dependency versions detected",
                    "Some dependencies use == (exact pins). Consider >= for libraries.",
                    file_path=str(pyproject),
                    recommendation="Use >= with upper bounds for libraries, == only for applications."
                ))

        return findings

    async def _check_dependency_updates(self) -> List[Finding]:
        """Check for dependency update automation."""
        findings = []

        dependabot = self.repo_path / ".github" / "dependabot.yml"
        if dependabot.exists():
            findings.append(self._create_finding(
                "info",
                "Dependencies",
                "Dependabot configured",
                "Automated dependency updates are enabled via Dependabot.",
                file_path=str(dependabot),
                recommendation="Review and merge Dependabot PRs regularly."
            ))

        return findings


class MultiAgentReviewSystem:
    """Coordinates multiple review agents and aggregates results."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.agents = [
            SecurityAgent(repo_path),
            CodeQualityAgent(repo_path),
            ArchitectureAgent(repo_path),
            PerformanceAgent(repo_path),
            TestingAgent(repo_path),
            DocumentationAgent(repo_path),
            DependenciesAgent(repo_path)
        ]

    async def execute_review(self) -> List[AgentReport]:
        """Execute all agents in parallel."""
        print("🚀 Starting Multi-Agent Code Review System")
        print(f"📁 Repository: {self.repo_path}")
        print(f"🤖 Agents: {len(self.agents)}\n")

        # Execute all agents in parallel
        tasks = [agent.analyze() for agent in self.agents]
        reports = await asyncio.gather(*tasks)

        return reports

    def generate_report(self, reports: List[AgentReport]) -> Dict[str, Any]:
        """Generate comprehensive review report."""
        all_findings = []
        agent_summaries = {}
        total_execution_time = 0.0

        for report in reports:
            all_findings.extend(report.findings)
            agent_summaries[report.agent_role.value] = {
                "summary": report.summary,
                "finding_count": len(report.findings),
                "execution_time": report.execution_time,
                "metrics": report.metrics
            }
            total_execution_time += report.execution_time

        # Categorize findings by severity
        findings_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }

        for finding in all_findings:
            findings_by_severity[finding.severity].append(finding)

        # Generate statistics
        stats = {
            "total_findings": len(all_findings),
            "by_severity": {
                severity: len(findings)
                for severity, findings in findings_by_severity.items()
            },
            "total_execution_time": total_execution_time,
            "agents_executed": len(reports)
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "repository": str(self.repo_path),
            "statistics": stats,
            "agent_summaries": agent_summaries,
            "findings_by_severity": {
                severity: [
                    {
                        "category": f.category,
                        "title": f.title,
                        "description": f.description,
                        "file_path": f.file_path,
                        "line_number": f.line_number,
                        "recommendation": f.recommendation
                    }
                    for f in findings
                ]
                for severity, findings in findings_by_severity.items()
            }
        }

    def print_report(self, report_data: Dict[str, Any]) -> None:
        """Print formatted report to console."""
        print("\n" + "="*80)
        print("📊 MULTI-AGENT CODE REVIEW REPORT")
        print("="*80)
        print(f"\n📅 Timestamp: {report_data['timestamp']}")
        print(f"📁 Repository: {report_data['repository']}")
        print(f"⏱️  Total Execution Time: {report_data['statistics']['total_execution_time']:.2f}s")

        # Statistics
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Findings: {report_data['statistics']['total_findings']}")
        print(f"   By Severity:")
        for severity, count in report_data['statistics']['by_severity'].items():
            emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵",
                "info": "⚪"
            }.get(severity, "⚫")
            print(f"      {emoji} {severity.capitalize()}: {count}")

        # Agent summaries
        print(f"\n🤖 Agent Summaries:")
        for agent_name, summary in report_data['agent_summaries'].items():
            print(f"\n   {agent_name.upper()}")
            print(f"      {summary['summary']}")
            print(f"      Execution Time: {summary['execution_time']:.2f}s")

        # Findings by severity
        print(f"\n🔍 Findings by Severity:\n")

        for severity in ["critical", "high", "medium", "low", "info"]:
            findings = report_data['findings_by_severity'][severity]
            if findings:
                emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🔵",
                    "info": "⚪"
                }.get(severity, "⚫")
                print(f"\n{emoji} {severity.upper()} ({len(findings)} findings)")
                print("-" * 80)

                for i, finding in enumerate(findings, 1):
                    print(f"\n{i}. [{finding['category']}] {finding['title']}")
                    print(f"   Description: {finding['description']}")
                    if finding.get('file_path'):
                        file_display = finding['file_path']
                        if finding.get('line_number'):
                            file_display += f":{finding['line_number']}"
                        print(f"   Location: {file_display}")
                    if finding.get('recommendation'):
                        print(f"   💡 Recommendation: {finding['recommendation']}")

        print("\n" + "="*80)
        print("✅ Review Complete")
        print("="*80 + "\n")

    def save_report(self, report_data: Dict[str, Any], output_file: Path) -> None:
        """Save report to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"💾 Report saved to: {output_file}")


async def main():
    """Main entry point for the multi-agent review system."""
    # Determine repository path
    repo_path = Path.cwd()

    # Check if we're in the right directory
    if not (repo_path / "custom_components" / "luxor_living").exists():
        print("❌ Error: Not in the LUXORliving repository root")
        print(f"   Current directory: {repo_path}")
        sys.exit(1)

    # Create review system
    review_system = MultiAgentReviewSystem(repo_path)

    # Execute review
    reports = await review_system.execute_review()

    # Generate report
    report_data = review_system.generate_report(reports)

    # Print report to console
    review_system.print_report(report_data)

    # Save report to file
    output_file = repo_path / "multi_agent_review_report.json"
    review_system.save_report(report_data, output_file)

    # Also save a markdown version
    markdown_file = repo_path / "REVIEW_REPORT.md"
    generate_markdown_report(report_data, markdown_file)

    return report_data


def generate_markdown_report(report_data: Dict[str, Any], output_file: Path) -> None:
    """Generate a markdown version of the report."""
    md_lines = [
        "# Multi-Agent Code Review Report",
        "",
        f"**Generated:** {report_data['timestamp']}",
        f"**Repository:** {report_data['repository']}",
        "",
        "## Executive Summary",
        "",
        f"- **Total Findings:** {report_data['statistics']['total_findings']}",
        f"- **Execution Time:** {report_data['statistics']['total_execution_time']:.2f}s",
        f"- **Agents Executed:** {report_data['statistics']['agents_executed']}",
        "",
        "### Findings by Severity",
        "",
        "| Severity | Count |",
        "|----------|-------|"
    ]

    for severity, count in report_data['statistics']['by_severity'].items():
        md_lines.append(f"| {severity.capitalize()} | {count} |")

    md_lines.extend([
        "",
        "## Agent Summaries",
        ""
    ])

    for agent_name, summary in report_data['agent_summaries'].items():
        md_lines.extend([
            f"### {agent_name.upper().replace('_', ' ')}",
            "",
            summary['summary'],
            "",
            f"- **Findings:** {summary['finding_count']}",
            f"- **Execution Time:** {summary['execution_time']:.2f}s",
            ""
        ])

    md_lines.extend([
        "## Detailed Findings",
        ""
    ])

    for severity in ["critical", "high", "medium", "low", "info"]:
        findings = report_data['findings_by_severity'][severity]
        if findings:
            md_lines.extend([
                f"### {severity.upper()} Severity",
                ""
            ])

            for finding in findings:
                md_lines.extend([
                    f"#### {finding['title']}",
                    "",
                    f"**Category:** {finding['category']}",
                    "",
                    finding['description'],
                    ""
                ])

                if finding.get('file_path'):
                    location = finding['file_path']
                    if finding.get('line_number'):
                        location += f":{finding['line_number']}"
                    md_lines.extend([
                        f"**Location:** `{location}`",
                        ""
                    ])

                if finding.get('recommendation'):
                    md_lines.extend([
                        f"**Recommendation:** {finding['recommendation']}",
                        ""
                    ])

                md_lines.append("---")
                md_lines.append("")

    with open(output_file, 'w') as f:
        f.write('\n'.join(md_lines))

    print(f"📄 Markdown report saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
