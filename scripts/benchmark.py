#!/usr/bin/env python3
"""Performance benchmarking for LUXORliving integration operations."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, List

_LOGGER = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a benchmark operation."""

    operation: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    throughput: float  # operations per second


class LuxorLivingBenchmark:
    """Benchmark suite for LUXORliving operations."""

    def __init__(self):
        """Initialize benchmark result storage."""
        self.results: List[BenchmarkResult] = []

    async def benchmark_operation(
        self,
        name: str,
        operation: Callable[[], Awaitable[Any]],
        iterations: int = 100,
        warmup_iterations: int = 10,
    ) -> BenchmarkResult:
        """Benchmark an async operation."""
        _LOGGER.info(f"Starting benchmark: {name} ({iterations} iterations)")

        # Warmup
        for i in range(warmup_iterations):
            await operation()

        # Benchmark
        times: List[float] = []
        for i in range(iterations):
            start_time = time.perf_counter()
            await operation()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        total_time = sum(times)
        avg_time = total_time / iterations
        min_time = min(times)
        max_time = max(times)
        throughput = iterations / total_time

        result = BenchmarkResult(
            operation=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            throughput=throughput,
        )

        self.results.append(result)
        _LOGGER.info(
            f"Benchmark completed: {name} - "
            f"Avg: {avg_time:.4f}s, Min: {min_time:.4f}s, Max: {max_time:.4f}s, "
            f"Throughput: {throughput:.2f} ops/sec"
        )

        return result

    def benchmark_sync_operation(
        self,
        name: str,
        operation: Callable[[], Any],
        iterations: int = 100,
        warmup_iterations: int = 10,
    ) -> BenchmarkResult:
        """Benchmark a synchronous operation."""
        _LOGGER.info(f"Starting sync benchmark: {name} ({iterations} iterations)")

        # Warmup
        for i in range(warmup_iterations):
            operation()

        # Benchmark
        times: List[float] = []
        for i in range(iterations):
            start_time = time.perf_counter()
            operation()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        total_time = sum(times)
        avg_time = total_time / iterations
        min_time = min(times)
        max_time = max(times)
        throughput = iterations / total_time

        result = BenchmarkResult(
            operation=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            throughput=throughput,
        )

        self.results.append(result)
        _LOGGER.info(
            f"Sync benchmark completed: {name} - "
            f"Avg: {avg_time:.4f}s, Min: {min_time:.4f}s, Max: {max_time:.4f}s, "
            f"Throughput: {throughput:.2f} ops/sec"
        )

        return result

    def print_summary(self) -> None:
        """Print benchmark results summary."""
        print("\n" + "=" * 80)
        print("LUXORLIVING PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)
        print(
            f"{'Operation':<25} {'Iter':<8} {'Total':<8} {'Avg':<8} {'Min':<8} {'Max':<8} {'Throughput':<10}"
        )
        print("-" * 80)

        for result in self.results:
            print(
                f"{result.operation:<25} "
                f"{result.iterations:<8} "
                f"{result.total_time:<8.2f} "
                f"{result.avg_time:<8.4f} "
                f"{result.min_time:<8.4f} "
                f"{result.max_time:<8.4f} "
                f"{result.throughput:<8.2f}"
            )

        print("=" * 80)

    def save_results(self, filepath: str) -> None:
        """Save benchmark results to JSON file."""
        import json
        from datetime import datetime

        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "operation": r.operation,
                    "iterations": r.iterations,
                    "total_time": r.total_time,
                    "avg_time": r.avg_time,
                    "min_time": r.min_time,
                    "max_time": r.max_time,
                    "throughput": r.throughput,
                }
                for r in self.results
            ],
        }

        Path(filepath).write_text(json.dumps(data, indent=2))
        _LOGGER.info(f"Benchmark results saved to {filepath}")


# Global benchmark instance
_benchmark = LuxorLivingBenchmark()


def get_benchmark() -> LuxorLivingBenchmark:
    """Get the global benchmark instance."""
    return _benchmark


async def benchmark_lxp_parsing(lxp_file: str, iterations: int = 10) -> BenchmarkResult:
    """Benchmark LXP file parsing."""
    from custom_components.luxor_living.lxp_parser import LXPParser

    async def parse_operation():
        await LXPParser.parse_cached(lxp_file, include_unaffected=False)

    return await _benchmark.benchmark_operation(
        f"LXP Parsing ({Path(lxp_file).name})", parse_operation, iterations=iterations
    )


def benchmark_entity_creation(entity_count: int, iterations: int = 50) -> BenchmarkResult:
    """Benchmark entity creation (simulated)."""

    def create_operation():
        # Simulate entity creation overhead
        entities = []
        for i in range(entity_count):
            # Simulate the overhead of entity initialization
            time.sleep(0.001)  # 1ms per entity creation
            entities.append(f"entity_{i}")
        return entities

    return _benchmark.benchmark_sync_operation(
        f"Entity Creation ({entity_count} entities)", create_operation, iterations=iterations
    )


async def benchmark_circuit_breaker(iterations: int = 100) -> BenchmarkResult:
    """Benchmark circuit breaker operations."""
    from custom_components.luxor_living.circuit_breaker import get_rest_api_circuit_breaker

    cb = get_rest_api_circuit_breaker()

    async def cb_operation():
        # Simulate a circuit breaker protected operation
        await cb.call(lambda: asyncio.sleep(0.001))

    return await _benchmark.benchmark_operation(
        "Circuit Breaker Operation", cb_operation, iterations=iterations
    )


async def run_full_benchmark(lxp_file: str | None = None) -> None:
    """Run a full benchmark suite."""
    print("Starting LUXORliving Performance Benchmark Suite")
    print("=" * 60)

    # Benchmark LXP parsing if file provided
    if lxp_file and Path(lxp_file).exists():
        await benchmark_lxp_parsing(lxp_file)

    # Benchmark entity creation scenarios
    benchmark_entity_creation(10)  # Small setup
    benchmark_entity_creation(50)  # Medium setup
    benchmark_entity_creation(100)  # Large setup

    # Benchmark circuit breaker
    await benchmark_circuit_breaker()

    # Print results
    _benchmark.print_summary()

    # Save results
    results_file = "benchmark_results.json"
    _benchmark.save_results(results_file)
    print(f"\nDetailed results saved to {results_file}")


if __name__ == "__main__":
    # Allow running benchmarks from command line
    import sys

    if len(sys.argv) > 1:
        lxp_file = sys.argv[1]
        asyncio.run(run_full_benchmark(lxp_file))
    else:
        asyncio.run(run_full_benchmark())
