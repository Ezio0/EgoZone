"""
管理员认证 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from config import get_settings
import hashlib
import secrets

router = APIRouter()

# ⚠️ 本地调试模式：设为 True 跳过密码验证
DEBUG_MODE = True

# 用于存储已验证的 session token（简单实现，生产环境建议使用 Redis）
valid_tokens = set()


class LoginRequest(BaseModel):
    """登录请求"""
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    token: Optional[str] = None
    message: str


class VerifyRequest(BaseModel):
    """验证请求"""
    token: str


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest):
    """
    管理员登录
    
    验证密码并返回访问令牌
    """
    settings = get_settings()
    
    if DEBUG_MODE or request.password == settings.admin_password:
        # 生成随机 token
        token = secrets.token_urlsafe(32)
        valid_tokens.add(token)
        
        return LoginResponse(
            success=True,
            token=token,
            message="登录成功"
        )
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


@router.post("/access-login")
async def access_login(request: AccessLoginRequest):
    """
    公共访问验证
    验证密码以获取访问对话功能的权限
    """
    settings = get_settings()
    
    if DEBUG_MODE or request.password == settings.access_password:
        token = secrets.token_urlsafe(32)
        access_tokens.add(token)
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
