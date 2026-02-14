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
    
    # Gemini / Vertex AI 配置
    gemini_api_key: Optional[str] = None  # 使用服务账号时不需要
    gemini_model: str = "gemini-3-flash-preview"
    gcp_project: str = "egozone"  # GCP 项目 ID
    gcp_location: str = "us-central1"  # Vertex AI 区域 (支持最新Gemini 3.0 Pro模型)
    
    # 数据库
    database_url: str = "sqlite:///./egozone.db"
    
    # Redis (可选)
    redis_url: Optional[str] = None
    
    # Telegram (可选)
    telegram_bot_token: Optional[str] = None
    
    # Google Cloud (语音服务，可选)
    google_cloud_project: Optional[str] = None
    
    # 管理员密码（用于访问问答采集、知识库、设置功能）
    admin_password: str = "Wuya2bu2.egozone"  # 请在生产环境修改
    
    # 公共访问密码（用于访问对话功能，防止恶意攻击）
    access_password: str = "123321abc0"  # 请在生产环境修改
    
    # Google Cloud Storage（持久化存储）
    gcs_bucket: Optional[str] = "egozone-data"
    use_gcs: bool = True  # 生产环境设为 True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
