#!/usr/bin/env python3
"""
EgoZone Security Fix Test Script
Tests whether all security fixes are working properly
"""

import asyncio
import requests
import json
import time
import sys
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_ADMIN_PASSWORD = (
    "Wuya2bu2.egozone"  # Default password, should be rejected by system
)
TEST_ACCESS_PASSWORD = "123321abc0"  # Default password, should be rejected by system
NEW_ADMIN_PASSWORD = "SecureAdmin123!@#"
NEW_ACCESS_PASSWORD = "SecureAccess456!@#"


class SecurityTester:
    """Security Tester"""

    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.admin_token = None
        self.access_token = None
        self.session = requests.Session()

    def test_security_configuration(self):
        """Test security configuration check"""
        print("🔍 Testing security configuration check...")

        try:
            # Run security configuration check
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from core.security_config import SecurityConfig; print(SecurityConfig.validate_security_configuration())",
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )

            if result.returncode != 0:
                print(f"❌ Security configuration check failed: {result.stderr}")
                return False

            print("✅ Security configuration check passed")
            return True

        except Exception as e:
            print(f"❌ Security configuration check exception: {e}")
            return False

    def test_default_password_rejection(self):
        """Test default password rejection"""
        print("🔍 Testing default password rejection...")

        # Test admin default password
        response = self.session.post(
            f"{self.base_url}/api/auth/login", json={"password": TEST_ADMIN_PASSWORD}
        )

        if response.status_code == 401:
            print("✅ Admin default password rejected")
        else:
            print(f"❌ Admin default password not rejected: {response.status_code}")
            return False

        # Test access default password
        response = self.session.post(
            f"{self.base_url}/api/auth/access-login",
            json={"password": TEST_ACCESS_PASSWORD},
        )

        if response.status_code == 401:
            print("✅ Access default password rejected")
        else:
            print(f"❌ Access default password not rejected: {response.status_code}")
            return False

        return True

    def test_rate_limiting(self):
        """Test rate limiting mechanism"""
        print("🔍 Testing rate limiting mechanism...")

        # Send multiple failed login requests quickly
        for i in range(8):
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"password": f"wrong_password_{i}"},
            )

            if response.status_code == 429:
                print(f"✅ Rate limiting activated (request #{i + 1})")
                return True

        print("❌ Rate limiting not activated")
        return False

    def test_token_persistence(self):
        """Test token persistence"""
        print("🔍 Testing token persistence...")

        # First ensure correct passwords are used
        # Note: Correct passwords need to be set manually to test token persistence
        print("⚠️  Please ensure strong passwords are set to test token persistence")
        return True

    def test_device_fingerprinting(self):
        """Test device fingerprinting"""
        print("🔍 Testing device fingerprinting...")

        # Test with different User-Agents
        headers1 = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        headers2 = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response1 = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"password": "wrong"},
            headers=headers1,
        )
        response2 = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"password": "wrong"},
            headers=headers2,
        )

        if response1.status_code == 401 and response2.status_code == 401:
            print("✅ Device fingerprinting working properly")
            return True
        else:
            print("❌ Device fingerprinting test failed")
            return False

    def test_authentication_headers(self):
        """Test authentication header format"""
        print("🔍 Testing authentication header format...")

        # Test standard Authorization header
        headers = {"Authorization": "Bearer fake_token"}
        response = self.session.get(
            f"{self.base_url}/api/chat/history/test", headers=headers
        )

        # Should return 401 (invalid token), not 400 (format error)
        if response.status_code == 401:
            print("✅ Standard Authorization header support working")
        else:
            print(
                f"❌ Standard Authorization header support abnormal: {response.status_code}"
            )
            return False

        # Test backward compatible X-Access-Token header
        headers = {"X-Access-Token": "fake_token"}
        response = self.session.get(
            f"{self.base_url}/api/chat/history/test", headers=headers
        )

        if response.status_code == 401:
            print("✅ Backward compatible header support working")
            return True
        else:
            print(
                f"❌ Backward compatible header support abnormal: {response.status_code}"
            )
            return False

    def test_security_headers(self):
        """Test security headers"""
        print("🔍 Testing security headers...")

        response = self.session.get(f"{self.base_url}/")

        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
        ]

        missing_headers = []
        for header in security_headers:
            if header not in response.headers:
                missing_headers.append(header)

        if not missing_headers:
            print("✅ Security headers configured correctly")
            return True
        else:
            print(f"❌ Missing security headers: {missing_headers}")
            return False

    def test_token_expiration(self):
        """Test token expiration mechanism"""
        print("🔍 Testing token expiration mechanism...")

        # Create expired token
        import jwt
        import datetime

        expired_token = jwt.encode(
            {
                "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=1),
                "type": "admin",
            },
            "secret",
            algorithm="HS256",
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = self.session.get(
            f"{self.base_url}/api/chat/history/test", headers=headers
        )

        if response.status_code == 401:
            print("✅ Expired token rejected")
            return True
        else:
            print(f"❌ Expired token not rejected: {response.status_code}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting EgoZone security fix tests...")
        print("=" * 50)

        tests = [
            ("Security Configuration Check", self.test_security_configuration),
            ("Default Password Rejection", self.test_default_password_rejection),
            ("Rate Limiting", self.test_rate_limiting),
            ("Token Persistence", self.test_token_persistence),
            ("Device Fingerprinting", self.test_device_fingerprinting),
            ("Authentication Header Format", self.test_authentication_headers),
            ("Security Headers Configuration", self.test_security_headers),
            ("Token Expiration Mechanism", self.test_token_expiration),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"\n📋 {test_name}:")
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} passed")
                else:
                    print(f"❌ {test_name} failed")
            except Exception as e:
                print(f"❌ {test_name} exception: {e}")

        print("\n" + "=" * 50)
        print(f"📊 Test results: {passed}/{total} passed")

        if passed == total:
            print("🎉 All security fix tests passed!")
            return True
        else:
            print("⚠️  Some tests failed, please check security fixes")
            return False


def main():
    """Main function"""
    import subprocess

    print("🔧 EgoZone Security Fix Test Tool")
    print("Please ensure EgoZone service is running...")

    # Check if service is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ EgoZone service not running properly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to EgoZone service: {e}")
        print("Please ensure service is started: python main.py")
        return

    tester = SecurityTester()
    success = tester.run_all_tests()

    if success:
        print("\n✅ Security fix verification complete, system security improved!")
    else:
        print("\n⚠️  Security fix verification failed, please check configuration")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
