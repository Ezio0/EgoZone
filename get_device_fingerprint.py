#!/usr/bin/env python3
"""
Device Fingerprint Generation Tool
Helps you obtain a fingerprint for a specific device to add to the trusted devices list
"""

import hashlib
import sys
import platform


def generate_device_fingerprint(user_agent, ip_address):
    """
    Generate device fingerprint
    This uses the same algorithm as EgoZone internally
    """
    return hashlib.sha256(f"{user_agent}_{ip_address}".encode()).hexdigest()


def main():
    print("=== EgoZone Device Fingerprint Generation Tool ===\n")

    print("To obtain a device fingerprint, you need to provide:")
    print("1. User-Agent string")
    print("2. Device IP address\n")

    print("How to get User-Agent string:")
    print(
        "- Chrome browser: Press F12, Console tab, type navigator.userAgent and press Enter"
    )
    print(
        "- Firefox browser: Press F12, Console tab, type navigator.userAgent and press Enter"
    )
    print(
        "- Safari browser: After enabling Develop menu, press Option+Cmd+C, type navigator.userAgent and press Enter\n"
    )

    # If arguments passed from command line
    if len(sys.argv) >= 3:
        user_agent = sys.argv[1]
        ip_address = sys.argv[2]
        device_fingerprint = generate_device_fingerprint(user_agent, ip_address)

        print(f"User-Agent: {user_agent}")
        print(f"IP Address: {ip_address}")
        print(f"Device fingerprint: {device_fingerprint}")
        print(f"Device fingerprint (truncated): {device_fingerprint[:16]}...")

        # Add to trusted devices list
        import os
        import json
        from datetime import datetime

TRUSTED_DEVICES_FILE = "data/trusted_devices.json"

        # Load existing device list
        if os.path.exists(TRUSTED_DEVICES_FILE):
            with open(TRUSTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
                trusted_devices = json.load(f)
        else:
            trusted_devices = {}

        # Add new device
        device_name = input(f"\nPlease enter a name for this device (e.g., 'Home Computer'): ").strip()
        if not device_name:
            device_name = "Home Computer"

        trusted_devices[device_fingerprint] = {
            "name": device_name,
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": user_agent[:200],
        }

# Save
        os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)
        with open(TRUSTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

        print(f"✅ Device '{device_name}' has been added to the trusted list")
        print(f"   Fingerprint: {device_fingerprint}")
        return

    # If no command line arguments, provide interactive interface
    print("Alternatively, you can manually enter information:")
    user_agent = input("Please enter User-Agent string: ").strip()
    if not user_agent:
        print("No User-Agent entered, exiting.")
        return

    ip_address = input("Please enter IP address (enter 'unknown' if not sure): ").strip()
    if not ip_address:
        ip_address = "unknown"

    device_fingerprint = generate_device_fingerprint(user_agent, ip_address)

    print(f"\nGenerated device fingerprint: {device_fingerprint}")
    print(f"Truncated version for matching: {device_fingerprint[:16]}...")

    # Add to trusted devices list
    import os
    import json
    from datetime import datetime

TRUSTED_DEVICES_FILE = "data/trusted_devices.json"

    # Load existing device list
    if os.path.exists(TRUSTED_DEVICES_FILE):
        with open(TRUSTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
            trusted_devices = json.load(f)
    else:
        trusted_devices = {}

    # Add new device
    device_name = input(f"\nPlease enter a name for this device (e.g., 'Home Computer'): ").strip()
    if not device_name:
        device_name = "Home Computer"

    trusted_devices[device_fingerprint] = {
        "name": device_name,
        "added_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "user_agent": user_agent[:200],
    }

# Save
    os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)
    with open(TRUSTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

    print(f"✅ Device '{device_name}' has been added to the trusted list")
    print(f"   Fingerprint: {device_fingerprint}")


if __name__ == "__main__":
    main()
