#!/usr/bin/env python3
"""Performance tests for LUXORliving integration."""

# Ensure pytest_homeassistant_custom_component plugin is loaded when running tests directly
pytest_plugins = "pytest_homeassistant_custom_component"

import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# benchmark.py was moved to scripts/ (it is a dev tool, not part of the integration)
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from benchmark import (  # noqa: E402
    LuxorLivingBenchmark,
    benchmark_circuit_breaker,
    benchmark_entity_creation,
    benchmark_lxp_parsing,
    run_full_benchmark,
)


class TestBenchmarkSuite:
    """Test the benchmark suite functionality."""

    def test_benchmark_creation(self):
        """Test benchmark instance creation."""
        benchmark = LuxorLivingBenchmark()
        assert benchmark.results == []

    @pytest.mark.asyncio
    async def test_benchmark_async_operation(self):
        """Test benchmarking an async operation."""
        benchmark = LuxorLivingBenchmark()

        async def test_operation():
            await asyncio.sleep(0.01)  # 10ms operation

        result = await benchmark.benchmark_operation(
            "Test Operation", test_operation, iterations=5, warmup_iterations=1
        )

        assert result.operation == "Test Operation"
        assert result.iterations == 5
        assert result.total_time > 0
        assert result.avg_time > 0.009  # Should be at least 10ms
        assert result.throughput > 0

    def test_benchmark_sync_operation(self):
        """Test benchmarking a sync operation."""
        benchmark = LuxorLivingBenchmark()

        def test_operation():
            import time

            time.sleep(0.01)  # 10ms operation

        result = benchmark.benchmark_sync_operation(
            "Test Sync Operation", test_operation, iterations=3, warmup_iterations=1
        )

        assert result.operation == "Test Sync Operation"
        assert result.iterations == 3
        assert result.total_time > 0
        assert result.avg_time > 0.009  # Should be at least 10ms
        assert result.throughput > 0

    def test_benchmark_summary(self, capsys):
        """Test benchmark summary printing."""
        benchmark = LuxorLivingBenchmark()

        # Add a mock result
        from custom_components.luxor_living.benchmark import BenchmarkResult

        result = BenchmarkResult(
            operation="Test",
            iterations=10,
            total_time=1.0,
            avg_time=0.1,
            min_time=0.09,
            max_time=0.11,
            throughput=10.0,
        )
        benchmark.results.append(result)

        benchmark.print_summary()

        captured = capsys.readouterr()
        assert "PERFORMANCE BENCHMARK RESULTS" in captured.out
        assert "Test" in captured.out

    @pytest.mark.asyncio
    async def test_lxp_parsing_benchmark(self):
        """Test LXP parsing benchmark with mock file."""
        # Create a temporary LXP file
        with tempfile.NamedTemporaryFile(suffix=".lxp", delete=False) as f:
            f.write(b'<?xml version="1.0"?><project></project>')
            temp_file = f.name

        try:
            with patch(
                "custom_components.luxor_living.lxp_parser.LXPParser.parse_cached"
            ) as mock_parse:
                mock_parse.return_value = Mock()  # Mock project

                result = await benchmark_lxp_parsing(temp_file, iterations=2)

                assert "LXP Parsing" in result.operation
                assert result.iterations == 2
                mock_parse.assert_called()

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_entity_creation_benchmark(self):
        """Test entity creation benchmark."""
        result = benchmark_entity_creation(5, iterations=2)

        assert "Entity Creation" in result.operation
        assert "(5 entities)" in result.operation
        assert result.iterations == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_benchmark(self):
        """Test circuit breaker benchmark."""
        result = await benchmark_circuit_breaker(iterations=2)

        assert "Circuit Breaker Operation" in result.operation
        assert result.iterations == 2

    @pytest.mark.asyncio
    async def test_full_benchmark_run(self, capsys):
        """Test running the full benchmark suite."""
        with (
            patch("custom_components.luxor_living.benchmark.benchmark_lxp_parsing") as mock_lxp,
            patch(
                "custom_components.luxor_living.benchmark.benchmark_entity_creation"
            ) as mock_entity,
            patch("custom_components.luxor_living.benchmark.benchmark_circuit_breaker") as mock_cb,
        ):

            # Mock the benchmark functions
            mock_lxp.return_value = None
            mock_entity.return_value = None
            mock_cb.return_value = None

            await run_full_benchmark()

            # Check that all benchmarks were called
            mock_entity.assert_called()  # Should be called 3 times for different entity counts
            mock_cb.assert_called()

            # Check output
            captured = capsys.readouterr()
            assert "Performance Benchmark Suite" in captured.out


class TestPerformanceRegression:
    """Test for performance regression detection."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_performance(self):
        """Test that circuit breaker operations are reasonably fast."""
        result = await benchmark_circuit_breaker(iterations=10)

        # Circuit breaker should be fast (< 10ms per operation)
        assert result.avg_time < 0.01, f"Circuit breaker too slow: {result.avg_time:.4f}s"

        # Should handle reasonable throughput
        assert result.throughput > 50, f"Low throughput: {result.throughput:.2f} ops/sec"

    def test_entity_creation_performance(self):
        """Test that entity creation is reasonably fast."""
        result = benchmark_entity_creation(20, iterations=5)

        # Entity creation should be reasonably fast
        assert result.avg_time < 0.1, f"Entity creation too slow: {result.avg_time:.4f}s"

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test that operations don't have memory leaks (basic check)."""
        import os

        import psutil

        # Get initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Run some operations
        await benchmark_circuit_breaker(iterations=20)

        # Check memory after operations
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 10MB)
        assert (
            memory_increase < 10 * 1024 * 1024
        ), f"Memory leak detected: {memory_increase / 1024 / 1024:.2f}MB increase"


class TestRealLXPBenchmark:
    """Benchmark tests that use real LXP files from the `docs/` folder."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "docs" / "Hauptwohnung.lxp").exists(),
        reason="Hauptwohnung.lxp not found",
    )
    async def test_lxp_parsing_real_file_benchmark(self):
        """Benchmark parsing using the real `Hauptwohnung.lxp` file.

        This test runs a small number of iterations to keep CI fast while
        verifying that parsing performs and the benchmark records results.
        """
        lxp_path = Path(__file__).parent.parent / "docs" / "Hauptwohnung.lxp"

        # Run benchmark with a conservative iteration count to avoid CI slowdowns
        result = await benchmark_lxp_parsing(str(lxp_path), iterations=3)

        assert "LXP Parsing" in result.operation
        assert result.iterations == 3
        assert result.avg_time > 0
        assert result.throughput > 0

        # Ensure result registered in global benchmark instance
        from custom_components.luxor_living.benchmark import get_benchmark

        assert any(r.operation == result.operation for r in get_benchmark().results)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "docs" / "Hauptwohnung.lxp").exists(),
        reason="Hauptwohnung.lxp not found",
    )
    async def test_integration_entity_creation_benchmark(self, mock_config_entry, mock_knx_gateway):
        """Benchmark the time to set up the integration entity mapping using a real LXP file.

        This measures entity mapping time including parsing the LXP file and creating
        the EntityMapper with the real project data.
        """
        import time

        from custom_components.luxor_living.entity_mapper import EntityMapper
        from custom_components.luxor_living.lxp_parser import LXPParser

        # Point to the real LXP file
        lxp_path = Path(__file__).parent.parent / "docs" / "Hauptwohnung.lxp"

        start = time.perf_counter()

        # Parse the LXP file
        project = await LXPParser.parse_cached(str(lxp_path), include_unaffected=False)

        # Create entity mapper
        mapper = EntityMapper(project)
        entity_count = len(mapper.entities)

        end = time.perf_counter()

        setup_time = end - start

        print(
            f"LXP parsing + entity mapping time: {setup_time:.4f}s — Entities mapped: {entity_count}"
        )

        assert setup_time > 0
        assert entity_count > 0  # Should have created some entities from Hauptwohnung.lxp

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "docs" / "Hauptwohnung.lxp").exists(),
        reason="Hauptwohnung.lxp not found",
    )
    async def test_full_entity_creation_benchmark(
        self, mock_config_entry, mock_knx_gateway, mock_coordinator
    ):
        """Benchmark the end-to-end entity creation by calling platform setup.

        This test parses the real LXP file, builds the `EntityMapper` and then
        calls each platform's `async_setup_entry` to simulate entity registration
        while timing the operation.
        """
        import importlib
        import time

        from custom_components.luxor_living.const import DOMAIN
        from custom_components.luxor_living.entity_mapper import EntityMapper
        from custom_components.luxor_living.lxp_parser import LXPParser

        lxp_path = Path(__file__).parent.parent / "docs" / "Hauptwohnung.lxp"

        # Parse real LXP project (blocking on parse_cached)
        project = await LXPParser.parse_cached(str(lxp_path), include_unaffected=False)

        # Create mapper
        mapper = EntityMapper(project)

        # Prepare a fake hass object with required data
        hass = MagicMock()
        hass.data = {
            DOMAIN: {
                mock_config_entry.entry_id: {
                    "mapper": mapper,
                    "knx_gateway": mock_knx_gateway,
                    "config": mock_config_entry.data,
                    "overrides": {},
                    "coordinator": mock_coordinator,
                }
            }
        }

        created_entities = []

        def async_add_entities(entities, update_before_add=False):
            # Entities are objects; store unique ids for counting
            created_entities.extend([getattr(e, "unique_id", str(e)) for e in entities])

        # Convert MappedEntity dataclasses to proxy objects that support both
        # attribute access (used by sensor/light) and dict-like get() (used by cover)
        def to_proxy(me):
            proxy = {}
            proxy["datapoints"] = [{"role": r, "address": a} for r, a in me.datapoints.items()]
            proxy["unique_id"] = me.unique_id
            proxy["name"] = me.name
            proxy["device_id"] = me.device_id
            proxy["device_name"] = me.device_name
            proxy["device_model"] = me.attributes.get("device_model", "")
            proxy["parameters"] = me.parameters
            proxy["entity_type"] = me.entity_type
            proxy["platform"] = me.platform

            # also set attributes for attribute-style access
            class Proxy(dict):
                pass

            p = Proxy(proxy)
            # mirror keys as attributes
            for k, v in proxy.items():
                setattr(p, k, v)

            # ensure .attributes, .datapoints, .parameters exist
            p.attributes = me.attributes
            p.datapoints = me.datapoints
            p.parameters = me.parameters
            p.entity_type = me.entity_type
            p.platform = me.platform
            return p

        mapper.get_entities_by_platform = lambda platform: [
            to_proxy(e) for e in mapper.entities if e.platform == platform
        ]

        platforms = ["sensor", "binary_sensor", "light", "switch", "cover", "climate"]

        start = time.perf_counter()
        for platform in platforms:
            module = importlib.import_module(f"custom_components.luxor_living.{platform}")
            await module.async_setup_entry(hass, mock_config_entry, async_add_entities)
        end = time.perf_counter()

        setup_time = end - start
        entity_count = len(created_entities)

        print(f"Full entity creation time: {setup_time:.4f}s — Entities created: {entity_count}")

        assert setup_time > 0
        assert entity_count > 0
