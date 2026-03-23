"""
Admin Authentication API - Security Enhanced Version
Supports token persistence, expiration mechanism and rate limiting protection
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Set
from config import get_settings
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from core.token_storage import get_token_storage
from core.device_fingerprint import DeviceFingerprint
from core.device_fingerprint import DeviceFingerprint

router = APIRouter()

# Trusted device file path
TRUSTED_DEVICES_FILE = "data/trusted_devices.json"


# Load trusted device list from data file
def load_trusted_devices() -> Dict[str, dict]:
    """Load trusted devices from file"""
    if os.path.exists(TRUSTED_DEVICES_FILE):
        try:
            with open(TRUSTED_DEVICES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_trusted_devices(trusted_devices: Dict[str, dict]):
    """Save trusted devices to file"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)
    with open(TRUSTED_DEVICES_FILE, "w", encoding="utf-8") as f:
        json.dump(trusted_devices, f, ensure_ascii=False, indent=2)


# Load trusted devices
trusted_devices = load_trusted_devices()

# Token storage (replaces in-memory storage)
token_storage = get_token_storage()


class LoginRequest(BaseModel):
    """Login request"""

    password: str
    trust_device: bool = False  # Whether to trust this device


class LoginResponse(BaseModel):
    """Login response"""

    success: bool
    token: Optional[str] = None
    message: str
    device_trusted: bool = False


class VerifyRequest(BaseModel):
    """Verify request"""

    token: str


class TrustDeviceRequest(BaseModel):
    """Trust device request"""

    token: str
    device_fingerprint: str
    device_name: str


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest, http_request: Request):
    """
    Admin login - Security enhanced version
    Supports rate limit protection and persistent tokens
    """
    settings = get_settings()

    # Get device info and enhanced fingerprint
    user_agent = http_request.headers.get("user-agent", "")
    ip_address = http_request.client.host
    accept_language = http_request.headers.get("accept-language")
    accept_encoding = http_request.headers.get("accept-encoding")
    dnt = http_request.headers.get("dnt")

    # Generate enhanced device fingerprint
    device_fingerprint = DeviceFingerprint.generate_enhanced_fingerprint(
        user_agent, ip_address, accept_language, accept_encoding, dnt
    )

    # Check for suspicious device
    if DeviceFingerprint.is_suspicious_device(user_agent, ip_address):
        print(
            f"[Security Warning] Suspicious device detected - IP: {ip_address}, User-Agent: {user_agent}"
        )
        return LoginResponse(
            success=False,
            token=None,
            message="Device verification failed, please use a normal browser to access",
        )

    # Check rate limit (using new rate limiter)
    from core.rate_limiter import check_login_rate_limit, record_login_attempt

    allowed, message = check_login_rate_limit("admin", ip_address)

    if not allowed:
        return LoginResponse(
            success=False, token=None, message=f"Login rate limited: {message}"
        )

    # Record login attempt (for device lock check)
    token_storage.record_login_attempt(
        ip_address, device_fingerprint, "admin", False, user_agent
    )

    # Record device info for management
    print(
        f"[Security] Admin login attempt - Device fingerprint: {device_fingerprint}, User-Agent: {user_agent}, IP: {ip_address}"
    )

    # Check if trusted device
    is_trusted_device = device_fingerprint in trusted_devices

    # Verify password (trusted devices still need password verification, only provides convenience)
    if request.password == settings.admin_password:
        # Record successful login attempt (before creating token)
        record_login_attempt(
            "admin",
            ip_address,
            success=True,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
        )

        # Create persistent admin token (7-day expiration)
        token = token_storage.create_token(
            "admin",
            device_fingerprint,
            user_agent,
            ip_address,
            expires_in_hours=168,  # 7-day expiration
        )

        # Record successful login (for device management)
        token_storage.record_login_attempt(
            ip_address, device_fingerprint, "admin", True, user_agent
        )

        response_data = LoginResponse(
            success=True, token=token, message="Login successful"
        )

        # Trusted device status is only for information display, does not affect authentication result
        if is_trusted_device:
            response_data.device_trusted = True

        # If requesting to trust this device
        if request.trust_device and request.password == settings.admin_password:
            # Add device to trusted list
            trusted_devices[device_fingerprint] = {
                "name": f"Trusted Device ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                "added_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "user_agent": user_agent[:200],  # Limit length
            }
            save_trusted_devices(trusted_devices)
            response_data.device_trusted = True

        return response_data
    else:
        return LoginResponse(success=False, token=None, message="Incorrect password")


@router.post("/check-device")
async def check_device(http_request: Request):
    """
    Check if current device is trusted
    If trusted device, automatically issue access token for passwordless login
    """
    # Get device info
    user_agent = http_request.headers.get("user-agent", "")
    ip_address = http_request.client.host
    accept_language = http_request.headers.get("accept-language")
    accept_encoding = http_request.headers.get("accept-encoding")
    dnt = http_request.headers.get("dnt")

    # Generate device fingerprint
    device_fingerprint = DeviceFingerprint.generate_enhanced_fingerprint(
        user_agent, ip_address, accept_language, accept_encoding, dnt
    )

    # Check for suspicious device
    if DeviceFingerprint.is_suspicious_device(user_agent, ip_address):
        return {"trusted": False, "message": "Device verification failed"}

    # Check if in trusted device list
    if device_fingerprint in trusted_devices:
        # Update last used time
        trusted_devices[device_fingerprint]["last_used"] = datetime.now().isoformat()
        save_trusted_devices(trusted_devices)

        # Automatically issue access token
        token = token_storage.create_token(
            "access", device_fingerprint, user_agent, ip_address, expires_in_hours=24
        )

        device_name = trusted_devices[device_fingerprint].get("name", "Unknown device")
        print(
            f"[Security] Trusted device auto-login - Device: {device_name}, Fingerprint: {device_fingerprint[:16]}..."
        )

        return {
            "trusted": True,
            "token": token,
            "device_name": device_name,
            "message": "Trusted device auto-login successful",
        }

    return {"trusted": False, "message": "Non-trusted device"}


@router.post("/verify")
async def verify_token(request: VerifyRequest):
    """
    Verify if token is valid
    """
    is_valid = token_storage.validate_token(request.token, "admin")
    return {"valid": is_valid}


@router.post("/logout")
async def admin_logout(request: VerifyRequest):
    """
    Admin logout
    """
    token_storage.revoke_token(request.token)
    return {"success": True, "message": "Logged out"}


def is_admin_token_valid(token: str) -> bool:
    """Check if admin token is valid"""
    return token_storage.validate_token(token, "admin")


# Public access token management has been moved to token_storage


class AccessLoginRequest(BaseModel):
    """Public access login request"""

    password: str
    trust_device: bool = False  # Whether to trust this device


@router.post("/access-login")
async def access_login(request: AccessLoginRequest, http_request: Request):
    """
    Public access verification
    Verify password to get access to chat function
    """
    settings = get_settings()

    # Get device info and enhanced fingerprint
    user_agent = http_request.headers.get("user-agent", "")
    ip_address = http_request.client.host
    accept_language = http_request.headers.get("accept-language")
    accept_encoding = http_request.headers.get("accept-encoding")
    dnt = http_request.headers.get("dnt")

    # Generate enhanced device fingerprint
    device_fingerprint = DeviceFingerprint.generate_enhanced_fingerprint(
        user_agent, ip_address, accept_language, accept_encoding, dnt
    )

    # Check for suspicious device
    if DeviceFingerprint.is_suspicious_device(user_agent, ip_address):
        print(
            f"[Security Warning] Suspicious device detected - IP: {ip_address}, User-Agent: {user_agent}"
        )
        return {
            "success": False,
            "token": None,
            "message": "Device verification failed, please use a normal browser to access",
        }

    # Check rate limit (using new rate limiter)
    from core.rate_limiter import check_login_rate_limit, record_login_attempt

    allowed, message = check_login_rate_limit("access", ip_address)

    if not allowed:
        return {
            "success": False,
            "token": None,
            "message": f"Login rate limited: {message}",
        }

    # Record login attempt (for device management)
    token_storage.record_login_attempt(
        ip_address, device_fingerprint, "access", False, user_agent
    )

    print(
        f"[Security] Access login attempt - Device fingerprint: {device_fingerprint}, User-Agent: {user_agent}, IP: {ip_address}"
    )

    # Check if trusted device
    is_trusted_device = device_fingerprint in trusted_devices

    # Trusted devices still need password verification, only provides convenience hint
    if request.password == settings.access_password:
        # Record successful login attempt (before creating token)
        record_login_attempt(
            "access",
            ip_address,
            success=True,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
        )

        # Create persistent token
        token = token_storage.create_token(
            "access",
            device_fingerprint,
            user_agent,
            ip_address,
            expires_in_hours=24,  # Access token expires in 24 hours
        )

        # Record successful login (for device management)
        token_storage.record_login_attempt(
            ip_address, device_fingerprint, "access", True, user_agent
        )

        # If requesting to trust this device
        if request.trust_device and request.password == settings.access_password:
            # Add device to trusted list
            trusted_devices[device_fingerprint] = {
                "name": f"Trusted Device ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                "added_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "user_agent": user_agent[:200],  # Limit length
            }
            save_trusted_devices(trusted_devices)

        return {"success": True, "token": token, "message": "Verification successful"}
    else:
        return {"success": False, "token": None, "message": "Incorrect password"}


@router.post("/verify-access")
async def verify_access_token(request: VerifyRequest):
    """
    Verify if public access token is valid
    """
    is_valid = is_access_token_valid(request.token)
    return {"valid": is_valid}


@router.get("/trusted-devices")
async def get_trusted_devices():
    """
    Get trusted device list
    """
    return {"devices": trusted_devices}


@router.delete("/trusted-devices/{device_fingerprint}")
async def remove_trusted_device(device_fingerprint: str):
    """
    Remove trusted device
    """
    if device_fingerprint in trusted_devices:
        del trusted_devices[device_fingerprint]
        save_trusted_devices(trusted_devices)
        return {"success": True, "message": "Device removed"}
    return {"success": False, "message": "Device not found"}


@router.post("/trust-device")
async def trust_device(request: TrustDeviceRequest):
    """
    Manually add trusted device
    """
    if is_admin_token_valid(request.token):
        settings = get_settings()
        # Requires a valid admin token
        trusted_devices[request.device_fingerprint] = {
            "name": request.device_name,
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": "Manually added",
        }
        save_trusted_devices(trusted_devices)
        return {"success": True, "message": "Device added to trusted list"}
    return {"success": False, "message": "Invalid token"}
