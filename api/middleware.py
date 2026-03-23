"""
EgoZone Authentication Middleware
Protects API endpoints and integrates new persistent token storage system
"""

from fastapi import HTTPException, Request
from fastapi.security.http import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import json
import os
from pathlib import Path

# Use new token storage system
from core.token_storage import get_token_storage


class TokenData(BaseModel):
    """Token data model"""

    token: str
    token_type: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


# Secure HTTP Bearer authentication
security = HTTPBearer()


def load_access_tokens():
    """Load access tokens from file (backward compatible)"""
    token_file = Path("./data/access_tokens.json")

    if token_file.exists():
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                old_tokens = json.load(f)

            # Migrate old tokens to new storage system
            token_storage = get_token_storage()
            migrated_count = 0

            for token, token_info in old_tokens.items():
                try:
                    from datetime import datetime, timedelta

                    created_at = datetime.fromisoformat(
                        token_info.get("created_at", datetime.now().isoformat())
                    )
                    token_type = token_info.get("type", "access")

                    # Only migrate non-expired tokens (within 24 hours)
                    if datetime.now() - created_at < timedelta(hours=24):
                        token_storage._add_token_to_memory(
                            token, token_type, created_at
                        )
                        migrated_count += 1
                except Exception as e:
                    print(f"Failed to migrate token: {e}")

            print(f"Migrated {migrated_count} old tokens to new storage system")

            # Backup old file
            backup_file = token_file.with_suffix(".json.backup")
            token_file.rename(backup_file)
            print(f"Old token file backed up to: {backup_file}")

        except Exception as e:
            print(f"Failed to load access tokens: {e}")


def is_access_token_valid(token: str) -> bool:
    """Check if access token is valid"""
    if not token:
        return False

    try:
        token_storage = get_token_storage()
        return token_storage.validate_token(token, "access")
    except Exception as e:
        print(f"Access token validation failed: {e}")
        return False


def is_admin_token_valid(token: str) -> bool:
    """Check if admin token is valid"""
    if not token:
        return False

    try:
        token_storage = get_token_storage()
        return token_storage.validate_token(token, "admin")
    except Exception as e:
        print(f"Admin token validation failed: {e}")
        return False


def require_access_token(token: str) -> bool:
    """Check if access token is required (based on config)"""
    from config import get_settings

    settings = get_settings()

    # If access password is set, verification is required
    return bool(settings.access_password)


def verify_access_token(token: str) -> bool:
    """Verify access token"""
    if not token:
        return False

    # Check if it's a valid access token or admin token
    return is_access_token_valid(token) or is_admin_token_valid(token)


def verify_admin_token(token: str) -> bool:
    """Verify admin token"""
    if not token:
        return False

    return is_admin_token_valid(token)


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract token from request"""
    # 1. Try to get from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header:
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer "
        elif auth_header.startswith("Token "):
            return auth_header[6:]  # Remove "Token "
        else:
            return auth_header

    # 2. Try to get from X-Access-Token header (backward compatible)
    access_token = request.headers.get("X-Access-Token")
    if access_token:
        return access_token

    # 3. Try to get from X-Admin-Token header (backward compatible)
    admin_token = request.headers.get("X-Admin-Token")
    if admin_token:
        return admin_token

    return None


def validate_request_token(request: Request, require_admin: bool = False) -> bool:
    """Verify token in request"""
    token = extract_token_from_request(request)

    if not token:
        return False

    if require_admin:
        return verify_admin_token(token)
    else:
        return verify_access_token(token)


def get_token_info(token: str) -> Optional[TokenData]:
    """Get token info"""
    if not token:
        return None

    try:
        token_storage = get_token_storage()
        token_data = token_storage.get_token_info(token)

        if token_data:
            return TokenData(
                token=token,
                token_type=token_data.get("type", "unknown"),
                user_agent=token_data.get("user_agent"),
                ip_address=token_data.get("ip_address"),
                created_at=token_data.get("created_at"),
                expires_at=token_data.get("expires_at"),
            )
    except Exception as e:
        print(f"Failed to get token info: {e}")

    return None


def cleanup_expired_tokens() -> int:
    """Clean up expired tokens"""
    try:
        token_storage = get_token_storage()
        return token_storage.cleanup_expired_tokens()
    except Exception as e:
        print(f"Failed to clean up expired tokens: {e}")
        return 0


# Load old tokens at initialization (if they exist)
load_access_tokens()
