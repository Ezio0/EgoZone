"""
EgoZone 配置管理
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "EgoZone"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    
    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"  # 可切换为 gemini-pro
    
    # 数据库
    database_url: str = "sqlite:///./egozone.db"
    
    # Redis (可选)
    redis_url: Optional[str] = None
    
    # Telegram (可选)
    telegram_bot_token: Optional[str] = None
    
    # Google Cloud (语音服务，可选)
    google_cloud_project: Optional[str] = None
    
    # 管理员密码（用于访问问答采集、知识库、设置功能）
    admin_password: str = "admin123"  # 请在生产环境修改
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
