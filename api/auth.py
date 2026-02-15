"""
管理员认证 API
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

router = APIRouter()

# 信任设备文件路径
TRUSTED_DEVICES_FILE = "data/trusted_devices.json"

# 从数据文件加载信任设备列表
def load_trusted_devices() -> Dict[str, dict]:
    """从文件加载信任设备"""
    if os.path.exists(TRUSTED_DEVICES_FILE):
        try:
            with open(TRUSTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_trusted_devices(trusted_devices: Dict[str, dict]):
    """保存信任设备到文件"""
    # 确保目录存在
    os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)
    with open(TRUSTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

# 加载信任设备
trusted_devices = load_trusted_devices()

# 用于存储已验证的 session token（简单实现，生产环境建议使用 Redis）
valid_tokens = set()


class LoginRequest(BaseModel):
    """登录请求"""
    password: str
    trust_device: bool = False  # 是否信任此设备


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    token: Optional[str] = None
    message: str
    device_trusted: bool = False


class VerifyRequest(BaseModel):
    """验证请求"""
    token: str


class TrustDeviceRequest(BaseModel):
    """信任设备请求"""
    token: str
    device_fingerprint: str
    device_name: str


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest, http_request: Request):
    """
    管理员登录

    验证密码并返回访问令牌
    """
    settings = get_settings()

    # 获取设备指纹
    user_agent = http_request.headers.get('user-agent', '')
    ip_address = http_request.client.host
    device_fingerprint = hashlib.sha256(f"{user_agent}_{ip_address}".encode()).hexdigest()

    # 记录设备信息以便管理
    print(f"[调试] 登录尝试 - 设备指纹: {device_fingerprint}, User-Agent: {user_agent}, IP: {ip_address}")

    # 检查是否为信任设备
    is_trusted_device = device_fingerprint in trusted_devices

    # 验证密码（如果不在调试模式且不是信任设备，则需要密码）
    if request.password == settings.admin_password or is_trusted_device:
        # 生成随机 token
        token = secrets.token_urlsafe(32)
        valid_tokens.add(token)

        response_data = LoginResponse(
            success=True,
            token=token,
            message="登录成功"
        )

        # 如果设备被信任，标记设备已信任
        if is_trusted_device:
            response_data.device_trusted = True

        # 如果请求信任此设备
        if request.trust_device and request.password == settings.admin_password:
            # 添加设备到信任列表
            trusted_devices[device_fingerprint] = {
                "name": f"Trusted Device ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                "added_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "user_agent": user_agent[:200]  # 限制长度
            }
            save_trusted_devices(trusted_devices)
            response_data.device_trusted = True

        return response_data
    else:
        return LoginResponse(
            success=False,
            token=None,
            message="密码错误"
        )


@router.post("/verify")
async def verify_token(request: VerifyRequest):
    """
    验证令牌是否有效
    """
    is_valid = request.token in valid_tokens
    return {"valid": is_valid}


@router.post("/logout")
async def admin_logout(request: VerifyRequest):
    """
    管理员登出
    """
    if request.token in valid_tokens:
        valid_tokens.discard(request.token)
    return {"success": True, "message": "已登出"}


def is_admin_token_valid(token: str) -> bool:
    """检查令牌是否有效"""
    return token in valid_tokens


# 公共访问令牌
access_tokens = set()


class AccessLoginRequest(BaseModel):
    """公共访问登录请求"""
    password: str
    trust_device: bool = False  # 是否信任此设备


@router.post("/access-login")
async def access_login(request: AccessLoginRequest, http_request: Request):
    """
    公共访问验证
    验证密码以获取访问对话功能的权限
    """
    settings = get_settings()

    # 获取设备指纹
    user_agent = http_request.headers.get('user-agent', '')
    ip_address = http_request.client.host
    device_fingerprint = hashlib.sha256(f"{user_agent}_{ip_address}".encode()).hexdigest()

    # 记录设备信息以便管理
    print(f"[调试] 访问登录尝试 - 设备指纹: {device_fingerprint}, User-Agent: {user_agent}, IP: {ip_address}")

    # 检查是否为信任设备
    is_trusted_device = device_fingerprint in trusted_devices

    if request.password == settings.access_password or is_trusted_device:
        token = secrets.token_urlsafe(32)
        access_tokens.add(token)

        # 如果请求信任此设备
        if request.trust_device and request.password == settings.access_password:
            # 添加设备到信任列表
            trusted_devices[device_fingerprint] = {
                "name": f"Trusted Device ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                "added_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "user_agent": user_agent[:200]  # 限制长度
            }
            save_trusted_devices(trusted_devices)

        return {
            "success": True,
            "token": token,
            "message": "验证成功"
        }
    else:
        return {
            "success": False,
            "token": None,
            "message": "密码错误"
        }


@router.post("/verify-access")
async def verify_access_token(request: VerifyRequest):
    """
    验证公共访问令牌是否有效
    """
    is_valid = request.token in access_tokens
    return {"valid": is_valid}


@router.get("/trusted-devices")
async def get_trusted_devices():
    """
    获取信任设备列表
    """
    return {"devices": trusted_devices}


@router.delete("/trusted-devices/{device_fingerprint}")
async def remove_trusted_device(device_fingerprint: str):
    """
    移除信任设备
    """
    if device_fingerprint in trusted_devices:
        del trusted_devices[device_fingerprint]
        save_trusted_devices(trusted_devices)
        return {"success": True, "message": "设备已移除"}
    return {"success": False, "message": "设备未找到"}


@router.post("/trust-device")
async def trust_device(request: TrustDeviceRequest):
    """
    手动添加信任设备
    """
    if is_admin_token_valid(request.token):
        settings = get_settings()
        # 需要一个有效的管理员令牌
        trusted_devices[request.device_fingerprint] = {
            "name": request.device_name,
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": "Manually added"
        }
        save_trusted_devices(trusted_devices)
        return {"success": True, "message": "设备已添加到信任列表"}
    return {"success": False, "message": "无效的令牌"}
