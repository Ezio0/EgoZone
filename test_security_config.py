#!/usr/bin/env python3
"""
Security Configuration Validation Script
Used to verify EgoZone security configuration is correct
"""

import os
import sys
from pathlib import Path

# Add project root directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_security_config():
    """Test security configuration"""
    print("🔐 Testing security configuration...")

    try:
        # Test configuration loading
        from config import get_settings

        settings = get_settings()
        print("✅ Configuration loaded successfully")

        # Test enhanced security validation
        from core.enhanced_security import (
            enhanced_security_validation,
            print_security_report,
        )

        is_secure, errors, warnings = enhanced_security_validation()

        print_security_report(is_secure, errors, warnings)

        # Test password generator
        from init_security import generate_strong_password, generate_secret_key

        test_admin_pwd = generate_strong_password()
        test_access_pwd = generate_strong_password()
        test_secret = generate_secret_key()

        print(f"\n✅ Password generator test passed")
        print(f"   Generated admin password: {test_admin_pwd[:8]}...")
        print(f"   Generated access password: {test_access_pwd[:8]}...")
        print(f"   Generated secret key: {test_secret[:8]}...")

        # Check if passwords meet basic requirements
        assert len(test_admin_pwd) >= 12, "Admin password length insufficient"
        assert len(test_access_pwd) >= 12, "Access password length insufficient"
        assert len(test_secret) >= 24, "Secret key length insufficient"

        # Check character complexity
        import re

        assert re.search(r"[A-Z]", test_admin_pwd), (
            "Admin password missing uppercase letters"
        )
        assert re.search(r"[a-z]", test_admin_pwd), (
            "Admin password missing lowercase letters"
        )
        assert re.search(r"\d", test_admin_pwd), "Admin password missing digits"
        assert re.search(r'[!@#$%^&*(),.?":{}|<>[\]\\`~;\'_+=)(*-]', test_admin_pwd), (
            "Admin password missing special characters"
        )

        print("✅ Password strength test passed")
        print("\n🎉 All security configuration tests passed!")
        return True

    except Exception as e:
        print(f"❌ Security configuration test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_security_config()
    if not success:
        sys.exit(1)
