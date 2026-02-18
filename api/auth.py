"""
管理员认证 API - 安全增强版本
支持令牌持久化、过期机制和限流保护
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

# 令牌存储（替代内存存储）
token_storage = get_token_storage()


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
    管理员登录 - 安全增强版本
    支持限流保护和持久化令牌
    """
    settings = get_settings()

    # 获取设备信息和增强指纹
    user_agent = http_request.headers.get('user-agent', '')
    ip_address = http_request.client.host
    accept_language = http_request.headers.get('accept-language')
    accept_encoding = http_request.headers.get('accept-encoding')
    dnt = http_request.headers.get('dnt')
    
    # 生成增强设备指纹
    device_fingerprint = DeviceFingerprint.generate_enhanced_fingerprint(
        user_agent, ip_address, accept_language, accept_encoding, dnt
    )
    
    # 检查可疑设备
    if DeviceFingerprint.is_suspicious_device(user_agent, ip_address):
        print(f"[安全警告] 检测到可疑设备 - IP: {ip_address}, User-Agent: {user_agent}")
        return LoginResponse(
            success=False,
            token=None,
            message="设备验证失败，请使用正常浏览器访问"
        )

    # 检查限流（使用新的限流器）
    from core.rate_limiter import check_login_rate_limit, record_login_attempt
    allowed, message = check_login_rate_limit('admin', ip_address)
    
    if not allowed:
        return LoginResponse(
            success=False,
            token=None,
            message=f"登录被限制: {message}"
        )
    
    # 记录登录尝试（用于设备锁定检查）
    token_storage.record_login_attempt(ip_address, device_fingerprint, 'admin', False, user_agent)

    # 记录设备信息以便管理
    print(f"[安全] 管理员登录尝试 - 设备指纹: {device_fingerprint}, User-Agent: {user_agent}, IP: {ip_address}")

    # 检查是否为信任设备
    is_trusted_device = device_fingerprint in trusted_devices

    # 验证密码（信任设备仍需密码验证，仅提供便利性）
    if request.password == settings.admin_password:
        # 记录成功的登录尝试（在创建令牌之前）
        record_login_attempt('admin', ip_address, success=True,
                           user_agent=user_agent, device_fingerprint=device_fingerprint)
        
        # 创建持久化管理员令牌（7天过期）
        token = token_storage.create_token(
            'admin',
            device_fingerprint,
            user_agent,
            ip_address,
            expires_in_hours=168  # 7天过期
        )

        # 记录成功登录（用于设备管理）
        token_storage.record_login_attempt(ip_address, device_fingerprint, 'admin', True, user_agent)

        response_data = LoginResponse(
            success=True,
            token=token,
            message="登录成功"
        )

        # 信任设备状态仅用于信息显示，不影响认证结果
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


@router.post("/check-device")
async def check_device(http_request: Request):
    """
    检查当前设备是否为可信设备
    如果是可信设备，自动签发访问令牌，实现免密码登录
    """
    # 获取设备信息
    user_agent = http_request.headers.get('user-agent', '')
    ip_address = http_request.client.host
    accept_language = http_request.headers.get('accept-language')
    accept_encoding = http_request.headers.get('accept-encoding')
    dnt = http_request.headers.get('dnt')

    # 生成设备指纹
    device_fingerprint = DeviceFingerprint.generate_enhanced_fingerprint(
        user_agent, ip_address, accept_language, accept_encoding, dnt
    )

    # 检查可疑设备
    if DeviceFingerprint.is_suspicious_device(user_agent, ip_address):
        return {"trusted": False, "message": "设备验证失败"}

    # 检查是否在可信设备列表中
    if device_fingerprint in trusted_devices:
        # 更新最后使用时间
        trusted_devices[device_fingerprint]["last_used"] = datetime.now().isoformat()
        save_trusted_devices(trusted_devices)

        # 自动签发 access 令牌
        token = token_storage.create_token(
            'access',
            device_fingerprint,
            user_agent,
            ip_address,
            expires_in_hours=24
        )

        device_name = trusted_devices[device_fingerprint].get("name", "未知设备")
        print(f"[安全] 可信设备自动登录 - 设备: {device_name}, 指纹: {device_fingerprint[:16]}...")

        return {
            "trusted": True,
            "token": token,
            "device_name": device_name,
            "message": "可信设备自动登录成功"
        }

    return {"trusted": False, "message": "非可信设备"}


@router.post("/verify")
async def verify_token(request: VerifyRequest):
    """
    验证令牌是否有效
    """
    is_valid = token_storage.validate_token(request.token, 'admin')
    return {"valid": is_valid}


@router.post("/logout")
async def admin_logout(request: VerifyRequest):
    """
    管理员登出
    """
    token_storage.revoke_token(request.token)
    return {"success": True, "message": "已登出"}


def is_admin_token_valid(token: str) -> bool:
    """检查管理员令牌是否有效"""
    return token_storage.validate_token(token, 'admin')


# 公共访问令牌管理已移至token_storage


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

    # 获取设备信息和增强指纹
    user_agent = http_request.headers.get('user-agent', '')
    ip_address = http_request.client.host
    accept_language = http_request.headers.get('accept-language')
    accept_encoding = http_request.headers.get('accept-encoding')
    dnt = http_request.headers.get('dnt')
    
    # 生成增强设备指纹
    device_fingerprint = DeviceFingerprint.generate_enhanced_fingerprint(
        user_agent, ip_address, accept_language, accept_encoding, dnt
    )
    
    # 检查可疑设备
    if DeviceFingerprint.is_suspicious_device(user_agent, ip_address):
        print(f"[安全警告] 检测到可疑设备 - IP: {ip_address}, User-Agent: {user_agent}")
        return {
            "success": False,
            "token": None,
            "message": "设备验证失败，请使用正常浏览器访问"
        }

    # 检查限流（使用新的限流器）
    from core.rate_limiter import check_login_rate_limit, record_login_attempt
    allowed, message = check_login_rate_limit('access', ip_address)
    
    if not allowed:
        return {
            "success": False,
            "token": None,
            "message": f"登录被限制: {message}"
        }
    
    # 记录登录尝试（用于设备管理）
    token_storage.record_login_attempt(ip_address, device_fingerprint, 'access', False, user_agent)
    
    print(f"[安全] 访问登录尝试 - 设备指纹: {device_fingerprint}, User-Agent: {user_agent}, IP: {ip_address}")

    # 检查是否为信任设备
    is_trusted_device = device_fingerprint in trusted_devices

    # 信任设备仍需密码验证，仅提供便利性提示
    if request.password == settings.access_password:
        # 记录成功的登录尝试（在创建令牌之前）
        record_login_attempt('access', ip_address, success=True,
                           user_agent=user_agent, device_fingerprint=device_fingerprint)
        
        # 创建持久化令牌
        token = token_storage.create_token(
            'access',
            device_fingerprint,
            user_agent,
            ip_address,
            expires_in_hours=24  # 访问令牌24小时过期
        )

        # 记录成功登录（用于设备管理）
        token_storage.record_login_attempt(ip_address, device_fingerprint, 'access', True, user_agent)

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
    is_valid = is_access_token_valid(request.token)
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
