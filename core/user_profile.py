"""
User Profile Management
Store and manage user personality traits, knowledge background, and speaking style
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import json
import os
from pathlib import Path


class UserProfile(BaseModel):
    """User profile data model"""

    # Basic information
    name: str = "Me"
    avatar: Optional[str] = None

    # Education and professional background
    education: str = ""  # Education background
    profession: str = ""  # Profession
    company: Optional[str] = None  # Company (optional)
    work_experience_years: Optional[int] = None  # Years of work experience

    # Professional areas
    expertise_areas: List[str] = Field(default_factory=list)  # Areas of expertise
    technical_skills: List[str] = Field(default_factory=list)  # Technical skills
    industry_knowledge: List[str] = Field(default_factory=list)  # Industry knowledge

    # Personality traits
    personality_traits: List[str] = Field(
        default_factory=list
    )  # Personality characteristics
    values: List[str] = Field(default_factory=list)  # Values
    interests: List[str] = Field(default_factory=list)  # Interests and hobbies

    # Communication style
    communication_style: str = (
        "friendly, professional"  # Communication style description
    )
    tone_of_voice: str = "gentle"  # Tone style
    formality_level: str = "semi-formal"  # Formality level: formal, semi-formal, casual

    # Language habits
    common_expressions: List[str] = Field(
        default_factory=list
    )  # Common expressions/catchphrases
    emoji_usage: str = "moderate"  # Emoji usage habit: none, light, moderate, heavy
    preferred_language: str = "zh-CN"  # Preferred language

    # Opinions and experiences (collected through Q&A)
    collected_insights: List[Dict] = Field(default_factory=list)  # Collected opinions

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_insight(self, question: str, answer: str, category: str = "general"):
        """Add collected opinion"""
        self.collected_insights.append(
            {
                "question": question,
                "answer": answer,
                "category": category,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.updated_at = datetime.now()

    def get_summary(self) -> str:
        """Generate user profile summary"""
        summary_parts = []

        if self.name:
            summary_parts.append(f"I am {self.name}")
        if self.education:
            summary_parts.append(f"education background is {self.education}")
        if self.profession:
            summary_parts.append(f"profession is {self.profession}")
        if self.expertise_areas:
            summary_parts.append(f"expertise in {', '.join(self.expertise_areas)}")
        if self.personality_traits:
            summary_parts.append(
                f"personality traits include {', '.join(self.personality_traits)}"
            )
        if self.communication_style:
            summary_parts.append(f"communication style is {self.communication_style}")

        return ". ".join(summary_parts) + "." if summary_parts else ""


class UserProfileManager:
    """User profile manager"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.profile_path = self.data_dir / "user_profile.json"
        self.gcs_path = "data/user_profile.json"  # Path in GCS
        self.profile: Optional[UserProfile] = None
        self._gcs_storage = None

    @property
    def gcs_storage(self):
        """Lazy load GCS storage"""
        if self._gcs_storage is None:
            from core.storage import get_gcs_storage

            self._gcs_storage = get_gcs_storage()
        return self._gcs_storage

    async def initialize(self):
        """Initialize, load or create user profile"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load from GCS first
        await self.load()

        if self.profile is None:
            # Create default profile (with user-provided background info)
            self.profile = UserProfile(
                education="Computer Science Bachelor",
                profession="Internet Product Manager",
                expertise_areas=[
                    "Product Design",
                    "User Experience",
                    "Requirements Analysis",
                    "Project Management",
                ],
                technical_skills=[
                    "Product Planning",
                    "Prototyping",
                    "Data Analysis",
                    "Agile Development",
                ],
                industry_knowledge=[
                    "Internet Industry",
                    "Software Development Process",
                    "User Growth",
                ],
                communication_style="Professional and friendly, good at listening and expressing",
                personality_traits=["Logical", "Detail-oriented", "Good communicator"],
            )
            await self.save()

    async def load(self):
        """Load user profile (GCS first, then local)"""
        try:
            # Try loading from GCS first
            if self.gcs_storage.use_gcs:
                data = self.gcs_storage.download_json(self.gcs_path)
                if data:
                    self.profile = UserProfile(**data)
                    # Sync to local
                    with open(self.profile_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                    return

            # Load from local
            if self.profile_path.exists():
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.profile = UserProfile(**data)
        except Exception as e:
            print(f"Failed to load user profile: {e}")
            self.profile = None

    async def save(self):
        """Save user profile (to both local and GCS)"""
        if not self.profile:
            return

        try:
            data = self.profile.model_dump()

            # Save to local
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            # Sync to GCS
            if self.gcs_storage.use_gcs:
                self.gcs_storage.upload_json(data, self.gcs_path)

        except Exception as e:
            print(f"Failed to save user profile: {e}")

    async def update(self, **kwargs):
        """Update user profile"""
        if self.profile:
            for key, value in kwargs.items():
                if hasattr(self.profile, key):
                    setattr(self.profile, key, value)
            self.profile.updated_at = datetime.now()
            await self.save()

    async def add_insight(self, question: str, answer: str, category: str = "general"):
        """Add collected opinion"""
        if self.profile:
            self.profile.add_insight(question, answer, category)
            await self.save()

    def get_profile(self) -> Optional[UserProfile]:
        """Get current user profile"""
        return self.profile

    def build_personality_prompt(self) -> str:
        """Build personalized System Prompt"""
        if not self.profile:
            return ""

        prompt_parts = [
            "You are an AI digital twin, simulating the following person's speaking style and thinking patterns:",
            "",
            f"## Basic Background",
            self.profile.get_summary(),
            "",
            f"## Communication Style",
            f"- Tone style: {self.profile.tone_of_voice}",
            f"- Communication characteristics: {self.profile.communication_style}",
            f"- Formality level: {'formal' if self.profile.formality_level == 'formal' else 'semi-formal' if self.profile.formality_level == 'semi-formal' else 'casual'}",
        ]

        if self.profile.common_expressions:
            prompt_parts.append(
                f"- Common expressions: {', '.join(self.profile.common_expressions)}"
            )

        emoji_desc = {
            "none": "no usage",
            "light": "occasional usage",
            "moderate": "moderate usage",
            "heavy": "frequent usage",
        }
        prompt_parts.append(
            f"- Emoji usage: {emoji_desc.get(self.profile.emoji_usage, 'moderate usage')}"
        )

        if self.profile.personality_traits:
            prompt_parts.extend(
                [
                    "",
                    "## Personality Traits",
                    ", ".join(self.profile.personality_traits),
                ]
            )

        if self.profile.values:
            prompt_parts.extend(["", "## Values", ", ".join(self.profile.values)])

        # Add collected opinions (most recent 10)
        if self.profile.collected_insights:
            recent_insights = self.profile.collected_insights[-10:]
            prompt_parts.extend(["", "## My Opinions and Experiences"])
            for insight in recent_insights:
                prompt_parts.append(f"- Q: {insight['question']}")
                prompt_parts.append(f"  A: {insight['answer']}")

        prompt_parts.extend(
            [
                "",
                "## Important Notes",
                "- Please answer in first person, as if this person is answering directly",
                "- Maintain this person's speaking style and thinking patterns",
                "- If uncertain about something, honestly admit uncertainty",
                "- Keep responses natural and authentic, like chatting with a friend",
            ]
        )

        return "\n".join(prompt_parts)
