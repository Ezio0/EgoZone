"""
EgoZone 认证中间件
用于保护API端点，集成新的持久化令牌存储系统
"""

from fastapi import HTTPException, Request
from fastapi.security.http import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import json
import os
from pathlib import Path

# 使用新的令牌存储系统
from core.token_storage import get_token_storage


class TokenData(BaseModel):
    """令牌数据模型"""
    token: str
    token_type: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


# 安全HTTP Bearer认证
security = HTTPBearer()


def load_access_tokens():
    """从文件加载访问令牌（向后兼容）"""
    token_file = Path("./data/access_tokens.json")
    
    if token_file.exists():
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                old_tokens = json.load(f)
            
            # 迁移旧令牌到新的存储系统
            token_storage = get_token_storage()
            migrated_count = 0
            
            for token, token_info in old_tokens.items():
                try:
                    from datetime import datetime, timedelta
                    created_at = datetime.fromisoformat(token_info.get('created_at', datetime.now().isoformat()))
                    token_type = token_info.get('type', 'access')
                    
                    # 只迁移未过期的令牌（24小时内）
                    if datetime.now() - created_at < timedelta(hours=24):
                        token_storage._add_token_to_memory(token, token_type, created_at)
                        migrated_count += 1
                except Exception as e:
                    print(f"迁移令牌失败: {e}")
            
            print(f"已迁移 {migrated_count} 个旧令牌到新的存储系统")
            
            # 备份旧文件
            backup_file = token_file.with_suffix('.json.backup')
            token_file.rename(backup_file)
            print(f"旧令牌文件已备份到: {backup_file}")
            
        except Exception as e:
            print(f"加载访问令牌失败: {e}")


def is_access_token_valid(token: str) -> bool:
    """检查访问令牌是否有效"""
    if not token:
        return False
    
    try:
        token_storage = get_token_storage()
        return token_storage.validate_token(token, 'access')
    except Exception as e:
        print(f"访问令牌验证失败: {e}")
        return False


def is_admin_token_valid(token: str) -> bool:
    """检查管理员令牌是否有效"""
    if not token:
        return False
    
    try:
        token_storage = get_token_storage()
        return token_storage.validate_token(token, 'admin')
    except Exception as e:
        print(f"管理员令牌验证失败: {e}")
        return False


def require_access_token(token: str) -> bool:
    """检查是否需要访问令牌 (根据配置决定)"""
    from config import get_settings
    settings = get_settings()

    # 如果设置了访问密码，则需要验证
    return bool(settings.access_password)


def verify_access_token(token: str) -> bool:
    """验证访问令牌"""
    if not token:
        return False

    # 检查是否为有效的访问令牌或管理员令牌
    return is_access_token_valid(token) or is_admin_token_valid(token)


def verify_admin_token(token: str) -> bool:
    """验证管理员令牌"""
    if not token:
        return False

    return is_admin_token_valid(token)


def extract_token_from_request(request: Request) -> Optional[str]:
    """从请求中提取令牌"""
    # 1. 尝试从 Authorization header 获取
    auth_header = request.headers.get("Authorization")
    if auth_header:
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # 移除 "Bearer "
        elif auth_header.startswith("Token "):
            return auth_header[6:]  # 移除 "Token "
        else:
            return auth_header
    
    # 2. 尝试从 X-Access-Token header 获取（向后兼容）
    access_token = request.headers.get("X-Access-Token")
    if access_token:
        return access_token
    
    # 3. 尝试从 X-Admin-Token header 获取（向后兼容）
    admin_token = request.headers.get("X-Admin-Token")
    if admin_token:
        return admin_token
    
    return None


def validate_request_token(request: Request, require_admin: bool = False) -> bool:
    """验证请求中的令牌"""
    token = extract_token_from_request(request)
    
    if not token:
        return False
    
    if require_admin:
        return verify_admin_token(token)
    else:
        return verify_access_token(token)


def get_token_info(token: str) -> Optional[TokenData]:
    """获取令牌信息"""
    if not token:
        return None
    
    try:
        token_storage = get_token_storage()
        token_data = token_storage.get_token_info(token)
        
        if token_data:
            return TokenData(
                token=token,
                token_type=token_data.get('type', 'unknown'),
                user_agent=token_data.get('user_agent'),
                ip_address=token_data.get('ip_address'),
                created_at=token_data.get('created_at'),
                expires_at=token_data.get('expires_at')
            )
    except Exception as e:
        print(f"获取令牌信息失败: {e}")
    
    return None


def cleanup_expired_tokens() -> int:
    """清理过期令牌"""
    try:
        token_storage = get_token_storage()
        return token_storage.cleanup_expired_tokens()
    except Exception as e:
        print(f"清理过期令牌失败: {e}")
        return 0


# 初始化时加载旧令牌（如果存在）
load_access_tokens()