"""
Enhanced Password Security Validation Module
For stricter security checks
"""

import re
from typing import Dict, List, Tuple
from config import get_settings


def enhanced_security_validation() -> Tuple[bool, List[str], List[str]]:
    """
    Enhanced security validation
    Returns: (passed, error list, warning list)
    """
    settings = get_settings()
    errors = []
    warnings = []

    # Check if required security configurations exist
    if not settings.admin_password or settings.admin_password.strip() == "":
        errors.append("❌ Admin password cannot be empty")

    if not settings.access_password or settings.access_password.strip() == "":
        errors.append("❌ Access password cannot be empty")

    if not settings.secret_key or settings.secret_key == "change-me-in-production":
        errors.append("❌ Must change default SECRET_KEY")

    if (
        not hasattr(settings, "gcp_project")
        or not settings.gcp_project
        or settings.gcp_project == "egozone"
    ):
        errors.append("❌ Must set valid GCP_PROJECT")

    # Stricter password strength check
    if settings.admin_password:
        admin_checks = _detailed_password_check(settings.admin_password, "Admin")
        errors.extend(admin_checks[0])
        warnings.extend(admin_checks[1])

    if settings.access_password:
        access_checks = _detailed_password_check(settings.access_password, "Access")
        errors.extend(access_checks[0])
        warnings.extend(access_checks[1])

    # Additional security checks
    if settings.debug and settings.debug is True:
        warnings.append("⚠️ Debug mode is enabled, should be disabled in production")

    # Check if default passwords are used
    if settings.admin_password in [
        "Wuya2bu2.egozone",
        "admin123",
        "password",
        "123456",
        "admin",
    ]:
        errors.append(
            "❌ Detected use of default admin password, please change immediately"
        )

    if settings.access_password in [
        "123321abc0",
        "access123",
        "password",
        "123456",
        "access",
    ]:
        errors.append(
            "❌ Detected use of default access password, please change immediately"
        )

    return len(errors) == 0, errors, warnings


def _detailed_password_check(
    password: str, password_type: str
) -> Tuple[List[str], List[str]]:
    """
    Detailed password check
    Returns: (error list, warning list)
    """
    errors = []
    warnings = []

    if len(password) < 12:
        errors.append(f"❌ {password_type} password must be at least 12 characters")

    if not re.search(r"[A-Z]", password):
        errors.append(f"❌ {password_type} password must contain uppercase letters")

    if not re.search(r"[a-z]", password):
        errors.append(f"❌ {password_type} password must contain lowercase letters")

    if not re.search(r"\d", password):
        errors.append(f"❌ {password_type} password must contain digits")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>[\]\\`~;\'_+=)(*-]', password):
        errors.append(f"❌ {password_type} password must contain special characters")

    # Check common weak password patterns
    weak_patterns = [
        (
            r"(.)\1{2,}",
            f"{password_type} password should not contain consecutive repeated characters",
        ),
        (
            r"(123|abc|qwe|asd)",
            f"{password_type} password should not contain common character sequences",
        ),
        (
            r"(password|admin|access|changeme|default)",
            f"{password_type} password should not contain common words",
        ),
    ]

    for pattern, msg in weak_patterns:
        if re.search(pattern, password.lower()):
            warnings.append(f"⚠️ {msg}")

    # Check character complexity
    unique_chars = len(set(password))
    if unique_chars < len(password) * 0.6:
        warnings.append(
            f"⚠️ {password_type} password has insufficient character diversity"
        )

    return errors, warnings


def print_security_report(is_secure: bool, errors: List[str], warnings: List[str]):
    """Print security report"""
    print("\n🔒 Security Configuration Check Report")
    print("=" * 40)

    if errors:
        print("\n🚨 Detected the following security issues:")
        for error in errors:
            print(f"   {error}")

    if warnings:
        print("\n⚠️ Detected the following security warnings:")
        for warning in warnings:
            print(f"   {warning}")

    if not errors and not warnings:
        print("\n✅ All security checks passed")
    elif not errors and warnings:
        print(
            f"\n⚠️ Basic security requirements met, but recommend addressing {len(warnings)} security warnings"
        )
    elif errors:
        print(
            f"\n❌ Detected {len(errors)} critical security issues, must fix before starting service"
        )

    print("=" * 40)


if __name__ == "__main__":
    is_secure, errors, warnings = enhanced_security_validation()
    print_security_report(is_secure, errors, warnings)
