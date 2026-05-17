"""Extended pytest tests for lxp_parser.py — LXPParser, LXPCache, dataclasses."""

import time
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest

from custom_components.luxor_living.lxp_parser import (
    LXPActuator,
    LXPCache,
    LXPDatapoint,
    LXPDevice,
    LXPParser,
    LXPProject,
    LXPSensor,
)

NS = "http://www.theben.de/LUXORplug/2016/12"
NP = f"{{{NS}}}"


# ── Minimal valid LXP XML ─────────────────────────────────────────────────────

MINIMAL_LXP = dedent(f"""\
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="{NS}" name="TestProject">
  <adapter address="192.168.1.50:3671"/>
  <devices>
    <device serialNumber="SN001" name="Wohnzimmer S16"
            appId="APP01" address="1.1.1"
            id="dev_001" affected="1">
      <actuator name="Wohnzimmer S16 Licht" channel="1" id="act_001"
                onIcon="Ceiling_ON" offIcon="Ceiling_OFF" useCase="1"
                affected="1">
        <datapoint address="2048" role="OnOff" id="dp1"/>
      </actuator>
      <actuator name="Dimmer" channel="2" id="act_002"
                onIcon="" offIcon="" useCase="0"
                affected="1">
        <datapoint address="2049" role="Dimmen%" id="dp2"/>
        <parameter name="teilnahmePanik" value="true"/>
      </actuator>
      <actuator name="Jalousie" channel="3" id="act_003"
                onIcon="" offIcon="" useCase="0"
                affected="0">
        <datapoint address="2560" role="UpDown" id="dp3"/>
      </actuator>
      <sensor name="Bewegungsmelder" channel="1" id="sen_001"
              sensorType="1" affected="1">
        <datapoint address="4096" role="OnOff" id="dp4"/>
        <parameter name="sensorTyp" value="1"/>
      </sensor>
      <sensor name="Status" channel="2" id="sen_002"
              sensorType="0" affected="0">
        <datapoint address="4097" role="status@OnOff" id="dp5"/>
      </sensor>
    </device>
    <device serialNumber="SN002" name="Wetterstation EG"
            appId="APP02" address="1.1.2"
            id="dev_002" affected="1">
      <sensor name="Außentemperatur" channel="1" id="sen_010"
              sensorType="0" affected="1">
        <datapoint address="8192" role="Temperatur" id="dp10"/>
      </sensor>
    </device>
  </devices>
</project>
""")

MINIMAL_LXP_NO_ADAPTER = dedent(f"""\
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="{NS}" name="NoAdapter">
  <devices>
    <device serialNumber="SN001" name="Dev" appId="A" address="1.1.1"
            id="dev_1" affected="1">
    </device>
  </devices>
</project>
""")

MINIMAL_LXP_ADAPTER_NO_PORT = dedent(f"""\
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="{NS}" name="NoPort">
  <adapter address="10.0.0.1"/>
  <devices/>
</project>
""")


@pytest.fixture
def lxp_file(tmp_path) -> Path:
    """Write MINIMAL_LXP to a temp file and return its path."""
    p = tmp_path / "test.lxp"
    p.write_text(MINIMAL_LXP, encoding="utf-8")
    return p


@pytest.fixture
def lxp_no_adapter(tmp_path) -> Path:
    p = tmp_path / "no_adapter.lxp"
    p.write_text(MINIMAL_LXP_NO_ADAPTER, encoding="utf-8")
    return p


@pytest.fixture
def lxp_no_port(tmp_path) -> Path:
    p = tmp_path / "no_port.lxp"
    p.write_text(MINIMAL_LXP_ADAPTER_NO_PORT, encoding="utf-8")
    return p


# ── LXPParser basic parsing ───────────────────────────────────────────────────


class TestLXPParserBasic:
    @pytest.mark.asyncio
    async def test_parses_project_name(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        assert project.name == "TestProject"

    @pytest.mark.asyncio
    async def test_parses_gateway_address_and_port(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        assert project.gateway_address == "192.168.1.50"
        assert project.gateway_port == 3671

    @pytest.mark.asyncio
    async def test_default_gateway_when_no_adapter(self, lxp_no_adapter):
        parser = LXPParser(lxp_no_adapter)
        project = await parser.parse()
        assert project.gateway_address == "192.168.1.3"
        assert project.gateway_port == 3671

    @pytest.mark.asyncio
    async def test_adapter_without_port(self, lxp_no_port):
        parser = LXPParser(lxp_no_port)
        project = await parser.parse()
        assert project.gateway_address == "10.0.0.1"
        assert project.gateway_port == 3671

    @pytest.mark.asyncio
    async def test_parses_two_devices(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        assert len(project.devices) == 2

    @pytest.mark.asyncio
    async def test_device_attributes(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        dev = project.devices[0]
        assert dev.name == "Wohnzimmer S16"
        assert dev.serial_number == "SN001"
        assert dev.address == "1.1.1"

    @pytest.mark.asyncio
    async def test_actuators_parsed(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        dev = project.devices[0]
        # Only affected=1 actuators by default
        assert len(dev.actuators) == 2  # Jalousie has affected=0

    @pytest.mark.asyncio
    async def test_sensors_parsed(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        dev = project.devices[0]
        # Only affected=1 sensors by default
        assert len(dev.sensors) == 1

    @pytest.mark.asyncio
    async def test_include_unaffected(self, lxp_file):
        parser = LXPParser(lxp_file, include_unaffected=True)
        project = await parser.parse()
        dev = project.devices[0]
        assert len(dev.actuators) == 3
        assert len(dev.sensors) == 2

    @pytest.mark.asyncio
    async def test_actuator_datapoints(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        actuator = project.devices[0].actuators[0]
        assert len(actuator.datapoints) == 1
        dp = actuator.datapoints[0]
        assert dp.role == "OnOff"
        assert dp.address == 2048

    @pytest.mark.asyncio
    async def test_actuator_parameters(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        actuator = project.devices[0].actuators[1]  # Dimmer has parameters
        assert "teilnahmePanik" in actuator.parameters

    @pytest.mark.asyncio
    async def test_sensor_datapoints(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        sensor = project.devices[0].sensors[0]
        assert sensor.sensor_type == 1
        assert any(dp.role == "OnOff" for dp in sensor.datapoints)

    @pytest.mark.asyncio
    async def test_returns_project_instance(self, lxp_file):
        parser = LXPParser(lxp_file)
        project = await parser.parse()
        assert isinstance(project, LXPProject)

    @pytest.mark.asyncio
    async def test_parse_cached_uses_global_cache(self, lxp_file):
        LXPParser.clear_cache()
        project = await LXPParser.parse_cached(lxp_file)
        assert isinstance(project, LXPProject)

    @pytest.mark.asyncio
    async def test_get_cache_stats_returns_dict(self, lxp_file):
        LXPParser.clear_cache()
        await LXPParser.parse_cached(lxp_file)
        stats = LXPParser.get_cache_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert stats["misses"] >= 1

    def test_is_weather_station_device_german(self):
        assert LXPParser._is_weather_station_device("Wetterstation EG") is True

    def test_is_weather_station_device_english(self):
        assert LXPParser._is_weather_station_device("Weather Station Roof") is True

    def test_is_weather_station_device_false(self):
        assert LXPParser._is_weather_station_device("Wohnzimmer S16") is False


# ── LXPCache ──────────────────────────────────────────────────────────────────


class TestLXPCache:
    @pytest.mark.asyncio
    async def test_cache_miss_then_hit(self, lxp_file):
        cache = LXPCache()
        await cache.get_or_parse(lxp_file)
        await cache.get_or_parse(lxp_file)
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_cache_invalidated_on_file_change(self, lxp_file, tmp_path):
        cache = LXPCache()
        await cache.get_or_parse(lxp_file)
        # Simulate file change by writing new content with different hash
        lxp_file.write_text(MINIMAL_LXP.replace("TestProject", "ModifiedProject"), encoding="utf-8")
        # Change mtime explicitly
        import os

        os.utime(lxp_file, (time.time() + 1, time.time() + 1))
        p2 = await cache.get_or_parse(lxp_file)
        assert p2.name == "ModifiedProject"

    @pytest.mark.asyncio
    async def test_clear_resets_stats(self, lxp_file):
        cache = LXPCache()
        await cache.get_or_parse(lxp_file)
        cache.clear()
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0

    @pytest.mark.asyncio
    async def test_evicts_oldest_when_full(self, tmp_path):
        cache = LXPCache(max_size=2)
        files = []
        for i in range(3):
            p = tmp_path / f"proj_{i}.lxp"
            p.write_text(MINIMAL_LXP.replace("TestProject", f"Project{i}"), encoding="utf-8")
            files.append(p)
            await cache.get_or_parse(p)
            time.sleep(0.01)  # ensure different timestamps
        assert cache.get_stats()["size"] == 2

    def test_get_stats_zero_accesses(self):
        cache = LXPCache()
        stats = cache.get_stats()
        assert stats["hit_rate_percent"] == 0
        assert stats["total_accesses"] == 0

    def test_get_stats_with_hits(self):
        cache = LXPCache()
        cache._hits = 3
        cache._misses = 1
        stats = cache.get_stats()
        assert stats["hit_rate_percent"] == 75.0

    @pytest.mark.asyncio
    async def test_expired_entry_is_re_parsed(self, lxp_file):
        cache = LXPCache(ttl_seconds=0)  # Expires immediately
        await cache.get_or_parse(lxp_file)
        # Second call should be a miss (expired)
        await cache.get_or_parse(lxp_file)
        assert cache.get_stats()["misses"] == 2

    def test_cache_key_is_deterministic(self, lxp_file):
        cache = LXPCache()
        key1 = cache._get_cache_key(lxp_file, True)
        key2 = cache._get_cache_key(lxp_file, True)
        assert key1 == key2

    def test_cache_key_differs_for_include_unaffected(self, lxp_file):
        cache = LXPCache()
        key1 = cache._get_cache_key(lxp_file, True)
        key2 = cache._get_cache_key(lxp_file, False)
        assert key1 != key2

    def test_evict_oldest_on_empty_cache(self):
        cache = LXPCache()
        cache._evict_oldest()  # Must not raise

    def test_calculate_file_hash_sync(self, lxp_file):
        cache = LXPCache()
        h = cache._calculate_file_hash_sync(lxp_file)
        assert len(h) == 64  # SHA256 hex


# ── Dataclass instantiation ───────────────────────────────────────────────────


class TestDataclasses:
    def test_lxp_datapoint(self):
        dp = LXPDatapoint(address=1024, role="OnOff", id="dp1")
        assert dp.address == 1024

    def test_lxp_sensor(self):
        s = LXPSensor(
            name="Sensor", channel=1, id="s1", sensor_type=0, datapoints=[], parameters={}
        )
        assert s.name == "Sensor"

    def test_lxp_actuator(self):
        a = LXPActuator(
            name="Actuator",
            channel=1,
            id="a1",
            on_icon="",
            off_icon="",
            use_case=0,
            datapoints=[],
            parameters={},
        )
        assert a.name == "Actuator"

    def test_lxp_device(self):
        d = LXPDevice(
            serial_number="SN",
            name="Dev",
            app_id="APP",
            address="1.1.1",
            id="d1",
            sensors=[],
            actuators=[],
        )
        assert d.serial_number == "SN"

    def test_lxp_device_has_device_type_field(self):
        d = LXPDevice(
            serial_number="SN",
            name="Dev",
            app_id="18502",
            address="1.1.1",
            id="d1",
            sensors=[],
            actuators=[],
        )
        assert hasattr(d, "device_type")

    def test_lxp_project(self):
        p = LXPProject(name="Proj", gateway_address="192.168.1.1", gateway_port=3671, devices=[])
        assert p.gateway_port == 3671


class TestLXPCacheMutationTargets:
    """Smoke tests targeting surviving mutants in LXPCache.__init__ and get_stats."""

    # ── __init__: default values and attribute mutations ──────────────────

    @pytest.mark.smoke
    def test_default_max_size_is_10(self):
        """Kill mutmut_1: default max_size 10 → 11."""
        import inspect

        from custom_components.luxor_living.lxp_parser import LXPCache

        sig = inspect.signature(LXPCache.__init__)
        assert sig.parameters["max_size"].default == 10

    @pytest.mark.smoke
    def test_default_ttl_is_3600(self):
        """Kill mutmut_2: default ttl_seconds 3600 → 3601."""
        import inspect

        from custom_components.luxor_living.lxp_parser import LXPCache

        sig = inspect.signature(LXPCache.__init__)
        assert sig.parameters["ttl_seconds"].default == 3600

    @pytest.mark.smoke
    def test_cache_dict_is_empty_dict_on_init(self):
        """Kill mutmut_3: self._cache = None."""
        from custom_components.luxor_living.lxp_parser import LXPCache

        c = LXPCache()
        assert isinstance(c._cache, dict)
        assert len(c._cache) == 0

    @pytest.mark.smoke
    def test_max_size_stored(self):
        """Kill mutmut_4: self._max_size = None."""
        from custom_components.luxor_living.lxp_parser import LXPCache

        c = LXPCache(max_size=5)
        assert c._max_size == 5

    @pytest.mark.smoke
    def test_ttl_stored(self):
        """Kill mutmut_5: self._ttl_seconds = None."""
        from custom_components.luxor_living.lxp_parser import LXPCache

        c = LXPCache(ttl_seconds=60)
        assert c._ttl_seconds == 60

    @pytest.mark.smoke
    def test_hits_initialised_to_zero(self):
        """Kill mutmut_6: self._hits = None."""
        from custom_components.luxor_living.lxp_parser import LXPCache

        c = LXPCache()
        assert c._hits == 0

    # ── get_stats: arithmetic and dict key mutations ──────────────────────

    @pytest.mark.smoke
    def test_get_stats_total_accesses_is_sum(self):
        """Kill mutmut_1/2: hits + misses → None / hits - misses."""
        from custom_components.luxor_living.lxp_parser import LXPCache

        c = LXPCache()
        c._hits = 3
        c._misses = 7
        stats = c.get_stats()
        # hit_rate with 3 hits out of 10 total = 30%
        assert abs(stats["hit_rate_percent"] - 30.0) < 0.1

    @pytest.mark.smoke
    def test_get_stats_hit_rate_uses_multiplication_not_division(self):
        """Kill mutmut_4/5: * 100 → / 100 or * total."""
        from custom_components.luxor_living.lxp_parser import LXPCache

        c = LXPCache()
        c._hits = 1
        c._misses = 1
        stats = c.get_stats()
        assert abs(stats["hit_rate_percent"] - 50.0) < 0.1  # not 0.5 or 50*2=100

    @pytest.mark.smoke
    def test_get_stats_hit_rate_zero_when_no_accesses(self):
        """Kill mutmut_7: total > 0 → total >= 0 (would divide by zero at 0)."""
        from custom_components.luxor_living.lxp_parser import LXPCache

        c = LXPCache()
        stats = c.get_stats()
        assert stats["hit_rate_percent"] == 0

    @pytest.mark.smoke
    def test_get_stats_returns_expected_keys(self):
        """Kill mutmut_11-15: dict key name mutations (SIZE/MAX_SIZE/HITS/etc.)."""
        from custom_components.luxor_living.lxp_parser import LXPCache

        c = LXPCache()
        stats = c.get_stats()
        for key in ("size", "max_size", "hits", "misses", "hit_rate_percent"):
            assert key in stats, f"missing stats key: {key}"


class TestDeviceTypeParsing:
    """Parser resolves device_type from appId via knxprod_reader."""

    _LXP_WITH_APP_IDS = dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="{NS}" name="AppIdTest">
          <adapter address="192.168.1.50:3671"/>
          <devices>
            <device serialNumber="SN1" name="H6 Dev" appId="18502"
                    address="1.1.1" id="d1" affected="1">
              <actuator name="H6 Ch1" channel="1" id="a1" onIcon="" offIcon=""
                        useCase="0" affected="1">
                <datapoint address="1024" role="Istwert" id="dp1"/>
                <datapoint address="1280" role="Sollwert" id="dp2"/>
                <parameter name="heizungsart" value="230"/>
              </actuator>
            </device>
            <device serialNumber="SN2" name="B6 Dev" appId="18486"
                    address="1.1.2" id="d2" affected="1">
              <sensor name="B6 Ch1" channel="1" id="s1" onIcon="" offIcon=""
                      sensor_type="0" affected="1">
                <datapoint address="2048" role="OnOff" id="dp3"/>
              </sensor>
            </device>
            <device serialNumber="SN3" name="Unknown Dev" appId="9999"
                    address="1.1.3" id="d3" affected="1">
              <sensor name="Unknown Ch1" channel="1" id="s2" onIcon="" offIcon=""
                      sensor_type="0" affected="1">
                <datapoint address="3072" role="OnOff" id="dp4"/>
              </sensor>
            </device>
          </devices>
        </project>
        """)

    def test_known_appid_sets_device_type(self, tmp_path):
        lxp = tmp_path / "test.lxp"
        lxp.write_text(self._LXP_WITH_APP_IDS, encoding="utf-8")
        parser = LXPParser(lxp)
        import asyncio

        project = asyncio.get_event_loop().run_until_complete(parser.parse())
        h6_dev = next(d for d in project.devices if d.name == "H6 Dev")
        assert h6_dev.device_type == "H6"

    def test_b6_appid_sets_device_type(self, tmp_path):
        lxp = tmp_path / "test.lxp"
        lxp.write_text(self._LXP_WITH_APP_IDS, encoding="utf-8")
        parser = LXPParser(lxp)
        import asyncio

        project = asyncio.get_event_loop().run_until_complete(parser.parse())
        b6_dev = next(d for d in project.devices if d.name == "B6 Dev")
        assert b6_dev.device_type == "B6"

    def test_unknown_appid_sets_empty_device_type(self, tmp_path):
        lxp = tmp_path / "test.lxp"
        lxp.write_text(self._LXP_WITH_APP_IDS, encoding="utf-8")
        parser = LXPParser(lxp)
        import asyncio

        project = asyncio.get_event_loop().run_until_complete(parser.parse())
        unknown_dev = next(d for d in project.devices if d.name == "Unknown Dev")
        assert unknown_dev.device_type == ""
