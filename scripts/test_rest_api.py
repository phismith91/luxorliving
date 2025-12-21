#!/usr/bin/env python3
"""Test script for REST API client and tunneling activation."""
import asyncio
import sys
from pathlib import Path

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "luxor_living"))

from rest_client import BAOSRestClient, AuthenticationError, TunnelingError


async def test_rest_api(host: str, username: str, password: str):
    """Test REST API authentication and tunneling."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing REST API Client")
    print(f"{'='*60}\n")
    
    print(f"Host: {host}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    async with BAOSRestClient(host, port=80) as client:
        # Step 1: Login
        print("Step 1/3: REST API Login...")
        try:
            token = await client.login(username, password)
            print(f"✅ Login successful!")
            print(f"   Session Token: {token[:20]}...")
            print(f"   Expires: {client.session_expires}")
        except AuthenticationError as err:
            print(f"❌ Login failed: {err}")
            return False
        except Exception as err:
            print(f"❌ Connection error: {err}")
            return False
        
        print()
        
        # Step 2: Enable Tunneling
        print("Step 2/3: Enable KNX Tunneling...")
        try:
            success = await client.enable_tunneling()
            if success:
                print("✅ Tunneling enabled successfully!")
            else:
                print("❌ Failed to enable tunneling")
                return False
        except TunnelingError as err:
            print(f"❌ Tunneling error: {err}")
            return False
        
        print()
        
        # Step 3: Check Status
        print("Step 3/3: Get Tunneling Status...")
        try:
            status = await client.get_tunneling_status()
            print(f"✅ Tunneling Status:")
            print(f"   Enabled: {status.get('enabled', 'unknown')}")
            print(f"   Connected Clients: {status.get('connectedClients', 'unknown')}")
            print(f"   Max Slots: {status.get('maxSlots', 'unknown')}")
        except Exception as err:
            print(f"⚠️  Could not get status: {err}")
        
        print()
        
        # Diagnostics
        print("📊 Diagnostics:")
        diag = client.get_diagnostics()
        for key, value in diag.items():
            print(f"   {key}: {value}")
        
        print()
        print("✅ All tests passed!")
        print()
        print("⚠️  Tunneling will auto-deactivate when script exits (logout)")
        print()
        
        return True


async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test REST API Authentication")
    parser.add_argument("host", help="BAOS 777 IP address (e.g., 192.168.1.3)")
    parser.add_argument("--username", "-u", default="admin", help="Username (default: admin)")
    parser.add_argument("--password", "-p", default="admin", help="Password (default: admin)")
    
    args = parser.parse_args()
    
    try:
        success = await test_rest_api(args.host, args.username, args.password)
        
        if success:
            print("\n✅ REST API client is working correctly!")
            print("\n🎯 Next steps:")
            print("   1. Delete existing LUXORliving integration in HA")
            print("   2. Add integration again (new config flow)")
            print("   3. Upload LXP file")
            print("   4. Enter these credentials")
            print("   5. Check logs for successful setup")
            sys.exit(0)
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    # Run with proper logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
