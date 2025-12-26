#!/usr/bin/env python3
"""KNX Bus Monitor for discovering ION Temperature Sensor addresses.

This script monitors all KNX telegrams on the bus and logs temperature-related
messages to help identify ION device temperature object addresses.

Usage:
    python scripts/monitor_knx_telegrams.py --host <IP1_ADDRESS> --port 3671 \
        --username <USER> --password <PASS> --duration 300

The script will:
1. Connect to LUXORliving IP1 gateway via REST + KNX Tunneling
2. Monitor ALL KNX telegrams for specified duration
3. Filter and log temperature telegrams (DPT 9.001)
4. Save results to knx_monitor_results.txt

Focus on ION devices by triggering temperature display or waiting for periodic updates.
"""

import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from xknx import XKNX
from xknx.dpt import DPT2ByteFloat, DPTArray
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import Telegram
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.luxor_living.rest_client import BAOSRestClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("knx_monitor.log"),
        logging.StreamHandler()
    ]
)
_LOGGER = logging.getLogger(__name__)


class KNXMonitor:
    """Monitor KNX bus for telegram analysis."""

    def __init__(self, host: str, port: int, username: str, password: str, http_port: int = 80):
        """Initialize monitor."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.http_port = http_port
        
        self._xknx: XKNX | None = None
        self._rest_client: BAOSRestClient | None = None
        self._telegram_count = 0
        self._temperature_telegrams: list[dict] = []
        self._all_telegrams: list[dict] = []
        
    async def start_monitoring(self, duration: int = 300) -> None:
        """Start monitoring for specified duration (seconds)."""
        try:
            # Step 1: REST API Login
            _LOGGER.info("Step 1/3: REST API Login to %s...", self.host)
            self._rest_client = BAOSRestClient(self.host, port=self.http_port)
            await self._rest_client.__aenter__()
            
            try:
                await self._rest_client.login(self.username, self.password)
                _LOGGER.info("✓ REST API login successful")
            except Exception as err:
                _LOGGER.error("✗ Authentication failed: %s", err)
                return
            
            # Step 2: Enable KNX Tunneling
            _LOGGER.info("Step 2/3: Enabling KNX Tunneling...")
            try:
                await self._rest_client.enable_tunneling()
                _LOGGER.info("✓ KNX Tunneling enabled")
            except Exception as err:
                _LOGGER.error("✗ Failed to enable tunneling: %s", err)
                return
            
            # Step 3: Connect KNX
            _LOGGER.info("Step 3/3: Connecting to KNX bus...")
            connection_config = ConnectionConfig(
                connection_type=ConnectionType.TUNNELING,
                gateway_ip=self.host,
                gateway_port=self.port,
                auto_reconnect=True,
                auto_reconnect_wait=3,
            )
            
            self._xknx = XKNX(connection_config=connection_config)
            await self._xknx.start()
            
            # Register telegram callback
            self._xknx.telegram_queue.register_telegram_received_cb(self._on_telegram)
            
            _LOGGER.info("✓ Connected to KNX bus")
            _LOGGER.info("")
            _LOGGER.info("=" * 80)
            _LOGGER.info("MONITORING KNX BUS FOR %d SECONDS", duration)
            _LOGGER.info("=" * 80)
            _LOGGER.info("Tip: Touch ION devices or wait for periodic temperature updates")
            _LOGGER.info("")
            
            # Monitor for specified duration
            await asyncio.sleep(duration)
            
        finally:
            await self.cleanup()
    
    def _on_telegram(self, telegram: Telegram) -> None:
        """Handle incoming KNX telegram."""
        self._telegram_count += 1
        
        # Extract telegram info
        timestamp = datetime.now().isoformat()
        src = str(telegram.source_address) if telegram.source_address else "unknown"
        dst = str(telegram.destination_address) if telegram.destination_address else "unknown"
        
        # Determine telegram type
        if isinstance(telegram.payload, GroupValueWrite):
            direction = "WRITE"
        elif isinstance(telegram.payload, GroupValueResponse):
            direction = "RESPONSE"
        else:
            direction = str(type(telegram.payload).__name__)
        
        # Get raw value
        value = telegram.payload.value if hasattr(telegram.payload, 'value') else None
        
        # Try to decode as temperature (DPT 9.001)
        temperature = None
        is_temperature = False
        if isinstance(value, DPTArray) and len(value.value) == 2:
            try:
                temperature = DPT2ByteFloat().from_knx(value)
                # Reasonable temperature range check
                if -50 <= temperature <= 100:
                    is_temperature = True
            except Exception:
                pass
        
        # Store telegram data
        telegram_data = {
            "timestamp": timestamp,
            "count": self._telegram_count,
            "source": src,
            "destination": dst,
            "direction": direction,
            "raw_value": str(value),
            "temperature": temperature,
            "is_temperature": is_temperature,
        }
        
        self._all_telegrams.append(telegram_data)
        
        if is_temperature:
            self._temperature_telegrams.append(telegram_data)
            _LOGGER.info(
                "[#%04d] 🌡️  TEMP: %s → %s = %.1f°C (%s)",
                self._telegram_count,
                src,
                dst,
                temperature,
                direction
            )
        else:
            # Log non-temperature telegrams at debug level
            _LOGGER.debug(
                "[#%04d] %s: %s → %s = %s",
                self._telegram_count,
                direction,
                src,
                dst,
                value
            )
    
    async def cleanup(self) -> None:
        """Clean up connections and save results."""
        _LOGGER.info("")
        _LOGGER.info("=" * 80)
        _LOGGER.info("MONITORING COMPLETE")
        _LOGGER.info("=" * 80)
        _LOGGER.info("Total telegrams: %d", self._telegram_count)
        _LOGGER.info("Temperature telegrams: %d", len(self._temperature_telegrams))
        _LOGGER.info("")
        
        # Save results
        self._save_results()
        
        # Cleanup connections
        if self._xknx:
            await self._xknx.stop()
        
        if self._rest_client:
            await self._rest_client.__aexit__(None, None, None)
    
    def _save_results(self) -> None:
        """Save monitoring results to files."""
        output_dir = Path(__file__).parent.parent / "knx_monitor_output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save temperature telegrams
        temp_file = output_dir / f"temperature_telegrams_{timestamp}.txt"
        with open(temp_file, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("ION TEMPERATURE SENSOR DISCOVERY RESULTS\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Monitoring session: {timestamp}\n")
            f.write(f"Total telegrams: {self._telegram_count}\n")
            f.write(f"Temperature telegrams: {len(self._temperature_telegrams)}\n\n")
            
            if self._temperature_telegrams:
                f.write("=" * 80 + "\n")
                f.write("TEMPERATURE TELEGRAMS (DPT 9.001)\n")
                f.write("=" * 80 + "\n\n")
                
                for tg in self._temperature_telegrams:
                    f.write(f"Time:        {tg['timestamp']}\n")
                    f.write(f"Source:      {tg['source']}\n")
                    f.write(f"Destination: {tg['destination']}\n")
                    f.write(f"Temperature: {tg['temperature']:.1f}°C\n")
                    f.write(f"Direction:   {tg['direction']}\n")
                    f.write(f"Raw Value:   {tg['raw_value']}\n")
                    f.write("-" * 80 + "\n\n")
                
                # Group by source address (ION devices)
                f.write("\n" + "=" * 80 + "\n")
                f.write("GROUPED BY SOURCE ADDRESS (ION Devices)\n")
                f.write("=" * 80 + "\n\n")
                
                sources = {}
                for tg in self._temperature_telegrams:
                    src = tg['source']
                    if src not in sources:
                        sources[src] = []
                    sources[src].append(tg)
                
                for src, telegrams in sorted(sources.items()):
                    f.write(f"Source: {src} ({len(telegrams)} telegrams)\n")
                    for tg in telegrams:
                        f.write(f"  → {tg['destination']}: {tg['temperature']:.1f}°C at {tg['timestamp']}\n")
                    f.write("\n")
            else:
                f.write("⚠️  NO TEMPERATURE TELEGRAMS DETECTED\n\n")
                f.write("Possible reasons:\n")
                f.write("- ION devices not sending periodic updates\n")
                f.write("- Monitoring duration too short\n")
                f.write("- Temperature not configured in LUXORplug\n\n")
                f.write("Try:\n")
                f.write("1. Touch ION display to wake it up\n")
                f.write("2. Increase monitoring duration (--duration 600)\n")
                f.write("3. Check LUXORplug ION configuration\n")
        
        _LOGGER.info("Results saved to: %s", temp_file)
        
        # Save all telegrams for reference
        all_file = output_dir / f"all_telegrams_{timestamp}.txt"
        with open(all_file, "w") as f:
            f.write("ALL KNX TELEGRAMS\n")
            f.write("=" * 80 + "\n\n")
            for tg in self._all_telegrams:
                f.write(f"[{tg['count']:04d}] {tg['timestamp']} | {tg['source']} → {tg['destination']} | {tg['direction']} | {tg['raw_value']}\n")
        
        _LOGGER.info("All telegrams saved to: %s", all_file)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor KNX bus to discover ION temperature sensor addresses"
    )
    parser.add_argument("--host", required=True, help="LUXORliving IP1 gateway address")
    parser.add_argument("--port", type=int, default=3671, help="KNX port (default: 3671)")
    parser.add_argument("--username", required=True, help="REST API username")
    parser.add_argument("--password", required=True, help="REST API password")
    parser.add_argument("--http-port", type=int, default=80, help="HTTP port (default: 80)")
    parser.add_argument("--duration", type=int, default=300, help="Monitoring duration in seconds (default: 300)")
    
    args = parser.parse_args()
    
    monitor = KNXMonitor(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        http_port=args.http_port
    )
    
    await monitor.start_monitoring(duration=args.duration)


if __name__ == "__main__":
    asyncio.run(main())
