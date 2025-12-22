"""
设置 API 路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class SettingsUpdate(BaseModel):
    """设置更新请求"""
    name: Optional[str] = None
    education: Optional[str] = None
    profession: Optional[str] = None
    expertise_areas: Optional[List[str]] = None
    technical_skills: Optional[List[str]] = None
    personality_traits: Optional[List[str]] = None
    communication_style: Optional[str] = None
    tone_of_voice: Optional[str] = None
    common_expressions: Optional[List[str]] = None
    emoji_usage: Optional[str] = None


class ProfileResponse(BaseModel):
    """用户画像响应"""
    name: str
    education: str
    profession: str
    expertise_areas: List[str]
    technical_skills: List[str]
    personality_traits: List[str]
    communication_style: str
    tone_of_voice: str
    common_expressions: List[str]
    emoji_usage: str


def get_profile_manager():
    """获取用户画像管理器"""
    from main import get_profile_manager as _get_profile_manager
    manager = _get_profile_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="服务尚未初始化")
    return manager


@router.get("/profile", response_model=ProfileResponse)
async def get_profile():
    """
    获取用户设置
    """
    manager = get_profile_manager()
    profile = manager.get_profile()
    
    if not profile:
        raise HTTPException(status_code=404, detail="用户画像不存在")
    
    return ProfileResponse(
        name=profile.name,
        education=profile.education,
        profession=profile.profession,
        expertise_areas=profile.expertise_areas,
        technical_skills=profile.technical_skills,
        personality_traits=profile.personality_traits,
        communication_style=profile.communication_style,
        tone_of_voice=profile.tone_of_voice,
        common_expressions=profile.common_expressions,
        emoji_usage=profile.emoji_usage
    )


@router.put("/profile")
async def update_profile(settings: SettingsUpdate):
    """
    更新用户设置
    """
    manager = get_profile_manager()
    
    # 过滤掉 None 值
    update_data = {k: v for k, v in settings.model_dump().items() if v is not None}
    
    if update_data:
        await manager.update(**update_data)
    
    return {"success": True, "message": "设置已保存"}
