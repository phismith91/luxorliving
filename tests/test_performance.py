#!/usr/bin/env python3
"""Performance tests for LUXORliving integration."""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from custom_components.luxor_living.benchmark import (
    LuxorLivingBenchmark,
    benchmark_lxp_parsing,
    benchmark_entity_creation,
    benchmark_circuit_breaker,
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
            "Test Operation",
            test_operation,
            iterations=5,
            warmup_iterations=1
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
            "Test Sync Operation",
            test_operation,
            iterations=3,
            warmup_iterations=1
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
            throughput=10.0
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
        with tempfile.NamedTemporaryFile(suffix='.lxp', delete=False) as f:
            f.write(b'<?xml version="1.0"?><project></project>')
            temp_file = f.name

        try:
            with patch('custom_components.luxor_living.lxp_parser.LXPParser.parse_cached') as mock_parse:
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
        with patch('custom_components.luxor_living.benchmark.benchmark_lxp_parsing') as mock_lxp, \
             patch('custom_components.luxor_living.benchmark.benchmark_entity_creation') as mock_entity, \
             patch('custom_components.luxor_living.benchmark.benchmark_circuit_breaker') as mock_cb:

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
        import psutil
        import os

        # Get initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Run some operations
        await benchmark_circuit_breaker(iterations=20)

        # Check memory after operations
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 10MB)
        assert memory_increase < 10 * 1024 * 1024, f"Memory leak detected: {memory_increase / 1024 / 1024:.2f}MB increase"