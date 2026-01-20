#!/usr/bin/env python3
"""Tests for LXP Parser Cache functionality."""

import tempfile
import time
from pathlib import Path

import pytest

from custom_components.luxor_living.lxp_parser import LXPCache, LXPParser


class TestLXPCache:
    """Test the LXP cache functionality."""

    @pytest.fixture
    def sample_lxp_content(self):
        """Sample LXP XML content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<LUXORplug version="1.0" name="Test Project">
    <Gateway address="192.168.1.3" port="3671" />
    <Devices>
        <Device name="Test Device" address="1" serial="12345">
            <Actuators>
                <Actuator name="Test Light" channel="1" affected="1">
                    <Datapoints>
                        <Datapoint address="1" role="OnOff" />
                    </Datapoints>
                </Actuator>
            </Actuators>
        </Device>
    </Devices>
</LUXORplug>"""

    @pytest.fixture
    def temp_lxp_file(self, sample_lxp_content):
        """Create a temporary LXP file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lxp", delete=False) as f:
            f.write(sample_lxp_content)
            f.flush()
            yield Path(f.name)
        Path(f.name).unlink()

    @pytest.mark.asyncio
    async def test_cache_hit(self, temp_lxp_file):
        """Test that cache returns the same project on second access."""
        cache = LXPCache(max_size=10, ttl_seconds=3600)

        # First access - cache miss
        project1 = await cache.get_or_parse(temp_lxp_file, include_unaffected=False)
        stats1 = cache.get_stats()
        assert stats1["misses"] == 1
        assert stats1["hits"] == 0

        # Second access - cache hit
        project2 = await cache.get_or_parse(temp_lxp_file, include_unaffected=False)
        stats2 = cache.get_stats()
        assert stats2["misses"] == 1
        assert stats2["hits"] == 1

        # Projects should be the same object (cached)
        assert project1 is project2
        assert project1.name == project2.name == "Test Project"

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_file_change(self, temp_lxp_file):
        """Test that cache invalidates when file content changes."""
        cache = LXPCache(max_size=10, ttl_seconds=3600)

        # First parse
        project1 = await cache.get_or_parse(temp_lxp_file, include_unaffected=False)
        assert cache.get_stats()["misses"] == 1

        # Modify file
        time.sleep(0.1)  # Ensure mtime changes
        temp_lxp_file.write_text(
            temp_lxp_file.read_text().replace("Test Project", "Modified Project")
        )

        # Second parse should be cache miss due to file change
        project2 = await cache.get_or_parse(temp_lxp_file, include_unaffected=False)
        stats = cache.get_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0
        assert project1.name == "Test Project"
        assert project2.name == "Modified Project"

    @pytest.mark.asyncio
    async def test_cache_different_options(self, temp_lxp_file):
        """Test that different parsing options create separate cache entries."""
        cache = LXPCache(max_size=10, ttl_seconds=3600)

        # Parse with include_unaffected=False
        project1 = await cache.get_or_parse(temp_lxp_file, include_unaffected=False)
        assert cache.get_stats()["misses"] == 1

        # Parse with include_unaffected=True (should be cache miss)
        project2 = await cache.get_or_parse(temp_lxp_file, include_unaffected=True)
        stats = cache.get_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0

        # Projects should be different objects
        assert project1 is not project2

    @pytest.mark.asyncio
    async def test_cache_eviction(self):
        """Test that cache evicts oldest entries when max size is reached."""
        cache = LXPCache(max_size=2, ttl_seconds=3600)

        # Create two temporary files
        with (
            tempfile.NamedTemporaryFile(mode="w", suffix=".lxp", delete=False) as f1,
            tempfile.NamedTemporaryFile(mode="w", suffix=".lxp", delete=False) as f2,
            tempfile.NamedTemporaryFile(mode="w", suffix=".lxp", delete=False) as f3,
        ):

            # Write different content to each file
            f1.write(
                '<LUXORplug version="1.0" name="Project1"><Gateway address="192.168.1.3" port="3671"/><Devices></Devices></LUXORplug>'
            )
            f1.flush()
            f2.write(
                '<LUXORplug version="1.0" name="Project2"><Gateway address="192.168.1.3" port="3671"/><Devices></Devices></LUXORplug>'
            )
            f2.flush()
            f3.write(
                '<LUXORplug version="1.0" name="Project3"><Gateway address="192.168.1.3" port="3671"/><Devices></Devices></LUXORplug>'
            )
            f3.flush()

            file1, file2, file3 = Path(f1.name), Path(f2.name), Path(f3.name)

            # Parse first two files
            await cache.get_or_parse(file1)
            await cache.get_or_parse(file2)
            assert cache.get_stats()["size"] == 2

            # Parse third file - should evict oldest (file1)
            await cache.get_or_parse(file3)
            assert cache.get_stats()["size"] == 2

            # Access file1 again - should be cache miss (evicted)
            await cache.get_or_parse(file1)
            stats = cache.get_stats()
            assert stats["size"] == 2
            assert stats["misses"] == 4  # file1, file2, file3, then file1 again (evicted)

        # Cleanup
        for f in [file1, file2, file3]:
            f.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, temp_lxp_file):
        """Test that cache entries expire after TTL."""
        cache = LXPCache(max_size=10, ttl_seconds=0.1)  # Very short TTL

        # First access
        project1 = await cache.get_or_parse(temp_lxp_file)
        assert cache.get_stats()["misses"] == 1

        # Wait for TTL to expire
        time.sleep(0.2)

        # Second access should be cache miss due to expiration
        project2 = await cache.get_or_parse(temp_lxp_file)
        stats = cache.get_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = LXPCache(max_size=5, ttl_seconds=3600)

        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["max_size"] == 5
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate_percent"] == 0.0
        assert stats["total_accesses"] == 0

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = LXPCache(max_size=10, ttl_seconds=3600)
        # Manually add a fake entry for testing
        cache._cache["test"] = "fake_entry"
        cache._hits = 5
        cache._misses = 3

        cache.clear()

        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0

    @pytest.mark.asyncio
    async def test_parse_cached_method(self, temp_lxp_file):
        """Test the LXPParser.parse_cached class method."""
        # Clear any existing cache
        LXPParser.clear_cache()

        # First call should cache
        project1 = await LXPParser.parse_cached(str(temp_lxp_file))
        stats1 = LXPParser.get_cache_stats()
        assert stats1["misses"] == 1

        # Second call should hit cache
        project2 = await LXPParser.parse_cached(str(temp_lxp_file))
        stats2 = LXPParser.get_cache_stats()
        assert stats2["hits"] == 1
        assert stats2["misses"] == 1

        # Projects should be identical
        assert project1.name == project2.name
