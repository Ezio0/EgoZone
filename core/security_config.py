"""
Security Configuration Management
Provides security-related configuration and validation functionality
"""

import re
from typing import Dict, List, Optional
from config import get_settings


class SecurityConfig:
    """Security configuration manager"""

    # Default password blacklist (must be changed)
    DEFAULT_PASSWORDS = {
        "admin": ["Wuya2bu2.egozone", "admin123", "password", "123456"],
        "access": ["123321abc0", "access123", "password", "123456"],
    }

    # Password strength requirements
    PASSWORD_REQUIREMENTS = {
        "min_length": 8,
        "max_length": 64,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": True,
        "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
    }

    # Security headers configuration
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    }

    @staticmethod
    def check_password_strength(password: str) -> Dict[str, any]:
        """Check password strength"""
        errors = []
        warnings = []

        # Length check
        if len(password) < SecurityConfig.PASSWORD_REQUIREMENTS["min_length"]:
            errors.append(
                f"Password must be at least {SecurityConfig.PASSWORD_REQUIREMENTS['min_length']} characters"
            )

        if len(password) > SecurityConfig.PASSWORD_REQUIREMENTS["max_length"]:
            errors.append(
                f"Password must not exceed {SecurityConfig.PASSWORD_REQUIREMENTS['max_length']} characters"
            )

        # Character type check
        if SecurityConfig.PASSWORD_REQUIREMENTS["require_uppercase"] and not re.search(
            r"[A-Z]", password
        ):
            errors.append("Password must contain at least one uppercase letter")

        if SecurityConfig.PASSWORD_REQUIREMENTS["require_lowercase"] and not re.search(
            r"[a-z]", password
        ):
            errors.append("Password must contain at least one lowercase letter")

        if SecurityConfig.PASSWORD_REQUIREMENTS["require_digit"] and not re.search(
            r"\d", password
        ):
            errors.append("Password must contain at least one digit")

        if SecurityConfig.PASSWORD_REQUIREMENTS["require_special"] and not re.search(
            f"[{re.escape(SecurityConfig.PASSWORD_REQUIREMENTS['special_chars'])}]",
            password,
        ):
            errors.append("Password must contain at least one special character")

        # Common weak password check
        weak_patterns = [
            r"123+",  # Consecutive numbers
            r"abc+",  # Consecutive letters
            r"qwe+",  # Keyboard sequence
            r"(.)\1{2,}",  # Repeated characters
        ]

        for pattern in weak_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                warnings.append(
                    "Password contains common patterns, consider increasing complexity"
                )
                break

        # Personal information related check (simple check)
        common_info_patterns = [
            r"admin",
            r"user",
            r"test",
            r"password",
            r"202[0-9]",
            r"19[0-9]{2}",  # Years
        ]

        for pattern in common_info_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                warnings.append("Password should not contain common words or dates")
                break

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": SecurityConfig._calculate_password_score(
                password, errors, warnings
            ),
        }

    @staticmethod
    def _calculate_password_score(
        password: str, errors: List[str], warnings: List[str]
    ) -> int:
        """Calculate password strength score (0-100)"""
        if errors:
            return 0

        score = 50  # Base score

        # Length bonus
        if len(password) >= 12:
            score += 20
        elif len(password) >= 10:
            score += 10

        # Character diversity bonus
        char_types = 0
        if re.search(r"[A-Z]", password):
            char_types += 1
        if re.search(r"[a-z]", password):
            char_types += 1
        if re.search(r"\d", password):
            char_types += 1
        if re.search(r"[^A-Za-z0-9]", password):
            char_types += 1

        score += char_types * 5

        # Complexity bonus
        if len(password) >= 16:
            score += 10

        # Warning penalty
        score -= len(warnings) * 5

        return max(0, min(100, score))

    @staticmethod
    def is_default_password(password_type: str, password: str) -> bool:
        """Check if default password is used"""
        if password_type not in SecurityConfig.DEFAULT_PASSWORDS:
            return False

        return password in SecurityConfig.DEFAULT_PASSWORDS[password_type]

    @staticmethod
    def validate_security_configuration() -> Dict[str, any]:
        """Validate security configuration"""
        settings = get_settings()
        issues = []
        warnings = []

        # Check default passwords
        if SecurityConfig.is_default_password("admin", settings.admin_password):
            issues.append("Admin password is using default password, must change")

        if SecurityConfig.is_default_password("access", settings.access_password):
            issues.append("Access password is using default password, must change")

        # Check password strength
        admin_check = SecurityConfig.check_password_strength(settings.admin_password)
        if not admin_check["is_valid"]:
            issues.extend(
                [f"Admin password: {error}" for error in admin_check["errors"]]
            )
        elif admin_check["score"] < 70:
            warnings.append("Admin password strength is low, consider strengthening")

        access_check = SecurityConfig.check_password_strength(settings.access_password)
        if not access_check["is_valid"]:
            issues.extend(
                [f"Access password: {error}" for error in access_check["errors"]]
            )
        elif access_check["score"] < 50:
            warnings.append("Access password strength is low, consider strengthening")

        # Check debug mode
        import os

        if os.environ.get("DEBUG", "false").lower() == "true":
            warnings.append("Debug mode is enabled, should be disabled in production")

        return {
            "is_secure": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": SecurityConfig._get_security_recommendations(
                issues, warnings
            ),
        }

    @staticmethod
    def _get_security_recommendations(
        issues: List[str], warnings: List[str]
    ) -> List[str]:
        """Get security recommendations"""
        recommendations = []

        if issues:
            recommendations.append(
                "Fix all security issues before deploying to production"
            )

        if warnings:
            recommendations.append(
                "Consider addressing security warnings to improve system security"
            )

        recommendations.extend(
            [
                "Regularly update passwords and monitor abnormal logins",
                "Enable HTTPS encrypted transmission",
                "Regularly backup data and audit logs",
                "Consider implementing multi-factor authentication (MFA)",
            ]
        )

        return recommendations

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security HTTP headers"""
        return SecurityConfig.SECURITY_HEADERS.copy()


def check_security_configuration():
    """Quick security check function"""
    result = SecurityConfig.validate_security_configuration()

    if not result["is_secure"]:
        print("❌ Critical security issues found:")
        for issue in result["issues"]:
            print(f"   - {issue}")
        return False

    if result["warnings"]:
        print("⚠️  Security warnings found:")
        for warning in result["warnings"]:
            print(f"   - {warning}")

    print("✅ Basic security check passed")
    return True


if __name__ == "__main__":
    check_security_configuration()
