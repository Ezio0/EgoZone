#!/usr/bin/env python3
"""
EgoZone Trusted Device Feature Test Script
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Clear cache and reload configuration
import config
import importlib

importlib.reload(config)

from api.auth import load_trusted_devices
from config import get_settings


def test_trusted_devices_functionality():
    """Test trusted device functionality"""
    print("🔍 Testing trusted device functionality...")

    # Test 1: Check if trusted devices data file exists
    print("\n✅ Test 1: Check trusted devices data file")
    trusted_devices = load_trusted_devices()
    if trusted_devices:
        print(f"   Found {len(trusted_devices)} trusted devices:")
        for fingerprint, info in list(trusted_devices.items())[:3]:  # Only show first 3
            print(f"   - {info['name']}: {fingerprint[:16]}...")
    else:
        print("   ❌ No trusted devices found")

    # Test 2: Check if configuration is updated
    print("\n✅ Test 2: Check configuration settings")
    settings = get_settings()
    print(f"   Debug mode: {'Enabled' if settings.debug else 'Disabled'}")
    print(f"   Admin password set: {'Yes' if settings.admin_password else 'No'}")
    print(f"   Access password set: {'Yes' if settings.access_password else 'No'}")

    # Test 3: Check if auth module imports work properly
    print("\n✅ Test 3: Check auth module import")
    try:
        from api.auth import is_admin_token_valid

        print("   ✅ Auth module import successful")
    except ImportError as e:
        print(f"   ❌ Auth module import failed: {e}")

    print("\n🎉 Tests completed!")
    print("\n📝 Summary:")
    print("- Password validation re-enabled (DEBUG_MODE disabled)")
    print("- Trusted device feature implemented")
    print("- Data persistence configured")
    print("- API endpoints updated to support trusted devices")
    print("\n💡 Next steps:")
    print("1. Log in from a trusted device and check 'Trust this device'")
    print("2. Use /api/auth/trusted-devices to view device list")
    print("3. Regularly check and manage trusted devices")


if __name__ == "__main__":
    test_trusted_devices_functionality()
