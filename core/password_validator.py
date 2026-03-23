"""
Password Validator - Enforces Password Security Policy
"""

import re
import hashlib
import secrets
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel


class PasswordPolicy(BaseModel):
    """Password policy configuration"""

    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special: bool = True
    min_special_chars: int = 2
    forbidden_patterns: List[str] = [
        "123",
        "abc",
        "qwe",
        "password",
        "admin",
        "egozone",
        "test",
        "demo",
        "default",
        "changeme",
        "123456",
    ]
    max_consecutive_chars: int = 3
    min_entropy_bits: float = 30.0


class PasswordValidator:
    """Password strength validator"""

    def __init__(self, policy: PasswordPolicy = None):
        self.policy = policy or PasswordPolicy()

    def validate_password(
        self, password: str, username: str = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate password strength

        Args:
            password: Password to validate
            username: Username (to check if password contains username)

        Returns:
            (is_valid, error message list)
        """
        errors = []

        # Length check
        if len(password) < self.policy.min_length:
            errors.append(
                f"Password must be at least {self.policy.min_length} characters"
            )

        if len(password) > self.policy.max_length:
            errors.append(
                f"Password must not exceed {self.policy.max_length} characters"
            )

        # Character type check
        if self.policy.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain uppercase letters")

        if self.policy.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain lowercase letters")

        if self.policy.require_digits and not re.search(r"\d", password):
            errors.append("Password must contain digits")

        if self.policy.require_special and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            errors.append("Password must contain special characters")

        # Special character count check
        special_count = len(re.findall(r'[!@#$%^&*(),.?":{}|<>]', password))
        if special_count < self.policy.min_special_chars:
            errors.append(
                f"Password must contain at least {self.policy.min_special_chars} special characters"
            )

        # Forbidden pattern check
        password_lower = password.lower()
        for pattern in self.policy.forbidden_patterns:
            if pattern.lower() in password_lower:
                errors.append(f"Password cannot contain common pattern '{pattern}'")

        # Username check
        if username and username.lower() in password_lower:
            errors.append("Password cannot contain username")

        # Consecutive character check
        consecutive_pattern = r"(.)\1{" + str(self.policy.max_consecutive_chars) + ",}"
        if re.search(consecutive_pattern, password):
            errors.append(
                f"Password cannot contain more than {self.policy.max_consecutive_chars + 1} consecutive identical characters"
            )

        # Entropy check (complexity estimation)
        entropy = self._calculate_entropy(password)
        if entropy < self.policy.min_entropy_bits:
            errors.append(
                f"Password complexity insufficient (entropy: {entropy:.1f}, required: {self.policy.min_entropy_bits})"
            )

        return len(errors) == 0, errors

    def _calculate_entropy(self, password: str) -> float:
        """Calculate password entropy"""
        char_counts = {}
        for char in password:
            char_counts[char] = char_counts.get(char, 0) + 1

        entropy = 0.0
        password_length = len(password)
        for count in char_counts.values():
            probability = count / password_length
            if probability > 0:
                entropy -= probability * (probability.bit_length() - 1)

        return entropy * len(set(password))

    def generate_strong_password(self, length: int = 16) -> str:
        """Generate strong password"""
        if length < self.policy.min_length:
            length = self.policy.min_length

        # Character sets
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = '!@#$%^&*(),.?":{}|<>[]'

        # Ensure all required character types are included
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special),
            secrets.choice(special),  # At least 2 special characters
        ]

        # Fill remaining length
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - len(password)):
            password.append(secrets.choice(all_chars))

        # Shuffle order
        secrets.SystemRandom().shuffle(password)

        return "".join(password)

    def hash_password(self, password: str, salt: bytes = None) -> Tuple[str, bytes]:
        """Securely hash password"""
        if salt is None:
            salt = secrets.token_bytes(32)

        # Use PBKDF2 + SHA256
        hashed = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 100000
        )  # 100,000 iterations

        return hashed.hex(), salt

    def verify_password(self, password: str, hashed_password: str, salt: bytes) -> bool:
        """Verify password"""
        calculated_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(calculated_hash, hashed_password)


class DefaultPasswordChecker:
    """Default password checker"""

    # Known default password list
    DEFAULT_PASSWORDS = {
        "admin_password": [
            "Wuya2bu2.egozone",
            "admin",
            "password",
            "123456",
            "admin123",
            "egozone",
            "egozone123",
            "default",
            "changeme",
        ],
        "access_password": [
            "123321abc0",
            "123456",
            "password",
            "access",
            "access123",
            "123321",
            "abc123",
            "default",
            "changeme",
        ],
    }

    @classmethod
    def is_default_password(cls, password: str, password_type: str) -> bool:
        """Check if password is a default password"""
        default_list = cls.DEFAULT_PASSWORDS.get(password_type, [])
        return password in default_list

    @classmethod
    def get_security_recommendations(cls) -> List[str]:
        """Get security recommendations"""
        return [
            "Change default password immediately",
            "Use at least 12 character complex password",
            "Include uppercase and lowercase letters, digits, and special characters",
            "Avoid common words or personal information",
            "Change password regularly",
            "Use different passwords for different accounts",
        ]


def validate_configuration_passwords(admin_pwd: str, access_pwd: str) -> Dict[str, any]:
    """Validate passwords in configuration file"""
    validator = PasswordValidator()
    checker = DefaultPasswordChecker()

    results = {
        "admin_password": {
            "is_valid": False,
            "is_default": False,
            "errors": [],
            "recommendations": [],
        },
        "access_password": {
            "is_valid": False,
            "is_default": False,
            "errors": [],
            "recommendations": [],
        },
    }

    # Check admin password
    is_valid, errors = validator.validate_password(admin_pwd)
    results["admin_password"]["is_valid"] = is_valid
    results["admin_password"]["errors"] = errors
    results["admin_password"]["is_default"] = checker.is_default_password(
        admin_pwd, "admin_password"
    )

    if not is_valid or results["admin_password"]["is_default"]:
        results["admin_password"]["recommendations"] = [
            "Admin password must meet strong password requirements",
            "Cannot use default or common passwords",
            f"Suggested password: {validator.generate_strong_password()}",
        ]

    # Check access password
    is_valid, errors = validator.validate_password(access_pwd)
    results["access_password"]["is_valid"] = is_valid
    results["access_password"]["errors"] = errors
    results["access_password"]["is_default"] = checker.is_default_password(
        access_pwd, "access_password"
    )

    if not is_valid or results["access_password"]["is_default"]:
        results["access_password"]["recommendations"] = [
            "Access password must meet strong password requirements",
            "Cannot use default or common passwords",
            f"Suggested password: {validator.generate_strong_password()}",
        ]

    return results
