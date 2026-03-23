#!/usr/bin/env python3
"""
EgoZone Security Configuration Initialization Script
For generating strong passwords and configuring security settings
"""

import secrets
import string
import os
from pathlib import Path


def generate_strong_password(length=16):
    """Generate strong password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        # Ensure password contains all character types
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*()_+-=" for c in password)
        ):
            return password


def generate_secret_key(length=32):
    """Generate secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def initialize_security_config():
    """Initialize security configuration"""
    print("🔐 EgoZone Security Configuration Initialization")
    print("=" * 40)

    # Check if .env file exists
    env_path = Path(".env")
    example_path = Path(".env.example")

    if not example_path.exists():
        print("❌ .env.example file not found")
        return False

    if env_path.exists():
        print("⚠️  Detected existing .env file")
        response = input("Overwrite existing configuration? (y/N): ")
        if response.lower() != "y":
            print("Operation cancelled")
            return False

    # Generate strong passwords
    admin_password = generate_strong_password()
    access_password = generate_strong_password()
    secret_key = generate_secret_key()

    print(f"\n✅ Generated security configuration:")
    print(f"   Admin password: {admin_password}")
    print(f"   Access password: {access_password}")
    print(f"   Application secret key: {secret_key}")

    # Read .env.example and replace passwords
    with open(example_path, "r") as f:
        env_content = f.read()

    # Replace password values
    env_content = env_content.replace(
        "Set-a-strong-admin-password-here", admin_password
    )
    env_content = env_content.replace(
        "Set-a-strong-access-password-here", access_password
    )
    env_content = env_content.replace(
        "Set-a-strong-secret-key-here-recommend-using-randomly-generated-long-string",
        secret_key,
    )

    # If still has example values, generate project ID
    if "your-gcp-project-id" in env_content:
        # Generate a sample project ID
        project_suffix = "".join(
            secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8)
        )
        env_content = env_content.replace(
            "your-gcp-project-id", f"egozone-{project_suffix}"
        )

    # Save to .env
    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"\n✅ Security configuration saved to {env_path}")
    print("\n📋 Important reminders:")
    print("   1. Please keep these passwords safe")
    print("   2. Do not commit .env file to version control")
    print("   3. To modify configuration, edit .env file directly")
    print("   4. Restart the service for changes to take effect")

    return True


if __name__ == "__main__":
    initialize_security_config()
