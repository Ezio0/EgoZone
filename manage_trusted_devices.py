#!/usr/bin/env python3
"""
EgoZone Trusted Device Management Tool
For pre-configuring trusted devices (home computer, work computer, and mobile phone)
"""

import json
import hashlib
import os
from datetime import datetime
from typing import Dict, List

TRUSTED_DEVICES_FILE = "data/trusted_devices.json"


def initialize_trusted_devices():
    """Initialize trusted devices list with pre-configured common trusted devices"""

    # Example device fingerprints and names
    trusted_devices = {
        # Home computer example - actual fingerprint should be generated from real device info when used
        "home_computer_fingerprint_placeholder": {
            "name": "Home Computer",
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": "Placeholder for home computer",
        },
        # Work computer example
        "work_computer_fingerprint_placeholder": {
            "name": "Work Computer",
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": "Placeholder for work computer",
        },
        # Mobile phone example (may have multiple device types)
        "mobile_phone_fingerprint_placeholder": {
            "name": "Personal Mobile Phone",
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": "Placeholder for mobile phone",
        },
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)

    # Save trusted devices list
    with open(TRUSTED_DEVICES_FILE, "w", encoding="utf-8") as f:
        json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

    print(f"✅ Trusted devices list created: {TRUSTED_DEVICES_FILE}")
    print("📝 Note: You need to replace placeholders with actual device fingerprints")
    print(
        "💡 You can auto-generate fingerprints by logging in from a trusted device and checking 'Trust this device'"
    )


def add_trusted_device(device_fingerprint: str, device_name: str):
    """Add a trusted device"""

    # Load existing trusted devices
    if os.path.exists(TRUSTED_DEVICES_FILE):
        with open(TRUSTED_DEVICES_FILE, "r", encoding="utf-8") as f:
            trusted_devices = json.load(f)
    else:
        trusted_devices = {}

    # Add new device
    trusted_devices[device_fingerprint] = {
        "name": device_name,
        "added_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "user_agent": "Added via management script",
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)

    # Save updated trusted devices list
    with open(TRUSTED_DEVICES_FILE, "w", encoding="utf-8") as f:
        json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

    print(f"✅ Device '{device_name}' has been added to the trusted list")


def list_trusted_devices():
    """List all trusted devices"""

    if not os.path.exists(TRUSTED_DEVICES_FILE):
        print("❌ Trusted devices list does not exist")
        return

    with open(TRUSTED_DEVICES_FILE, "r", encoding="utf-8") as f:
        trusted_devices = json.load(f)

    if not trusted_devices:
        print("📭 No trusted devices")
        return

    print(f"📋 Trusted devices list ({len(trusted_devices)} devices):")
    for fingerprint, info in trusted_devices.items():
        print(
            f"  • {info['name']} (fingerprint: {fingerprint[:16]}...) - added: {info['added_at']}"
        )


def remove_trusted_device(device_fingerprint: str):
    """Remove a trusted device"""

    if not os.path.exists(TRUSTED_DEVICES_FILE):
        print("❌ Trusted devices list does not exist")
        return

    with open(TRUSTED_DEVICES_FILE, "r", encoding="utf-8") as f:
        trusted_devices = json.load(f)

    if device_fingerprint in trusted_devices:
        device_name = trusted_devices[device_fingerprint]["name"]
        del trusted_devices[device_fingerprint]

        with open(TRUSTED_DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

        print(f"✅ Device '{device_name}' has been removed from the trusted list")
    else:
        print(
            f"❌ Device with fingerprint {device_fingerprint} is not in the trusted list"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="EgoZone Trusted Device Management Tool"
    )
    parser.add_argument(
        "action",
        choices=["init", "list", "add", "remove"],
        help="Action type: init(initialize), list(list), add(add), remove(remove)",
    )
    parser.add_argument("--fingerprint", type=str, help="Device fingerprint")
    parser.add_argument("--name", type=str, help="Device name")

    args = parser.parse_args()

    if args.action == "init":
        initialize_trusted_devices()
    elif args.action == "list":
        list_trusted_devices()
    elif args.action == "add":
        if not args.fingerprint or not args.name:
            print(
                "❌ Adding a device requires both --fingerprint and --name parameters"
            )
        else:
            add_trusted_device(args.fingerprint, args.name)
    elif args.action == "remove":
        if not args.fingerprint:
            print("❌ Removing a device requires --fingerprint parameter")
        else:
            remove_trusted_device(args.fingerprint)
