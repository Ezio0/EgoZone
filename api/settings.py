"""
Settings API Router
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class SettingsUpdate(BaseModel):
    """Settings update request"""

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
    """User profile response"""

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
    """Get user profile manager"""
    from main import get_profile_manager as _get_profile_manager

    manager = _get_profile_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return manager


@router.get("/profile", response_model=ProfileResponse)
async def get_profile():
    """
    Get user settings
    """
    manager = get_profile_manager()
    profile = manager.get_profile()

    if not profile:
        raise HTTPException(status_code=404, detail="User profile does not exist")

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
        emoji_usage=profile.emoji_usage,
    )


@router.put("/profile")
async def update_profile(settings: SettingsUpdate, http_request: Request):
    """
    Update user settings
    """
    # Verify admin token
    # Get admin token
    admin_token = http_request.headers.get("x-admin-token")
    if not admin_token:
        # Try to get from Authorization header
        auth_header = http_request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            admin_token = auth_header[len("Bearer ") :]

    # Verify admin token
    from api.auth import is_admin_token_valid

    if not is_admin_token_valid(admin_token):
        raise HTTPException(status_code=401, detail="Valid admin token required")

    manager = get_profile_manager()

    # Filter out None values
    update_data = {k: v for k, v in settings.model_dump().items() if v is not None}

    if update_data:
        await manager.update(**update_data)

    return {"success": True, "message": "Settings saved"}
